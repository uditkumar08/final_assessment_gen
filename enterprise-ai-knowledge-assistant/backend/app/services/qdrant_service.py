
import uuid

from qdrant_client import QdrantClient, models

QDRANT_URL = "http://localhost:6335"
COLLECTION_NAME = "enterprise_documents"
VECTOR_SIZE = 384
client = QdrantClient(
    url=QDRANT_URL
)

def create_collection():
    collections = client.get_collections().collections
    collection_exists = any(
        collection.name == COLLECTION_NAME
        for collection in collections
    )
    if not collection_exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE
            )
        )
        print("Qdrant collection created.")
    else:
        print("Qdrant collection already exists.")

def store_chunks(chunks, embeddings):
    create_collection()
    points = []
    for chunk, embedding in zip(chunks, embeddings):
        document_id = chunk["document_id"]
        page_number = chunk["page_number"]
        chunk_index = chunk["chunk_index"]
        unique_key = (
            f"{document_id}:{page_number}:{chunk_index}"
        )
        point_id = str(
            uuid.uuid5(uuid.NAMESPACE_URL, unique_key)
        )
        points.append(
            models.PointStruct(
                id=point_id,

                vector=embedding.tolist(),
                payload={
                    "document_id": document_id,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "text": chunk["text"]
                }
            )
        )

    if points:
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True
        )
    return len(points)

def search_similar_chunks(
    query_embedding,
    document_id,
    top_k=5
):
    search_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(
                    value=document_id
                )
            )
        ]
    )

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        query_filter=search_filter,
        limit=top_k,
        with_payload=True
    )

    return response.points

def delete_document_chunks(document_id):

    client.delete(
        collection_name=COLLECTION_NAME,

        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(
                            value=document_id
                        )
                    )
                ]
            )
        ),

        wait=True
    )

    return True
