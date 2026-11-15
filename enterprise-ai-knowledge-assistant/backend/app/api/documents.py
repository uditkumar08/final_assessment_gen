from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter,File,HTTPException,UploadFile

from backend.app.services.pdf_service import(
    extract_pdf_text,
    save_extracted_text
)
from backend.app.services.indexing_service import index_document


router=APIRouter()

# Project root
PROJECT_ROOT=Path(__file__).resolve().parents[3]

UPLOAD_DIR=PROJECT_ROOT/"storage"/"uploads"

MAX_FILE_SIZE=10*1024*1024


@router.post("/documents/upload-and-index")
async def upload_and_index_document(
    file: UploadFile = File(...)
):
    """
    Complete document ingestion pipeline:
    1. Validate PDF
    2. Save PDF
    3. Extract text
    4. Create chunks
    5. Generate embeddings
    6. Store vectors in Qdrant
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required."
        )

    if Path(file.filename).suffix.lower()!=".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    content=await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content)>MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF exceeds the 10 MB size limit."
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file."
        )


    document_id = uuid4().hex

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    pdf_path=UPLOAD_DIR/f"{document_id}.pdf"

    try:
        pdf_path.write_bytes(content)

        extraction_result=extract_pdf_text(
            pdf_path=pdf_path,
            document_id=document_id
        )

        if not extraction_result.get("pages"):
            raise ValueError(
                "No pages could be extracted from this PDF."
            )

        has_text = any(
            page.get("text", "").strip()
            for page in extraction_result["pages"]
        )

        if not has_text:
            raise ValueError(
                "No readable text found. This PDF may require OCR."
            )

        save_extracted_text(
            extraction_result,
            document_id
        )
        indexing_result = index_document(document_id)

        return {
            "success": True,
            "message": "Document uploaded and indexed successfully.",
            "document_id": document_id,
            "filename": Path(file.filename).name,
            "total_pages": extraction_result.get("total_pages"),
            "total_chunks": indexing_result.get("total_chunks"),
            "stored_points": indexing_result.get("stored_points"),
            "status": "ready"
        }

    except Exception as error:

        if pdf_path.exists():
            pdf_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(error)}"
        )

    finally:
        await file.close()
