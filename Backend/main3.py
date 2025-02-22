from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import uuid
import asyncio
import time
from contextlib import asynccontextmanager
from typing import List
import asyncio
import json
import uuid
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from googlesearch import search
import google.generativeai as genai

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = OpenAIEmbeddings()
vectorstore = PineconeVectorStore(
    index_name="asknust",
    embedding=embeddings
)
retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

chat_model = ChatGoogleGenerativeAI(model="Gemini 2.0 Flash-Lite Preview 02-05", streaming=True, api_key="your-google-api-key")

qa_system_prompt = """
You are an assistant for answering questions. Use the retrieved context and web search results.
If the answer is unknown, simply say so.
{context}
"""

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(chat_model, qa_prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# Web Scraper
async def search_google(query: str, num_results: int = 3) -> List[str]:
    urls = []
    try:
        search_results = search(query, num_results=num_results)
        urls = list(search_results)
        time.sleep(0.2)
    except Exception as e:
        print(f"Error during Google search: {e}")
    return urls

async def fetch_web_content(prompt: str, chatbot: AsyncWebCrawler):
    urls = await search_google(prompt)
    context_parts = []
    for url in urls:
        try:
            run_cfg = CrawlerRunConfig(only_text=True)
            result = await chatbot.arun(url=url, config=run_cfg)
            if result and result.markdown_v2:
                context_parts.append(f"Source ({url}):\n{result.markdown_v2}\n")
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            continue
    return "\n".join(context_parts)


async def langchain_generator(user_prompt: str, chatbot: AsyncWebCrawler):
    try:
        message_id = str(uuid.uuid4())
        processing_message = {"id": message_id, "role": "assistant", "content": ""}
        yield f"data: {json.dumps(processing_message)}\n\n"
        print("I came here1")

        # Fetch both RAG-based context and Web-based context in parallel
        rag_task = rag_chain.ainvoke({"input": user_prompt})
        web_task = fetch_web_content(user_prompt, chatbot)

        retrieved_context, web_context = await asyncio.gather(rag_task, web_task)
        print("I came here2")
        # Merge both contexts
        combined_context = f"**RAG Context:**\n{retrieved_context.get('text', '')}\n\n**Web Context:**\n{web_context}"

        # Single LLM call with both contexts
        async for event in question_answer_chain.astream_events(
            {"input": user_prompt, "context": combined_context}, version="v1"
        ):
            if event["name"] == "ChatOpenAI" and event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                message = {"id": message_id, "role": "assistant", "content": content}
                yield f"data: {json.dumps(message)}\n\n"
                await asyncio.sleep(0.02)

    except Exception as e:
        error_message = {"id": str(uuid.uuid4()), "role": "assistant", "content": f"Error: {str(e)}"}
        yield f"data: {json.dumps(error_message)}\n\n"


@app.get("/chat-stream")
async def chat_stream(prompt: str):
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt parameter is required")
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*"
    }
    chatbot = AsyncWebCrawler()
    return StreamingResponse(
        langchain_generator(prompt, chatbot),
        media_type="text/event-stream",
        headers=headers
    )
