from langchain_community.document_loaders import PyPDFLoader
file_path = "/home/samama/Projects/AskNust/Data/handbook.pdf"
loader = PyPDFLoader(file_path)
pages = []
for page in loader.alazy_load():
    pages.append(page)
print(f"{pages[19].metadata}\n")
print(pages[0].page_content)