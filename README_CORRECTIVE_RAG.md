# Corrective RAG (CRAG) Implementation Guide

## Overview

This project now includes **Corrective RAG (CRAG)**, an advanced retrieval-augmented generation approach that improves answer quality through relevance evaluation and adaptive retrieval strategies.

## What is Corrective RAG?

Corrective RAG enhances traditional RAG by:

1. **Relevance Evaluation**: Uses an LLM to evaluate if retrieved documents are actually relevant to the query
2. **Adaptive Retrieval**: Performs web search when retrieved documents have low relevance
3. **Quality Assurance**: Ensures the generation LLM receives high-quality, relevant context

## Architecture

```
User Query
    ↓
Vector Store Retrieval (k documents)
    ↓
Relevance Evaluation (LLM-based)
    ↓
    ├─→ High Relevance (≥ threshold)
    │       ↓
    │   Use Retrieved Documents
    │
    └─→ Low Relevance (< threshold)
            ↓
        Web Search Fallback
            ↓
        Combine Results
    ↓
Generate Answer with Best Context
```

## Installation

1. Install the required dependencies:

```bash
cd RAG_Project_AWS_Bedrock
pip install -r requirements.txt
```

Key new dependency:
- `duckduckgo-search`: For web search fallback

## Usage

### 1. Using the Streamlit App

Run the Streamlit app:

```bash
streamlit run rag_app.py
```

In the sidebar:
- Select **"Corrective RAG (CRAG)"** mode
- Adjust the **Relevance Threshold** (0.0 - 1.0)
  - Higher threshold = stricter relevance requirements
  - Lower threshold = more lenient
- Enable **"Show Retrieval Metadata"** to see the retrieval process details

### 2. Using Python Code

```python
from QA_System.corrective_rag import create_corrective_rag
from QA_System.retrieval import get_llama_llm
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import boto3

# Setup
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

embeddings = BedrockEmbeddings(
    client=bedrock_client,
    model_id='amazon.titan-embed-text-v1'
)

# Load vector store
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# Create LLM
llm = get_llama_llm()

# Create Corrective RAG
crag = create_corrective_rag(
    vectorstore=vectorstore,
    llm=llm,
    relevance_threshold=0.5  # Adjust as needed
)

# Query with metadata
answer, metadata = crag.query(
    "What is the attention mechanism?",
    k=3,
    return_metadata=True
)

print(f"Answer: {answer}")
print(f"Retrieval Method: {metadata['retrieval_method']}")
print(f"Relevance Score: {metadata['relevance_score']:.2f}")
print(f"Web Search Used: {metadata['used_web_search']}")
```

### 3. Using the Retrieval Module

```python
from QA_System.retrieval import get_response_corrective_rag, get_llama_llm
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import boto3

# Setup (same as above)
# ...

# Simple query
answer = get_response_corrective_rag(
    llm=llm,
    vectorstore=vectorstore,
    query="Your question here",
    relevance_threshold=0.5,
    return_metadata=False
)

# Query with metadata
answer, metadata = get_response_corrective_rag(
    llm=llm,
    vectorstore=vectorstore,
    query="Your question here",
    relevance_threshold=0.5,
    return_metadata=True
)
```

## Testing

Run the test script to see Corrective RAG in action:

```bash
cd RAG_Project_AWS_Bedrock
python test_corrective_rag.py
```

This will test:
- Queries likely in your documents (high relevance)
- Queries unlikely in your documents (low relevance, triggers web search)
- General queries (mixed relevance)

## Configuration

### Relevance Threshold

The relevance threshold determines when to use web search:

- **0.0 - 0.3**: Very lenient (rarely uses web search)
- **0.4 - 0.6**: Balanced (recommended)
- **0.7 - 1.0**: Strict (frequently uses web search)

### Number of Documents (k)

Adjust the number of documents retrieved:

```python
answer = crag.query(question, k=5)  # Retrieve 5 documents
```

## Components

### 1. RelevanceEvaluator (`corrective_rag.py`)

Evaluates document relevance using an LLM:
- Takes a question and document
- Returns YES/NO relevance judgment
- Calculates overall relevance score

### 2. WebSearchFallback (`corrective_rag.py`)

Performs web search when needed:
- Uses DuckDuckGo search
- Returns results as LangChain documents
- Handles errors gracefully

### 3. CorrectiveRAG (`corrective_rag.py`)

Main pipeline orchestrator:
- Retrieves documents from vector store
- Evaluates relevance
- Decides on correction strategy
- Generates final answer

## Metadata

When `return_metadata=True`, you get:

```python
{
    "retrieval_method": str,      # "vector_store", "web_search_fallback", etc.
    "relevance_score": float,     # 0.0 - 1.0
    "used_web_search": bool,      # True if web search was used
    "num_retrieved": int,         # Number of documents retrieved
    "num_relevant": int           # Number of relevant documents
}
```

## Benefits

1. **Better Out-of-Domain Handling**: Automatically searches the web for questions outside your document scope
2. **Reduced Hallucinations**: Only uses relevant context for generation
3. **Transparency**: Metadata shows exactly what retrieval strategy was used
4. **Adaptive**: Automatically adjusts based on document relevance

## Comparison: Standard RAG vs Corrective RAG

| Aspect | Standard RAG | Corrective RAG |
|--------|-------------|----------------|
| Retrieval | Fixed vector search | Adaptive (vector + web) |
| Relevance Check | None | LLM-based evaluation |
| Out-of-domain | May hallucinate | Web search fallback |
| Transparency | Limited | Full metadata |
| Accuracy | Good | Better |

## Troubleshooting

### Web Search Not Working

If web search fails:
1. Check internet connection
2. DuckDuckGo may have rate limits
3. The system will fall back to using available relevant documents

### Low Relevance Scores

If you consistently get low relevance scores:
1. Check if your documents cover the query topics
2. Adjust the relevance threshold lower
3. Consider adding more documents to your vector store

### Performance

Corrective RAG is slower than standard RAG because:
- Relevance evaluation requires LLM calls
- Web search adds latency
- Trade-off: Speed vs. Accuracy

## Files Modified/Created

- ✅ `QA_System/corrective_rag.py` - Main CRAG implementation
- ✅ `QA_System/retrieval.py` - Added CRAG support
- ✅ `rag_app.py` - Updated UI with CRAG mode
- ✅ `requirements.txt` - Added `duckduckgo-search`
- ✅ `test_corrective_rag.py` - Test script
- ✅ `README_CORRECTIVE_RAG.md` - This documentation

## Next Steps

1. Run the test script to verify installation
2. Try both Standard and Corrective RAG modes in the Streamlit app
3. Experiment with different relevance thresholds
4. Monitor the metadata to understand retrieval behavior

## References

- [Corrective RAG Paper](https://arxiv.org/abs/2401.15884)
- [LangChain Documentation](https://python.langchain.com/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

## Support

For issues or questions:
1. Check the metadata to understand what's happening
2. Review the test script output
3. Adjust relevance threshold based on your use case