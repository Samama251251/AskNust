from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import asyncio
import re

file_path = "/home/samama/Projects/AskNust/Data/handbook_removed-2.pdf"
loader = PyPDFLoader(file_path)
documents = []  # Array to store Document objects

async def load_pages():
    page_num = 1
    actual_page = 0
    async for page in loader.alazy_load():
        content = page.page_content
        # Remove both footer text formats
        content = re.sub(r'NUST Undergraduate Student Handbook \d+', '', content)
        content = re.sub(r'\d+\s+NUST Undergraduate Student Handbook', '', content)
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
        page_num += 1
async def main():

    await load_pages()
    # Combine short sections with previous sections
    i = 1
    while i < len(documents):
        word_count = len(documents[i].page_content.split())
        if word_count < 10:
            # Append current section to previous section
            documents[i-1].page_content = documents[i-1].page_content + " " + documents[i].page_content
            # Remove current section
            documents.pop(i)
        else:
            i += 1

    # Print sections 60-70 for verification
    for i in range(len(documents)):
        if i>60 and i<70:
            print("No of words in section",i,":",len(documents[i].page_content.split()))
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