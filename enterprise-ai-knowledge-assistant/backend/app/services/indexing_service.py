
from backend.app.services.document_chunking import chunk_document

from backend.app.services.embedding_service import (generate_embeddings)
from backend.app.services.qdrant_service import (
    create_collection,
    store_chunks
)


def index_document(document_id: str):

    chunk_data=chunk_document(document_id)
    chunks=chunk_data["chunks"]

    if not chunks:
        raise ValueError("No chunks found")
    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings=generate_embeddings(texts)
    create_collection()
    stored_count = store_chunks(
        chunks,
        embeddings
    )

    return {
        "document_id": document_id,
        "total_chunks": len(chunks),
        "stored_points": stored_count
    }
