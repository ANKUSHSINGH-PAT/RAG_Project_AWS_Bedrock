"""
Corrective RAG (CRAG) Implementation

This module implements Corrective RAG which:
1. Retrieves documents from vector store
2. Evaluates relevance of retrieved documents
3. If relevant: uses them for generation
4. If not relevant: performs web search or uses alternative strategies
5. Generates final answer with corrected context
"""

import boto3
from typing import List, Dict, Tuple
from langchain_community.vectorstores import FAISS
from langchain_aws import BedrockEmbeddings, BedrockLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults


# -------------------------------
# Bedrock Client Setup
# -------------------------------
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)


# -------------------------------
# Relevance Evaluator
# -------------------------------
class RelevanceEvaluator:
    """Evaluates if retrieved documents are relevant to the query"""
    
    def __init__(self, bedrock_client):
        self.llm = BedrockLLM(
            client=bedrock_client,
            model_id="meta.llama3-8b-instruct-v1:0",
            model_kwargs={
                "temperature": 0,
                "max_tokens": 100
            }
        )
        
        self.evaluation_prompt = ChatPromptTemplate.from_template(
            """You are a relevance evaluator. Determine if the following document is relevant to answer the question.
            
Question: {question}

Document: {document}

Is this document relevant to answer the question? Answer with ONLY 'YES' or 'NO'.
If the document contains information that could help answer the question, say YES.
If the document is completely unrelated or doesn't help answer the question, say NO.

Answer (YES/NO):"""
        )
    
    def evaluate_document(self, question: str, document: str) -> bool:
        """
        Evaluate if a single document is relevant to the question
        
        Args:
            question: User's question
            document: Document content to evaluate
            
        Returns:
            True if relevant, False otherwise
        """
        prompt = self.evaluation_prompt.format_prompt(
            question=question,
            document=document[:1000]  # Limit document length for evaluation
        )
        
        response = self.llm.invoke(prompt.to_string()).strip().upper()
        
        # Check if response contains YES
        return "YES" in response
    
    def evaluate_documents(self, question: str, documents: List[Document]) -> Tuple[List[Document], float]:
        """
        Evaluate multiple documents and return relevant ones with relevance score
        
        Args:
            question: User's question
            documents: List of retrieved documents
            
        Returns:
            Tuple of (relevant_documents, relevance_score)
        """
        if not documents:
            return [], 0.0
        
        relevant_docs = []
        for doc in documents:
            if self.evaluate_document(question, doc.page_content):
                relevant_docs.append(doc)
        
        relevance_score = len(relevant_docs) / len(documents)
        return relevant_docs, relevance_score


# -------------------------------
# Web Search Fallback
# -------------------------------
class WebSearchFallback:
    """Performs web search when retrieved documents are not relevant"""
    
    def __init__(self):
        try:
            self.search = DuckDuckGoSearchResults(
                api_wrapper=DuckDuckGoSearchAPIWrapper(max_results=3)
            )
        except Exception as e:
            print(f"Warning: Could not initialize web search: {e}")
            self.search = None
    
    def search_web(self, query: str) -> List[Document]:
        """
        Perform web search and return results as documents
        
        Args:
            query: Search query
            
        Returns:
            List of documents from web search
        """
        if self.search is None:
            return []
        
        try:
            results = self.search.run(query)
            
            # Parse results and create documents
            documents = []
            if isinstance(results, str):
                # Simple string result
                documents.append(Document(
                    page_content=results,
                    metadata={"source": "web_search"}
                ))
            elif isinstance(results, list):
                # List of results
                for i, result in enumerate(results):
                    if isinstance(result, dict):
                        content = result.get('snippet', '') or result.get('content', '')
                        documents.append(Document(
                            page_content=content,
                            metadata={
                                "source": "web_search",
                                "title": result.get('title', f'Result {i+1}'),
                                "link": result.get('link', '')
                            }
                        ))
            
            return documents
        except Exception as e:
            print(f"Web search error: {e}")
            return []


