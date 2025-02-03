from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_mistralai import ChatMistralAI
from langchain.schema import HumanMessage
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
import json
import uuid
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
import asyncio
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage
app = FastAPI()

# Update CORS middleware with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = OpenAIEmbeddings()
# Initialize Pinecone
vectorstore = PineconeVectorStore(
    
        index_name="asknust",
        embedding=embeddings
    )

# Initialize embeddings and vector store


# Initialize chat model
# chat_model = ChatMistralAI(
#     model="mistral-small-latest", 
#     streaming=True,
#     api_key="3in4IBXCqcSR34YCoHXItT10ae8lrEJE"
# )
chat_model = ChatOpenAI(model="gpt-4o-mini",streaming=True)
# Initialize chat model and retriever components
llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
# small_llm = ChatMistralAI("mistral-small-latest", 
#     api_key="3in4IBXCqcSR34YCoHXItT10ae8lrEJE"
#  )
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
    llm, retriever, contextualize_q_prompt
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
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

# Modify the langchain_generator function
async def langchain_generator(user_prompt: str, chat_history=[]):
    try:
        # Use the RAG chain instead of direct retrieval
        result = await rag_chain.ainvoke({
            "input": user_prompt,
            "chat_history": chat_history
        })
        
        message_id = str(uuid.uuid4())
        message = {
            "id": message_id,
            "role": "assistant",
            "content": result["answer"]
        }
        yield f"data: {json.dumps(message)}\n\n"
        
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
        # print("Regenarated Question",{retriever_output})
        return result["answer"]
    except Exception as e:
        return f"Error: {str(e)}"

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

if __name__ == "__main__":
    asyncio.run(main())

# # Modify the chat_stream endpoint to handle chat history
# @app.get("/chat-stream")
# async def chat_stream(prompt: str = None, chat_history: str = "[]"):
#     if not prompt:
#         raise HTTPException(status_code=400, detail="Prompt parameter is required")
    
#     try:
#         history_list = json.loads(chat_history)
#         formatted_history = [
#             HumanMessage(content=msg["content"]) if msg["role"] == "user" 
#             else SystemMessage(content=msg["content"])
#             for msg in history_list
#         ]
#     except json.JSONDecodeError:
#         formatted_history = []
    
#     return StreamingResponse(
#         langchain_generator(prompt, formatted_history),
#         media_type="text/event-stream",
#     )