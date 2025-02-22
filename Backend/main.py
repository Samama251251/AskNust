from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from config.database import Database
from repositories.user_repository import UserRepository
from crawl4ai import AsyncWebCrawler
import google.generativeai as genai

load_dotenv()
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

user_repository = None  # Global repository instance
chatbot = None          # Global chatbot instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    await Database.connect_db()
    
    global user_repository, chatbot
    user_repository = UserRepository()
    app.state.user_repository = user_repository  # Store repo in app state
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from the routers package
from routers import chat, auth
app.include_router(chat.router, prefix="/chat")
app.include_router(auth.router, prefix="/auth")