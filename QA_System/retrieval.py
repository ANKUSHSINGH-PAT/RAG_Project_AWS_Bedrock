import boto3
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
from langchain_aws import BedrockLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from QA_System.ingestion import get_vectorstore
from QA_System.corrective_rag import CorrectiveRAG, create_corrective_rag

# -------------------------------
# Bedrock Runtime Client
# -------------------------------
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

# -------------------------------
# Prompt
# -------------------------------
prompt = ChatPromptTemplate.from_template(
    """
    You are an enterprise AI assistant.
    Answer only using the provided context.

    Context:
    {context}

    Question:
    {question}

    If the answer is not in the context, say "I don't know".
    """
)

# -------------------------------
# LLM
# -------------------------------
def get_llama_llm():
    llm = BedrockLLM(
        client=bedrock_client,
        model_id="meta.llama3-8b-instruct-v1:0",
        model_kwargs={
            "temperature": 0,
            "max_tokens": 512
        },
    )
    return llm

# -------------------------------
# RAG Query
# -------------------------------
def get_response_llm(llm, vectorstore, query):
    # Retrieve relevant documents from the vector store
    docs = vectorstore.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    # Format the prompt with context and question
    formatted_prompt = prompt.format_prompt(context=context, question=query)

    # Get response from the LLM
    response = llm.invoke(formatted_prompt.to_string())
    return response

# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    # Create embeddings object
    embeddings = BedrockEmbeddings(
        client=bedrock_client,
        model_id='amazon.titan-embed-text-v1'
    )

    # Load FAISS safely
    vectorstore = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True  
    )

    # Load LLM
    llm = get_llama_llm()

    # Example query
    query = "What is attentation mechanism in transformers?"
    response = get_response_llm(llm, vectorstore, query)
    print("Response:", response)


# -------------------------------
# Corrective RAG Query (New)
# -------------------------------
def get_response_corrective_rag(llm, vectorstore, query, relevance_threshold=0.5, return_metadata=False):
    """
    Query using Corrective RAG approach
    
    Args:
        llm: Bedrock LLM instance
        vectorstore: FAISS vector store
        query: User's question
        relevance_threshold: Minimum relevance score (0-1) to use retrieved docs
        return_metadata: Whether to return metadata about the retrieval process
        
    Returns:
        Answer string, or tuple of (answer, metadata) if return_metadata=True
    """
    crag = create_corrective_rag(vectorstore, llm, relevance_threshold)
    return crag.query(query, k=3, return_metadata=return_metadata)
