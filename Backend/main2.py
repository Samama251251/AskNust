from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from langchain_mistralai import ChatMistralAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
import json
import uuid
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config.database import Database
from repositories.user_repository import UserRepository
from models.user import UserCreate, UserResponse
import asyncio
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage
from contextlib import asynccontextmanager
from utils.auth import create_access_token
from fastapi import Response,status
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from jose import JWTError, jwt
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

load_dotenv()
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Global variable for repository
user_repository = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    await Database.connect_db()
    
    # Initialize repositories after database connection
    global user_repository
    user_repository = UserRepository()
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await Database.close_db()

app = FastAPI(lifespan=lifespan)

# Update CORS middleware with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = OpenAIEmbeddings()
vectorstore = PineconeVectorStore(
    index_name="asknust",
    embedding=embeddings
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


chat_model = ChatGoogleGenerativeAI(model="Gemini 2.0 Flash-Lite Preview 02-05",streaming=True, api_key="AIzaSyCcZp2pD7_zlhwJl9nHGPBI-8YQOSSCFsA")
# Initialize chat model and retriever components
# llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
small_llm = ChatMistralAI(model_name="mistral-small-latest", 
    api_key="3in4IBXCqcSR34YCoHXItT10ae8lrEJE",
    streaming=True,
 )

# Contextualize question prompt
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it but make sure the question does not contain the word Nust in either case"
)

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create retriever from vectorstore
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# Create history-aware retriever
history_aware_retriever = create_history_aware_retriever(
    small_llm, retriever, contextualize_q_prompt
)

# Create QA prompt
qa_system_prompt = (
    "You are an assistant for question-answering tasks. Use "
    "the following pieces of retrieved context to answer the "
    "question. If you don't know the answer, just say that you "
    "don't know."
    "\n\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

# Create the chain
question_answer_chain = create_stuff_documents_chain(chat_model, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
async def langchain_generator(user_prompt: str, chat_history=[]):
    try:
        message_id = str(uuid.uuid4())
        logging.debug("I came here")
        async for event in rag_chain.astream_events(
            {"input": user_prompt, "chat_history": chat_history},
            version="v1"
        ):
            # Check if the event is from ChatOpenAI
            if event["name"] == "ChatOpenAI" and event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                message = {
                    "id": message_id,
                    "role": "assistant",
                    "content": content
                }
                yield f"data: {json.dumps(message)}\n\n"
                await asyncio.sleep(0.02)
        
    except Exception as e:
        error_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": f"Error: {str(e)}"
        }
        yield f"data: {json.dumps(error_message)}\n\n"
# Test function that doesn't require server/streaming
async def test_chat(prompt: str, chat_history: list = []):
    """
    Test the RAG chain directly without server/streaming
    Args:
        prompt (str): User's question
        chat_history (list): List of previous messages
    Returns:
        str: Assistant's response
    """
    try:
        result = await rag_chain.ainvoke({
            "input": prompt,
            "chat_history": chat_history
        })
        print("this is before returning\n")
        print(result)
        print()
        return result["answer"]
    except Exception as e:
        return f"Error: {str(e)}"

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

async def main():
    # Create dummy chat history with university-related questions
    chat_history = [
        HumanMessage(content="What does credit hour mean?"),
        SystemMessage(content="A credit hour represents the amount of time a student is expected to spend in class and studying per week. One credit hour typically equals one hour of classroom time and two hours of out-of-class work."),
        HumanMessage(content="How many credit hours do I need to graduate?"),
        SystemMessage(content="Most undergraduate programs at NUST require completing 130-140 credit hours to graduate, spread across 8 semesters.")
    ]
    
    # Test new question with chat history context
    question = "How many credit hours does a software engineering student requies to graduate from Nust"
    print(f"\nUser: {question}")
    response = await test_chat(question, chat_history)
    print(f"AI: {response}")


@app.get("/chat-stream")
async def chat_stream(prompt: str = None, chat_history: str = "[]"):
    """
    Endpoint to stream chat responses using SSE.
    Expects:
      - prompt: a string provided via query parameters.
      - chat_history: a JSON string representing the previous conversation.
    """
    logging.info("Received streaming request for chat-stream")
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*"
    }

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt parameter is required")

    try:
        # Parse and format the chat history
        history_list = json.loads(chat_history)
        formatted_history = [
            HumanMessage(content=msg["content"]) if msg["role"] == "user"
            else SystemMessage(content=msg["content"])
            for msg in history_list
        ]

        return StreamingResponse(
            langchain_generator(prompt, formatted_history),
            media_type="text/event-stream",
            headers=headers
        )

    except Exception as e:
        logging.exception("Error in chat_stream endpoint:")
        raise HTTPException(status_code=500, detail=str(e))

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

if __name__ == "__main__":
    asyncio.run(main())


    