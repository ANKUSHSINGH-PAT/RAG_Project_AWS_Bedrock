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

    # Check if data directory exists
    if not os.path.exists('data/'):
        print("Warning: 'data/' directory not found. Returning empty documents.")
        return []

    # Loop through all PDFs in the 'data' directory
    for file_name in os.listdir('data/'):
        if file_name.endswith('.pdf'):
            try:
                loader = PyPDFLoader(f'data/{file_name}')
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {file_name}: {e}")

    if not documents:
        print("Warning: No PDF documents found in 'data/' directory")
        return []

    # Split the documents into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    docs = text_splitter.split_documents(documents)
    
    print(f"Number of chunks: {len(docs)}")
    return docs

def get_vectorstore(docs):
    # Try to load existing FAISS index first
    if os.path.exists("faiss_index/index.faiss"):
        print("Loading existing FAISS index...")
        try:
            vectorstore = FAISS.load_local(
                "faiss_index",
                bedrock_embedding,
                allow_dangerous_deserialization=True
            )
            print("Successfully loaded existing FAISS index")
            return vectorstore
        except Exception as e:
            print(f"Error loading existing index: {e}")
    
    # If no existing index or docs provided, create new one
    if docs and len(docs) > 0:
        print("Creating new FAISS index from documents...")
        vectorstore = FAISS.from_documents(docs, embedding=bedrock_embedding)
        vectorstore.save_local("faiss_index")
        return vectorstore
    else:
        # Create a dummy vectorstore with sample text if no docs available
        print("Warning: No documents available. Creating minimal vectorstore.")
        from langchain.schema import Document
        sample_docs = [
            Document(page_content="This is a sample document for the RAG system. Please upload your PDF files to the data/ directory.", metadata={"source": "sample"})
        ]
        vectorstore = FAISS.from_documents(sample_docs, embedding=bedrock_embedding)
        return vectorstore




if __name__ == "__main__":
    docs = data_ingestion()
    get_vectorstore(docs)  # Replace None with actual embeddings instance
