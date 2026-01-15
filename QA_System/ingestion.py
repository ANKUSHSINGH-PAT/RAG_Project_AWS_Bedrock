from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from langchain_aws import BedrockLLM

import os
import boto3


#Bedroack  Client Setup
bedrock_client=boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)
bedrock_embedding=BedrockEmbeddings(
    client=bedrock_client,
    model_id='amazon.titan-embed-text-v1'
)

def data_ingestion():
    documents = []

    # Loop through all PDFs in the 'data' directory
    for file_name in os.listdir('data/'):
        if file_name.endswith('.pdf'):
            loader = PyPDFLoader(f'data/{file_name}')
            documents.extend(loader.load())

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    docs = text_splitter.split_documents(documents)
    
    print(f"Number of chunks: {len(docs)}")
    return docs

def get_vectorstore(docs):
   
    vectorstore = FAISS.from_documents(docs,embedding=bedrock_embedding)
    vectorstore.save_local("faiss_index")
    return vectorstore




if __name__ == "__main__":
    docs = data_ingestion()
    get_vectorstore(docs)  # Replace None with actual embeddings instance
