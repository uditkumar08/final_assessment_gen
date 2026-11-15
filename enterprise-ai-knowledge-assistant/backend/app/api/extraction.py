
from fastapi import APIRouter, HTTPException
from pathlib import Path

from backend.app.services.pdf_service import (
    extract_pdf_text,
    save_extracted_text
)

router=APIRouter()

BASE_DIR=Path(__file__).resolve().parents[3]
UPLOAD_DIR=BASE_DIR/"storage"/"uploads"


@router.post("/documents/{document_id}/extract")
def extract_document(document_id: str):

    pdf_path=UPLOAD_DIR/f"{document_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    try:

        extracted_data=extract_pdf_text(
            pdf_path,
            document_id
        )
        json_path = save_extracted_text(
            extracted_data,
            document_id
        )

        return {
            "message": "PDF extraction successful",
            "document_id": document_id,
            "total_pages": extracted_data["total_pages"],
            "processed_file": str(json_path)
        }

    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Unable to process this PDF"
        )
