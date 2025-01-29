from fastapi import FastAPI
from starlette.responses import StreamingResponse
from langchain_mistralai import ChatMistralAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
import asyncio
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()
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

# Define prompt template
PROMPT_TEMPLATE = """
Answer the following question based on the provided context.

Context:
{context}

Question:
{question}

Answer:
"""

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=PROMPT_TEMPLATE
)

async def langchain_generator(user_prompt: str):
    """ Async generator to stream AI responses chunk-by-chunk with RAG """
    # Get relevant documents from vector store
    relevant_docs = vectorstore.similarity_search(user_prompt, k=2)
    
    # Combine document contents
    context = "\n".join([doc.page_content for doc in relevant_docs])
    print(context)
    
    # Format prompt with template
    formatted_prompt = prompt.format(
        context=context,
        question=user_prompt
    )
    
    # Stream response
    async for chunk in chat_model.astream([HumanMessage(content=formatted_prompt)]):
        print( chunk.content)

# @app.get("/chat-stream")
# async def chat_stream(prompt: str):
#     return StreamingResponse(langchain_generator(prompt), media_type="text/plain")

if __name__ == "__main__":
    text = "what happens if i come to hostel after 9pm"
    asyncio.run(langchain_generator(text))