# -------------------------------
# Corrective RAG Pipeline
# -------------------------------
class CorrectiveRAG:
    """
    Main Corrective RAG implementation
    
    Pipeline:
    1. Retrieve documents from vector store
    2. Evaluate relevance
    3. If relevance is low, perform web search
    4. Generate answer with corrected context
    """
    
    def __init__(self, vectorstore: FAISS, llm: BedrockLLM, relevance_threshold: float = 0.5):
        """
        Initialize Corrective RAG
        
        Args:
            vectorstore: FAISS vector store
            llm: Bedrock LLM for generation
            relevance_threshold: Minimum relevance score (0-1) to use retrieved docs
        """
        self.vectorstore = vectorstore
        self.llm = llm
        self.relevance_threshold = relevance_threshold
        self.evaluator = RelevanceEvaluator(bedrock_client)
        self.web_search = WebSearchFallback()
        
        self.generation_prompt = ChatPromptTemplate.from_template(
            """You are an enterprise AI assistant.
Answer the question using the provided context.

Context:
{context}

Question:
{question}

Provide a comprehensive answer. If the context doesn't contain enough information, say so.

Answer:"""
        )
    
    def retrieve_documents(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve documents from vector store"""
        return self.vectorstore.similarity_search(query, k=k)
    
    def correct_retrieval(self, query: str, k: int = 3) -> Tuple[List[Document], Dict]:
        """
        Perform corrective retrieval
        
        Args:
            query: User's question
            k: Number of documents to retrieve
            
        Returns:
            Tuple of (final_documents, metadata)
        """
        metadata = {
            "retrieval_method": "vector_store",
            "relevance_score": 0.0,
            "used_web_search": False,
            "num_retrieved": 0,
            "num_relevant": 0
        }
        
        # Step 1: Retrieve from vector store
        retrieved_docs = self.retrieve_documents(query, k=k)
        metadata["num_retrieved"] = len(retrieved_docs)
        
        if not retrieved_docs:
            # No documents retrieved, try web search
            print("No documents retrieved from vector store. Trying web search...")
            web_docs = self.web_search.search_web(query)
            metadata["retrieval_method"] = "web_search_only"
            metadata["used_web_search"] = True
            return web_docs, metadata
        
        # Step 2: Evaluate relevance
        relevant_docs, relevance_score = self.evaluator.evaluate_documents(query, retrieved_docs)
        metadata["relevance_score"] = relevance_score
        metadata["num_relevant"] = len(relevant_docs)
        
        print(f"Relevance Score: {relevance_score:.2f} ({len(relevant_docs)}/{len(retrieved_docs)} docs relevant)")
        
        # Step 3: Decide on correction strategy
        if relevance_score >= self.relevance_threshold:
            # Good relevance, use retrieved documents
            print("Using retrieved documents (good relevance)")
            return relevant_docs, metadata
        else:
            # Low relevance, perform web search
            print(f"Low relevance ({relevance_score:.2f}). Performing web search...")
            web_docs = self.web_search.search_web(query)
            metadata["retrieval_method"] = "web_search_fallback"
            metadata["used_web_search"] = True
            
            if web_docs:
                # Combine relevant docs (if any) with web search results
                final_docs = relevant_docs + web_docs
                print(f"Combined {len(relevant_docs)} relevant docs with {len(web_docs)} web results")
                return final_docs, metadata
            else:
                # Web search failed, use whatever relevant docs we have
                print("Web search failed. Using available relevant documents.")
                metadata["retrieval_method"] = "vector_store_fallback"
                return relevant_docs if relevant_docs else retrieved_docs, metadata
    
    def generate_answer(self, query: str, documents: List[Document]) -> str:
        """Generate answer using LLM with provided documents"""
        if not documents:
            return "I don't have enough information to answer this question."
        
        # Combine document contents
        context = "\n\n".join([
            f"[Source: {doc.metadata.get('source', 'document')}]\n{doc.page_content}"
            for doc in documents
        ])
        
        # Generate answer
        prompt = self.generation_prompt.format_prompt(
            context=context,
            question=query
        )
        
        response = self.llm.invoke(prompt.to_string())
        return response
    
    def query(self, question: str, k: int = 3, return_metadata: bool = False):
        """
        Main query method for Corrective RAG
        
        Args:
            question: User's question
            k: Number of documents to retrieve
            return_metadata: Whether to return metadata about the retrieval process
            
        Returns:
            Answer string, or tuple of (answer, metadata) if return_metadata=True
        """
        # Perform corrective retrieval
        documents, metadata = self.correct_retrieval(question, k=k)
        
        # Generate answer
        answer = self.generate_answer(question, documents)
        
        if return_metadata:
            return answer, metadata
        return answer


# -------------------------------
# Helper Functions
# -------------------------------
def create_corrective_rag(vectorstore: FAISS, llm: BedrockLLM, relevance_threshold: float = 0.5) -> CorrectiveRAG:
    """
    Factory function to create a CorrectiveRAG instance
    
    Args:
        vectorstore: FAISS vector store
        llm: Bedrock LLM
        relevance_threshold: Minimum relevance score (default: 0.5)
        
    Returns:
        CorrectiveRAG instance
    """
    return CorrectiveRAG(vectorstore, llm, relevance_threshold)


# -------------------------------
# Example Usage
# -------------------------------
if __name__ == "__main__":
    from langchain_community.vectorstores import FAISS
    from langchain_aws import BedrockEmbeddings
    
    # Load embeddings
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
    llm = BedrockLLM(
        client=bedrock_client,
        model_id="meta.llama3-8b-instruct-v1:0",
        model_kwargs={
            "temperature": 0,
            "max_tokens": 512
        }
    )
    
    # Create Corrective RAG
    crag = create_corrective_rag(vectorstore, llm, relevance_threshold=0.5)
    
    # Test query
    question = "What is the attention mechanism in transformers?"
    print(f"\nQuestion: {question}\n")
    
    answer, metadata = crag.query(question, k=3, return_metadata=True)
    
    print(f"\nAnswer: {answer}")
    print(f"\nMetadata: {metadata}")

# Made with Bob
