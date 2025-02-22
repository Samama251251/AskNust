from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_mistralai import ChatMistralAI
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import json
import uuid
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from contextlib import asynccontextmanager
from langchain_google_genai import ChatGoogleGenerativeAI
import logging

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

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

chat_model = ChatGoogleGenerativeAI(model="Gemini 2.0 Flash-Lite Preview 02-05", streaming=True, api_key="your-google-api-key")
small_llm = ChatMistralAI(model_name="mistral-small-latest", api_key="your-mistral-api-key", streaming=True)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

qa_system_prompt = (
    "You are an assistant for question-answering tasks. Use "
    "the following pieces of retrieved context to answer the "
    "question. If you don't know the answer, just say that you "
    "don't know.\n\n{context}"
)

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", qa_system_prompt),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(chat_model, qa_prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

async def langchain_generator(user_prompt: str):
    try:
        message_id = str(uuid.uuid4())
        async for event in rag_chain.astream_events({"input": user_prompt}, version="v1"):
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

@app.get("/chat-stream")
async def chat_stream(prompt: str):
    logging.info("Received streaming request for chat-stream")
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*"
    }

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt parameter is required")

    return StreamingResponse(
        langchain_generator(prompt),
        media_type="text/event-stream",
        headers=headers
    )

@app.get("/test-stream")
async def test_stream():
    async def simple_generator():
        for i in range(5):
            message = {"id": str(uuid.uuid4()), "role": "assistant", "content": f"Test message {i}"}
            yield f"data: {json.dumps(message)}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(
        simple_generator(),
        media_type="text/event-stream"
    )
