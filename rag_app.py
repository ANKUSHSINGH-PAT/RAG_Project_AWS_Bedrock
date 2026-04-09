import streamlit as st

from QA_System.ingestion import get_vectorstore, data_ingestion
from QA_System.retrieval import get_llama_llm, get_response_llm, get_response_corrective_rag

# ------------------ Streamlit Config ------------------
st.set_page_config(page_title="RAG with AWS Bedrock", layout="wide")
st.title("📄 RAG with AWS Bedrock")

# ------------------ Sidebar Configuration ------------------
st.sidebar.title("⚙️ Configuration")
rag_mode = st.sidebar.radio(
    "Select RAG Mode:",
    ["Standard RAG", "Corrective RAG (CRAG)"],
    help="Standard RAG: Basic retrieval\nCorrective RAG: Evaluates relevance and uses web search fallback"
)

if rag_mode == "Corrective RAG (CRAG)":
    relevance_threshold = st.sidebar.slider(
        "Relevance Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="Minimum relevance score to use retrieved documents (0-1)"
    )
    show_metadata = st.sidebar.checkbox(
        "Show Retrieval Metadata",
        value=True,
        help="Display information about the retrieval process"
    )

# ------------------ Load Resources ------------------
@st.cache_resource
def load_resources():
    docs=data_ingestion()
    vectorstore = get_vectorstore(docs)
    llm = get_llama_llm()
    return vectorstore, llm

vectorstore, llm = load_resources()

# ------------------ User Input ------------------
user_query = st.text_input("Enter your question?")

if user_query:
    with st.spinner("Generating answer..."):
        if rag_mode == "Standard RAG":
            # Standard RAG
            response = get_response_llm(
                llm=llm,
                vectorstore=vectorstore,
                query=user_query
            )
            
            st.subheader("Answer")
            st.write(response)
            
        else:
            # Corrective RAG
            if show_metadata:
                response, metadata = get_response_corrective_rag(
                    llm=llm,
                    vectorstore=vectorstore,
                    query=user_query,
                    relevance_threshold=relevance_threshold,
                    return_metadata=True
                )
                
                st.subheader("Answer")
                st.write(response)
                
                # Display metadata
                st.subheader("📊 Retrieval Metadata")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Retrieval Method", metadata.get("retrieval_method", "N/A"))
                    st.metric("Documents Retrieved", metadata.get("num_retrieved", 0))
                
                with col2:
                    relevance = metadata.get("relevance_score", 0.0)
                    st.metric("Relevance Score", f"{relevance:.2f}")
                    st.metric("Relevant Documents", metadata.get("num_relevant", 0))
                
                with col3:
                    web_search = "Yes" if metadata.get("used_web_search", False) else "No"
                    st.metric("Web Search Used", web_search)
                
                # Show detailed metadata in expander
                with st.expander("🔍 Detailed Metadata"):
                    st.json(metadata)
            else:
                response = get_response_corrective_rag(
                    llm=llm,
                    vectorstore=vectorstore,
                    query=user_query,
                    relevance_threshold=relevance_threshold,
                    return_metadata=False
                )
                
                st.subheader("Answer")
                st.write(response)

# ------------------ Information Section ------------------
with st.expander("ℹ️ About Corrective RAG"):
    st.markdown("""
    ### What is Corrective RAG (CRAG)?
    
    Corrective RAG is an advanced retrieval-augmented generation approach that improves answer quality by:
    
    1. **Relevance Evaluation**: Evaluates if retrieved documents are actually relevant to the question
    2. **Adaptive Retrieval**: If documents aren't relevant enough, performs web search as fallback
    3. **Quality Assurance**: Ensures the LLM receives high-quality context for generation
    
    ### How it works:
    
    1. **Retrieve** documents from the vector store
    2. **Evaluate** each document's relevance using an LLM
    3. **Decide** based on relevance score:
       - High relevance (≥ threshold): Use retrieved documents
       - Low relevance (< threshold): Perform web search and combine results
    4. **Generate** answer with the best available context
    
    ### Benefits:
    
    - ✅ Better handling of out-of-domain questions
    - ✅ Reduced hallucinations
    - ✅ More accurate answers
    - ✅ Transparent retrieval process
    """)
