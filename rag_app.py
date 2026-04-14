from fastapi import FastAPI
from pydantic import BaseModel

# ✅ NEW IMPORTS
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from QA_System.ingestion import get_vectorstore, data_ingestion
from QA_System.retrieval import get_llama_llm
from QA_System.corrective_rag import create_corrective_rag

app = FastAPI(title="RAG with AWS Bedrock")

# ✅ ENABLE CORS (important for UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Load resources once
# -------------------------------
docs = data_ingestion()
vectorstore = get_vectorstore(docs)
llm = get_llama_llm()

crag = create_corrective_rag(vectorstore, llm, relevance_threshold=0.5)

# -------------------------------
# Request schema
# -------------------------------
class QueryRequest(BaseModel):
    query: str
    mode: str = "standard"

# -------------------------------
# API endpoint
# -------------------------------
@app.post("/ask")
def ask_question(req: QueryRequest):
    if req.mode == "corrective":
        answer, metadata = crag.query(
            req.query,
            return_metadata=True
        )
        return {
            "answer": answer,
            "metadata": metadata
        }
    else:
        from QA_System.retrieval import get_response_llm
        
        answer = get_response_llm(
            llm=llm,
            vectorstore=vectorstore,
            query=req.query
        )
        return {"answer": answer}

# -------------------------------
# Health check
# -------------------------------
@app.get("/")
def health():
    return {"status": "running"}

# -------------------------------
# ✅ SERVE UI
# -------------------------------

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root UI
@app.get("/ui")
def serve_ui():
    return FileResponse("static/index.html")