import boto3
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from langchain_aws import BedrockLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from QA_System.ingestion import get_vecrtorstore

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

def get_llama_llm():
    llm = BedrockLLM(
        client=bedrock_client,
        model_id="meta-llama-2-70b-instruct-v2",
        temperature=0,
        max_tokens=1000,
        output_parser=StrOutputParser()
    )
    return llm

def get_response_llm(llm,vectorstore, query):
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
    vectorstore = FAISS.load_local("faiss_index", embedding=BedrockEmbeddings(
        client=bedrock_client,
        model_id='amazon.titan-embed-text-v1'
    ))
    llm = get_llama_llm()
    query = "What is the company's return policy?"
    response = get_response_llm(llm, vectorstore, query)
    print("Response:", response)
