
from fastapi import APIRouter, HTTPException

from backend.app.services.document_chunking import chunk_document

router = APIRouter()


@router.post("/documents/{document_id}/chunk")
def create_document_chunks(document_id: str):

    try:

        result = chunk_document(document_id)

        return {
            "message": "Document chunking successful",
            "document_id": document_id,
            "total_chunks": result["total_chunks"]
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Extracted document not found. Extract PDF first."
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document chunking failed"
        )
