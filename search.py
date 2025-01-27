from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import os

# Set up environment variables
os.environ['OPENAI_API_KEY'] = 'sk-SNmrvRHrImV6BNABsxAgCgpVQw1dIgsGcVQsDbeMdMT3BlbkFJkE4nudEUff3LhipEAFd4TU4EK4NCC3oorbInBsPikA'
os.environ['PINECONE_API_KEY'] = 'pcsk_71EcLV_3A37JhnuxAn3UX5bEJX3cbBP7aNNi5ifksSTyzWgatizjr7GWM7Rspb11AXtHCQ'

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
    query = "what will happen if a student comes to hostel after 11pm" 
    matching_docs = search_documents(query)
    
    print("\nTop 2 matching documents:")
    for i, doc in enumerate(matching_docs, 1):
        print(f"\nDocument {i}:")
        print(f"Content: {doc.page_content}")
        print(f"Metadata: {doc.metadata}")
