from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
load_dotenv()
# Set up environment variables
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['PINECONE_API_KEY'] = os.getenv('PINECONE_API_KEY')

def search_documents(query: str, k: int = 3):
    # Initialize embeddings and vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = PineconeVectorStore(
        index_name="asknust",
        embedding=embeddings
    )
    
    # Perform similarity search
    results = vectorstore.similarity_search(
        query=query,
        k=k  # Return top 2 most similar documents
    )
    
    return results

# Example usage
if __name__ == "__main__":
    query =  "What happens if I my attendance is below 75%" 
    matching_docs = search_documents(query)
    
    print("\nTop 3 matching documents:")
    for i, doc in enumerate(matching_docs, 1):
        print(f"\nDocument {i}:")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
