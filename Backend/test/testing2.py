import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from dotenv import load_dotenv
load_dotenv()
os.environ['OPENAI_API_KEY'] = 'sk-SNmrvRHrImV6BNABsxAgCgpVQw1dIgsGcVQsDbeMdMT3BlbkFJkE4nudEUff3LhipEAFd4TU4EK4NCC3oorbInBsPikA'
os.environ['PINECONE_API_KEY'] = 'pcsk_71EcLV_3A37JhnuxAn3UX5bEJX3cbBP7aNNi5ifksSTyzWgatizjr7GWM7Rspb11AXtHCQ'

index_name = "asknust"
embeddings = OpenAIEmbeddings()

# path to an example text file

texts = ["I am going to pakistan"]

vectorstore_from_texts = PineconeVectorStore.from_texts(
        texts,
        index_name=index_name,
        embedding=embeddings
    )
print("Successfully done")