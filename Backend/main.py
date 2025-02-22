from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import asyncio
import logging
from typing import List
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from config.database import Database
from repositories.user_repository import UserRepository
from models.user import UserCreate, UserResponse
from fastapi import Response, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from utils.auth import create_access_token
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import google.generativeai as genai
from googlesearch import search
import time

load_dotenv()
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Global variable for repository
user_repository = None

# Initialize the chatbot as a global variable
chatbot = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    await Database.connect_db()
    
    # Initialize repositories and chatbot
    global user_repository, chatbot
    user_repository = UserRepository()
    genai.configure(api_key="AIzaSyCcZp2pD7_zlhwJl9nHGPBI-8YQOSSCFsA")
    chatbot = AsyncWebCrawler()
    await chatbot.__aenter__()
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await Database.close_db()
    if chatbot:
        await chatbot.__aexit__(None, None, None)

app = FastAPI(lifespan=lifespan)

# Update CORS middleware with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def search_google(query: str, num_results: int = 3) -> List[str]:
    """Search Google and return the top URLs."""
    urls = []
    try:
        search_results = search(query, num_results=num_results)
        urls = list(search_results)
        time.sleep(0.2)  # Add delay between searches
    except Exception as e:
        print(f"Error during Google search: {e}")
    return urls

async def generate_streaming_response(prompt: str):
    """Generate streaming response using web scraping and Gemini."""
    try:
        message_id = str(uuid.uuid4())
        model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05')
        
        # Initial processing message
        processing_message = {
            "id": message_id,
            "role": "assistant",
            "content": ""
        }
        yield f"data: {json.dumps(processing_message)}\n\n"
        
        # Search Google and get URLs
        urls = search_google(prompt)
        context_parts = []
        
        # Scrape each URL
        for url in urls:
            try:
                run_cfg = CrawlerRunConfig(only_text=True)
                result = await chatbot.arun(url=url, config=run_cfg)
                if result and result.markdown_v2:
                    context_parts.append(f"Source ({url}):\n{result.markdown_v2}\n")
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue
        
        # Combine all context
        context = "\n".join(context_parts)
        
        # Generate response
        prompt_template = f"""**System Instructions**:
You are a helpful university chatbot. Use the provided context to answer questions.
If the context doesn't contain relevant information, say I do not have enough information to answer this question
do not provide any citations . Make sure you give enough informations to help the user.
**Context**:
{context}

**Question**:
{prompt}

Please provide a helpful response using the above context and your knowledge. but in resposen do not say that based on the current context the answer is this just answer if you do not know the answer do not say that based on the current context the answer is this just answer if you do not know the answer"""

        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(prompt_template)
        )
        
        if response.text:
            # Stream the response in chunks
            chunk_size = 100
            text = response.text
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
            
            for chunk in chunks:
                message = {
                    "id": message_id,
                    "role": "assistant",
                    "content": chunk
                }
                yield f"data: {json.dumps(message)}\n\n"
                await asyncio.sleep(0.02)
        else:
            error_message = {
                "id": message_id,
                "role": "assistant",
                "content": "Sorry, I couldn't generate a response."
            }
            yield f"data: {json.dumps(error_message)}\n\n"
            
    except Exception as e:
        error_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": f"Error: {str(e)}"
        }
        yield f"data: {json.dumps(error_message)}\n\n"

@app.get("/chat-stream")
async def chat_stream(prompt: str = None):
    """
    Endpoint to stream chat responses using web scraping and Gemini.
    """
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt parameter is required")

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*"
    }

    return StreamingResponse(
        generate_streaming_response(prompt),
        media_type="text/event-stream",
        headers=headers
    )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    Args:
        plain_password (str): The password in plain text
        hashed_password (str): The hashed password to compare against
    Returns:
        bool: True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password
    Args:
        password (str): The plain text password to hash
    Returns:
        str: The hashed password
    """
    return pwd_context.hash(password)


# User authentication endpoints
@app.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate):
    if user_repository is None:
        raise HTTPException(status_code=500, detail="Repository not initialized")
    existing_user = await user_repository.get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    created_user = await user_repository.create_user(user)
    jwt_token = create_access_token({"email":created_user.email})
    return Response(
        status_code=status.HTTP_201_CREATED,
        content=json.dumps({
            "message": "User created successfully",
            "user": {
                "id": str(created_user.id),
                "email": created_user.email,
                "name": created_user.name,
            },
            "access_token": jwt_token,
        }),
        media_type="application/json"
    )

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    user = await user_repository.get_user_by_email(request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    # Generate JWT token
    access_token = create_access_token({"email": user.email})
    
    # Set cookies with tokens
    response = JSONResponse(content={"message": "Login successful"})
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600  # 1 hour
    )
    return response

@app.post('/auth')
async def verify_auth(request: Request):
    try:
        # Get token from cookie
        token = request.cookies.get("access_token")
        if not token:
            return JSONResponse(content={"isAuthenticated": False})
            
        # Verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")
        if not email:
            return JSONResponse(content={"isAuthenticated": False})
            
        # Check if user exists
        user = await user_repository.get_user_by_email(email)
        if not user:
            return JSONResponse(content={"isAuthenticated": False})
            
        return JSONResponse(content={"isAuthenticated": True})
        
    except jwt.JWTError:
        return JSONResponse(content={"isAuthenticated": False})

@app.get("/test-stream")
async def test_stream():
    async def simple_generator():
        for i in range(5):
            # Each message is yielded with the proper SSE format
            message = {"id": str(uuid.uuid4()), "role": "assistant", "content": f"Test message {i}"}
            yield f"data: {json.dumps(message)}\n\n"
            await asyncio.sleep(1)  # Delay to simulate a stream
    return StreamingResponse(
        simple_generator(),
        media_type="text/event-stream"
    )
