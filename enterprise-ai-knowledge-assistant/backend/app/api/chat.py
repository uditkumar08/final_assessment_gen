
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.rag_service import answer_question


router = APIRouter()


class ChatRequest(BaseModel):

    document_id: str = Field(
        min_length=1,
        description="ID of the uploaded document"
    )

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Question about the uploaded document"
    )


@router.post("/chat/query")
def chat_query(request: ChatRequest):

    question = request.question.strip()
    document_id = request.document_id.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    if not document_id:
        raise HTTPException(
            status_code=400,
            detail="Document ID is required."
        )

    try:

        result = answer_question(
            question=question,
            document_id=document_id
        )

        return {
            "success": True,
            "question": question,
            "document_id": document_id,
            "answer": result["answer"],
            "sources": result["sources"]
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        print("Chat error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer."
        )
