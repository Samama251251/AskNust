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
    # First, get all content with page numbers
    all_content = ""
    page_numbers = {}  # Track which content came from which page
    current_position = 0
    page_num = 0
    
    async for page in loader.alazy_load():
        content = page.page_content
        page_num += 1  # Increment page number manually
        # Record the page number for this content range
        page_numbers[current_position] = page_num
        all_content += content + "\n"
        current_position += len(content) + 1
    
    # Find all section matches in the complete text
    matches = list(re.finditer(r'(?m)^[\s]*?(?<!\d)(\d+)\.\s+([A-Z][^\n]+?)(?=\s*\n)', all_content))
    
    # Process each section
    for i in range(len(matches)):
        current_match = matches[i]
        section_heading = current_match.group(2)
        
        # Calculate section content boundaries
        start_pos = current_match.start()
        if i < len(matches) - 1:
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(all_content)
        
        # Extract the section content (including the heading)
        section_content = all_content[start_pos:end_pos].strip()
        
        # Clean up the content
        cleaned_content = re.sub(r'\s+', ' ', section_content).strip()
        
        # Find the page number for this section
        section_page = 1
        for pos, page in sorted(page_numbers.items()):
            if pos <= start_pos:
                section_page = page
            else:
                break
        
        # Create document
        doc = Document(
            page_content=cleaned_content,
            metadata={
                "page": section_page,
                "source": file_path,
                "heading": section_heading
            }
        )
        documents.append(doc)
        print(f"Found section: {section_heading} on page {section_page}")

async def main():
    await load_pages()
    
    # # Create a dictionary to store unique sections by their headings
    # unique_docs = {}
    # for doc in documents:
    #     heading = doc.metadata.get('heading', 'No Heading')
    #     if heading not in unique_docs:
    #         unique_docs[heading] = doc
    
    # # Convert back to list of unique documents
    # filtered_documents = list(unique_docs.values())
    
    # print(f"\nTotal unique sections to be indexed: {len(filtered_documents)}")
    
    # try:
    #     # Initialize embeddings
    #     embeddings = OpenAIEmbeddings()
        
    #     # Extract text content and metadata from filtered documents
    #     texts = [doc.page_content for doc in filtered_documents]
    #     metadatas = [doc.metadata for doc in filtered_documents]
        
    #     # Create vector store with unique documents
    #     vectorstore = PineconeVectorStore.from_texts(
    #         texts,
    #         metadatas=metadatas,
    #         index_name="asknust",
    #         embedding=embeddings
    #     )
    #     print("Successfully indexed unique documents to Pinecone")
        
    #     # Print indexed sections for verification
    #     print("\nIndexed Sections:")
    #     print("-" * 50)
    #     for doc in filtered_documents:
    #         print(f"\nSection: {doc.metadata.get('heading', 'No Heading')}")
    #         print(f"Page: {doc.metadata['page']}")
    #         print("-" * 30)
    #         print(doc.page_content[:200] + "...")
        
    # except Exception as e:
    #     print(f"An error occurred while creating embeddings: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
