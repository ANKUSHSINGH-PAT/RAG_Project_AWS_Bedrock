"""
Test script for Corrective RAG implementation

This script tests the Corrective RAG functionality with various queries
to demonstrate relevance evaluation and web search fallback.
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from QA_System.corrective_rag import create_corrective_rag
from QA_System.retrieval import get_llama_llm
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings
import boto3


def test_corrective_rag():
    """Test Corrective RAG with different types of queries"""
    
    print("=" * 80)
    print("CORRECTIVE RAG TEST")
    print("=" * 80)
    
    # Setup
    print("\n1. Setting up Bedrock client and embeddings...")
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )
    
    embeddings = BedrockEmbeddings(
        client=bedrock_client,
        model_id='amazon.titan-embed-text-v1'
    )
    
    # Load vector store
    print("2. Loading FAISS vector store...")
    try:
        vectorstore = FAISS.load_local(
            "faiss_index",
            embeddings,
            allow_dangerous_deserialization=True
        )
        print("   ✓ Vector store loaded successfully")
    except Exception as e:
        print(f"   ✗ Error loading vector store: {e}")
        print("   Please run ingestion.py first to create the vector store.")
        return
    
    # Create LLM
    print("3. Creating LLM...")
    llm = get_llama_llm()
    print("   ✓ LLM created successfully")
    
    # Create Corrective RAG
    print("4. Creating Corrective RAG instance...")
    crag = create_corrective_rag(vectorstore, llm, relevance_threshold=0.5)
    print("   ✓ Corrective RAG created successfully")
    
    # Test queries
    test_queries = [
        {
            "query": "What is the attention mechanism in transformers?",
            "description": "Query likely to be in the document (high relevance expected)"
        },
        {
            "query": "What is the weather today in New York?",
            "description": "Query unlikely to be in the document (low relevance, web search expected)"
        },
        {
            "query": "Explain the concept of neural networks",
            "description": "General ML query (may or may not be in document)"
        }
    ]
    
    print("\n" + "=" * 80)
    print("RUNNING TEST QUERIES")
    print("=" * 80)
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"\n{'─' * 80}")
        print(f"TEST {i}: {description}")
        print(f"{'─' * 80}")
        print(f"Query: {query}")
        print()
        
        try:
            # Query with metadata
            answer, metadata = crag.query(query, k=3, return_metadata=True)
            
            # Display results
            print("ANSWER:")
            print(answer)
            print()
            
            print("METADATA:")
            print(f"  • Retrieval Method: {metadata.get('retrieval_method', 'N/A')}")
            print(f"  • Documents Retrieved: {metadata.get('num_retrieved', 0)}")
            print(f"  • Relevant Documents: {metadata.get('num_relevant', 0)}")
            print(f"  • Relevance Score: {metadata.get('relevance_score', 0.0):.2f}")
            print(f"  • Web Search Used: {'Yes' if metadata.get('used_web_search', False) else 'No'}")
            
        except Exception as e:
            print(f"✗ Error during query: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_corrective_rag()

# Made with Bob
