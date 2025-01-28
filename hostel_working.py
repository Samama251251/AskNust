from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import asyncio
import re

file_path = "/home/samama/Projects/AskNust/Data/handbook.pdf"
loader = PyPDFLoader(file_path)
documents = []  # Array to store Document objects

async def load_pages():
    page_num = 1
    actual_page = 0
    async for page in loader.alazy_load():
        content = page.page_content
        sections = re.split(r'\n\s*\d+\.\s+', content)
        sections = [section.strip() for section in sections if section.strip()]
        page_sections  = []
        # Create Document object for each section
        for section in sections:
            doc = Document(
                page_content=section,
                metadata={
                    "page": page_num,
                    "source": file_path
                }
            )
            page_sections.append(doc)
            documents.append(doc)
        # Optional: Print progress
        if page_num== 1:
            #print(f"Processed page {page_num} - Found {len(sections)} sections")
            for i,section in enumerate(page_sections):
                print("Section",i,":",section.page_content)
        page_num += 1
async def main():

    await load_pages()
    # # # Print total documents collected
    for i in range(len(documents)):
        if i>20 and i<30:
            print("Section",i,":\n",documents[i].page_content)
    # # print(f"\nTotal sections collected: {len(documents)}")
    
    # # # Set up environment variables
    # # os.environ['OPENAI_API_KEY'] = 'sk-SNmrvRHrImV6BNABsxAgCgpVQw1dIgsGcVQsDbeMdMT3BlbkFJkE4nudEUff3LhipEAFd4TU4EK4NCC3oorbInBsPikA'
    # # os.environ['PINECONE_API_KEY'] = 'pcsk_71EcLV_3A37JhnuxAn3UX5bEJX3cbBP7aNNi5ifksSTyzWgatizjr7GWM7Rspb11AXtHCQ'
    
    # # try:
    # #     # Initialize embeddings
    # #     embeddings = OpenAIEmbeddings()
        
    # #     # Extract text content and metadata from documents
    # #     texts = [doc.page_content for doc in documents]
    # #     metadatas = [doc.metadata for doc in documents]
        
    # #     # Create vector store
    # #     vectorstore = PineconeVectorStore.from_texts(
    # #         texts,
    # #         metadatas=metadatas,
    # #         index_name="asknust",
    # #         embedding=embeddings
    # #     )
    # #     print("Successfully indexed all documents to Pinecone")
        
    # # except Exception as e:
    #     print(f"An error occurred while creating embeddings: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())