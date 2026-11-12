from io import BytesIO

from fastapi import UploadFile, File, HTTPException

from pdf_extractor import extract_pdf_text
from text_chunker import split_text_into_chunks
from embedding_service import create_embeddings
from db_service import save_document
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db_service import get_documents, test_connection

app = FastAPI(
    title="DocuMind API",
    description="AI-powered Document Assistant",
    version="1.0.0"
)

document_embeddings = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def home():
    return {
        "message": "DocuMind API is running"
    }


@app.get("/api/health")
def health_check():
    database_connected = test_connection()

    return {
        "status": "success",
        "api": "running",
        "database": "connected" if database_connected else "disconnected"
    }


@app.get("/api/documents")
def documents_list():
    documents = get_documents()

    return [
        {
            "id": str(document["_id"]),
            "file_name": document["file_name"],
            "created_at": (
                document["created_at"].isoformat()
                if document.get("created_at")
                else None
            )
        }
        for document in documents
    ]
    

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
            detail="Uploaded PDF is empty"
        )

    try:
        pages = extract_pdf_text(BytesIO(file_content))

        if not pages:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from PDF"
            )

        chunks = split_text_into_chunks(pages)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No readable content found in PDF"
            )

        embeddings = create_embeddings(chunks)

        save_document(file.filename, chunks)

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
