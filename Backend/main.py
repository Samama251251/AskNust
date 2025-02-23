from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import json
import uuid
import asyncio
import time
import logging
from typing import List

from langchain_mistralai import ChatMistralAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from googlesearch import search
import google.generativeai as genai
from config.database import Database
from repositories.user_repository import UserRepository
from langchain_openai import ChatOpenAI

load_dotenv()
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

user_repository = None  # Global repository instance
chatbot = None         # Global crawler instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await Database.connect_db()
    
    global user_repository, chatbot
    user_repository = UserRepository()
    app.state.user_repository = user_repository
    
    # Initialize the crawler and enter its async context
    chatbot = AsyncWebCrawler()
    await chatbot.__aenter__()
    app.state.chatbot = chatbot
    
    yield
    
    print("Shutting down...")
    await Database.close_db()
    if chatbot:
        await chatbot.__aexit__(None, None, None)

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ask-nust.vercel.app",  # your production domain
    "http://localhost",             # allow localhost (any port if needed)
    "http://127.0.0.1"    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embeddings and vector store
embeddings = OpenAIEmbeddings()
vectorstore = PineconeVectorStore(
    index_name="asknust",
    embedding=embeddings
)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# Set up chat models
chat_model = ChatOpenAI(model_name="gpt-4o-mini", streaming=True)
small_llm = ChatMistralAI(model_name="mistral-small-latest", api_key="your-mistral-api-key", streaming=True)

qa_system_prompt = """
You are an assistant for answering questions about NUST (National University of Science and Technology) Islamabad, you are created by Muhammad Samama Usman of BSCS13E (Goated Section). 
Use the retrieved context and web search context to answer the question.
If the answer is not in the context then simply say that "I am sorry, I can answer questions only about NUST, please let me know if you need any help !"
If something is contradictory in the web context and the retrieved context, then prefer the web context.
{context}
"""

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(
    llm=chat_model, 
    prompt=qa_prompt,
    document_variable_name="context"
)

# Web Scraper helpers
async def search_google(query: str, num_results: int = 2) -> List[str]:
    urls = []
    try:
        search_results = search(query, num_results=num_results)
        urls = list(search_results)
        time.sleep(0.2)
    except Exception as e:
        print(f"Error during Google search: {e}")
    return urls

async def fetch_web_content(prompt: str, crawler: AsyncWebCrawler):
    urls = await search_google(prompt)
    context_parts = []
    for url in urls:
        if "nust" not in url:  # Process only URLs that contain "nust"
            continue

        # Special handling for NUST Library
        if "library.nust.edu.pk" in url:
            try:
                specialized_crawler = AsyncWebCrawler()
                await specialized_crawler.__aenter__()
                run_cfg = CrawlerRunConfig()
                result = await specialized_crawler.arun(url=url, config=run_cfg)
                await specialized_crawler.__aexit__(None, None, None)
                if result and result.markdown_v2:
                    context_parts.append(f"Source ({url}):\n{result.markdown_v2}\n")
            except Exception as e:
                print(f"Error scraping {url} with special settings: {e}")
                continue
        else:
            try:
                run_cfg = CrawlerRunConfig(only_text=True)
                result = await crawler.arun(url=url, config=run_cfg)
                if result and result.markdown_v2:
                    context_parts.append(f"Source ({url}):\n{result.markdown_v2}\n")
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue
    return "\n".join(context_parts)

async def getRelevantDocs(prompt: str):
    print("I came in getRelevantDocs")
    context = ""
    docs = await retriever.ainvoke(prompt)  # Use async invocation
    for doc in docs:
        context += doc.page_content
    print("Context:", context)
    return context

from langchain_core.messages import SystemMessage, HumanMessage

async def langchain_generator(user_prompt: str, crawler: AsyncWebCrawler):
    try:
        message_id = str(uuid.uuid4())
        print("Fetching context...")
        
        # Run both tasks concurrently
        rag_task = getRelevantDocs(user_prompt)
        web_task = fetch_web_content(user_prompt, crawler)
        retrieved_context, web_context = await asyncio.gather(rag_task, web_task)
        
        print("Context fetched.")
        full_context = f"Retrieved Context:\n{retrieved_context}\n\nWeb Search Context:\n{web_context}"
        
        messages = [
            SystemMessage(content=qa_system_prompt.format(context=full_context)),
            HumanMessage(content=user_prompt)
        ]
        
        async for event in chat_model.astream_events(messages, version="v1"):
            if event["name"] == "ChatOpenAI" and event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                yield f"data: {json.dumps({'id': message_id, 'role': 'assistant', 'content': content})}\n\n"
                await asyncio.sleep(0.02)
    except Exception as e:
        yield f"data: {json.dumps({'id': str(uuid.uuid4()), 'role': 'assistant', 'content': f'Error: {str(e)}'})}\n\n"

@app.get("/chat-stream")
async def chat_stream(request: Request, prompt: str):
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt parameter is required")
    if "nust" not in prompt.lower():
        prompt += " Nust University"
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*"
    }
    # Reuse the globally initialized crawler from the app state
    crawler = request.app.state.chatbot
    return StreamingResponse(
        langchain_generator(prompt, crawler),
        media_type="text/event-stream",
        headers=headers
    )

@app.get("/test")
async def test_endpoint():
    """
    A simple test endpoint to verify the API is running.
    Returns a JSON response with a status message and timestamp.
    """
    return {
        "status": "success",
        "message": "API is running",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": {
            "db_connected": user_repository is not None,
            "chatbot_initialized": chatbot is not None
        }
    }

from routers import chat, auth

app.include_router(chat.router, prefix="/chat")
app.include_router(auth.router, prefix="/auth")
