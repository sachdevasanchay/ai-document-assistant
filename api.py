
import os
from io import BytesIO

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pdf_extractor import extract_pdf_text
from text_chunker import split_text_into_chunks
from embedding_service import create_embeddings, search_similar_chunks
from ai_service import generate_answer
from db_service import (
    save_document,
    get_documents,
    get_document,
    test_connection
)


app = FastAPI(
    title="DocuMind API",
    description="AI-powered Document Assistant",
    version="1.0.0"
)

document_embeddings = {}


# Request model for chat API
class ChatRequest(BaseModel):
    document_name: str
    question: str


# CORS configuration
frontend_url = os.getenv("FRONTEND_URL", "")

allowed_origins = [
    "http://localhost:5173"
]

if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Home API
@app.get("/")
def home():
    return {
        "message": "DocuMind API is running"
    }


# Health check API
@app.get("/api/health")
def health_check():

    database_connected = test_connection()

    return {
        "status": "success",
        "api": "running",
        "database": "connected" if database_connected else "disconnected"
    }


# Get all uploaded documents
@app.get("/api/documents")
def documents_list():

    documents = get_documents()

    return [
        {
            "id": str(document["_id"]),
            "file_name": document["file_name"],
            "created_at": document["created_at"].isoformat()
            if document.get("created_at") else None
        }
        for document in documents
    ]


# Upload PDF document
@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    try:
        # Extract PDF text
        pages = extract_pdf_text(BytesIO(file_content))

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF"
            )

        # Split text into chunks
        chunks = split_text_into_chunks(pages)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Could not create document chunks"
            )

        # Create embeddings
        embeddings = create_embeddings(chunks)

        # Save document in MongoDB
        save_document(file.filename, chunks)

        # Store embeddings in memory
        document_embeddings[file.filename] = embeddings

        return {
            "status": "success",
            "message": "Document uploaded successfully",
            "document": {
                "file_name": file.filename,
                "total_pages": len(pages),
                "total_chunks": len(chunks)
            }
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# Chat with uploaded PDF
@app.post("/api/chat")
async def chat_with_document(request: ChatRequest):

    try:
        document_name = request.document_name
        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )

        # Get document from MongoDB
        document = get_document(document_name)

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        chunks = document.get("chunks", [])

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail="No document content found"
            )

        # Get embeddings
        if document_name not in document_embeddings:
            document_embeddings[document_name] = create_embeddings(chunks)

        embeddings = document_embeddings[document_name]

        # Find relevant chunks
        relevant_chunks = search_similar_chunks(
            question,
            chunks,
            embeddings,
            top_k=3,
            program_filter=None,
            min_similarity=0.25
        )

        if not relevant_chunks:
            return {
                "status": "success",
                "answer": "I couldn't find relevant information in this document.",
                "sources": []
            }

        # Generate AI answer
        answer = generate_answer(
            question,
            relevant_chunks
        )

        # Prepare source information
        sources = [
            {
                "page": chunk.get("page"),
                "text": chunk.get("text", "")
            }
            for chunk in relevant_chunks
        ]

        return {
            "status": "success",
            "answer": answer,
            "sources": sources
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
