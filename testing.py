from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import asyncio
import re

file_path = "/home/samama/Projects/AskNust/Data/NUST_Hostels.pdf"
loader = PyPDFLoader(file_path)
documents = []  # Array to store Document objects

async def load_pages():
    page_num = 1
    async for page in loader.alazy_load():
        content = page.page_content
        sections = re.split(r'\n\s*\d+\.\s+', content)
        sections = [section.strip() for section in sections if section.strip()]
        
        # Create Document object for each section
        for section in sections:
            doc = Document(
                page_content=section,
                metadata={
                    "page": page_num,
                    "source": file_path
                }
            )
            documents.append(doc)
        # Optional: Print progress
        print(f"Processed page {page_num} - Found {len(sections)} sections")
        page_num += 1

async def main():
    await load_pages()
    # Print total documents collected
    os.environ['OPENAI_API_KEY'] = 'sk-SNmrvRHrImV6BNABsxAgCgpVQw1dIgsGcVQsDbeMdMT3BlbkFJkE4nudEUff3LhipEAFd4TU4EK4NCC3oorbInBsPikA'
    os.environ['PINECONE_API_KEY'] = 'ad2e0f2e-e8e1-4688-a05d-0e1cf7b8eeb6'
    print(f"\nTotal sections collected: {len(documents)}")
    embeddings = OpenAIEmbeddings()
    # Optional: Print first few documents to verify
    print("\nFirst few sections:")
    for doc in documents:
        print(f"Content:\n {doc.page_content}")
      # Print first 200 chars of each section
    # Extract text content from documents
    # texts = [doc.page_content for doc in documents]
    # metadatas = [doc.metadata for doc in documents]
    
    # vectorstore_from_texts = PineconeVectorStore.from_texts(
    #     texts,
    #     metadatas=metadatas,  # Pass metadata separately
    #     index_name="asknust",
    #     embedding=embeddings
    # )
    # print("Indexing Done")
    

if __name__ == "__main__":
    asyncio.run(main())