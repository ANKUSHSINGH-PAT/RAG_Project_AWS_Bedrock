import streamlit as st

from QA_System.ingestion import get_vectorstore, data_ingestion
from QA_System.retrieval import get_llama_llm, get_response_llm

# ------------------ Streamlit Config ------------------
st.set_page_config(page_title="RAG with AWS Bedrock", layout="wide")
st.title("📄 RAG with AWS Bedrock")

# ------------------ Load Resources ------------------
@st.cache_resource
def load_resources():
    docs=data_ingestion()
    vectorstore = get_vectorstore(docs)
    llm = get_llama_llm()
    return vectorstore, llm

vectorstore, llm = load_resources()

# ------------------ User Input ------------------
user_query = st.text_input("Enter your question")

if user_query:
    with st.spinner("Generating answer..."):
        response = get_response_llm(
            llm=llm,
            vectorstore=vectorstore,
            query=user_query
        )

    st.subheader("Answer")
    st.write(response)
