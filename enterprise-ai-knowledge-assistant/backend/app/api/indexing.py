
from fastapi import APIRouter, HTTPException

from backend.app.services.indexing_service import index_document
from backend.app.services.embedding_service import generate_embedding
from backend.app.services.qdrant_service import search_similar_chunks

from pydantic import BaseModel, Field

router=APIRouter()


class SearchRequest(BaseModel):
    query:str=Field(min_length=1)
    top_k:int=Field(default=3,ge=1,le=10)


@router.post("/documents/{document_id}/index")
def index_uploaded_document(document_id: str):

    try:
        result=index_document(document_id)

        return{
            "message": "Document indexed successfully",
            **result
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Extracted document not found"
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document indexing failed"
        )


@router.post("/search")
def search_documents(request: SearchRequest):

    try:
        query_vector=generate_embedding(request.query)
        results=search_similar_chunks(
            query_vector,
            request.top_k
        )

        return{
            "query":request.query,
            "results": [
                {
                    "score": point.score,
                    "payload": point.payload
                }
                for point in results
            ]
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Document search failed"
        )
