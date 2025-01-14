import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter

os.environ['OPENAI_API_KEY'] = 'sk-SNmrvRHrImV6BNABsxAgCgpVQw1dIgsGcVQsDbeMdMT3BlbkFJkE4nudEUff3LhipEAFd4TU4EK4NCC3oorbInBsPikA'
os.environ['PINECONE_API_KEY'] = 'ad2e0f2e-e8e1-4688-a05d-0e1cf7b8eeb6'

index_name = "asknust"
embeddings = OpenAIEmbeddings()

    # path to an example text file

texts = ["Tonight, I call on the Senate to: Pass the Freedom to Vote Act.", "ne of the most serious constitutional responsibilities a President has is nominating someone to serve on the United States Supreme Court.", "One of our nation’s top legal minds, who will continue Justice Breyer’s legacy of excellence."]

vectorstore_from_texts = PineconeVectorStore.from_texts(
        texts,
        index_name=index_name,
        embedding=embeddings
    )
