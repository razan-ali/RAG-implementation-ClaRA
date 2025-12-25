import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import settings
from models import (
    QueryRequest,
    UploadResponse,
    HealthResponse,
    ClarificationResponse,
    AnswerResponse
)
from document_processor import DocumentProcessor
from vector_store import VectorStore
from clara_engine import ClaRAEngine


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="RAG system with Apple's ClaRA approach for clarifying questions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
document_processor = DocumentProcessor()
vector_store = VectorStore()
clara_engine = ClaRAEngine(vector_store)


# ============ API Endpoints ============

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML interface"""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse(content="<h1>ClaRA RAG System</h1><p>API is running. Access /docs for API documentation.</p>")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy")


@app.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload and process a document

    Supported formats: PDF, DOCX, TXT, CSV, XLSX
    """

    try:
        # Save uploaded file
        file_path = os.path.join(settings.upload_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process document
        metadata, chunks = document_processor.process_document(
            file_path=file_path,
            filename=file.filename
        )

        # Add to vector store
        vector_store.add_documents(chunks)

        return UploadResponse(
            success=True,
            message=f"Document '{file.filename}' uploaded and processed successfully. {len(chunks)} chunks created.",
            document_metadata=metadata
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@app.post("/query")
async def query_documents(query_request: QueryRequest):
    """
    Query documents using ClaRA approach

    Returns either:
    - Clarification questions if query is ambiguous
    - Direct answer if query is clear or clarifications provided
    """

    try:
        clarification_response, answer_response = clara_engine.process_query(query_request)

        if clarification_response:
            return clarification_response
        else:
            return answer_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        stats = vector_store.get_collection_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a specific document"""
    try:
        vector_store.delete_document(document_id)
        return {"success": True, "message": f"Document {document_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.delete("/documents")
async def clear_all_documents():
    """Clear all documents from the system"""
    try:
        vector_store.clear_all()
        return {"success": True, "message": "All documents cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    conversation = clara_engine.get_conversation(conversation_id)
    if conversation:
        return conversation
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")


@app.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history"""
    clara_engine.clear_conversation(conversation_id)
    return {"success": True, "message": f"Conversation {conversation_id} cleared"}


# Mount static files if directory exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============ Main Entry Point ============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
