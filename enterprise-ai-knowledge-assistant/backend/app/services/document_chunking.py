
import json
from pathlib import Path

from backend.app.services.chunk_service import split_text


def chunk_document(document_id:str):
    base_dir=Path(__file__).resolve().parents[3]
    processed_dir=base_dir / "storage" / "processed"
    input_path=processed_dir / f"{document_id}.json"

    if not input_path.exists():
        raise FileNotFoundError("Extracted document not found")

    with input_path.open("r", encoding="utf-8") as file:
        document_data=json.load(file)

    all_chunks=[]

    for page in document_data["pages"]:
        page_number=page["page_number"]
        page_text=page["text"]

        page_chunks=split_text(page_text, chunk_size=1000, chunk_overlap=150)

        for index, chunk_text in enumerate(page_chunks):
            chunk_data={
                "document_id": document_id,
                "page_number": page_number,
                "chunk_index": index,
                "text": chunk_text,
            }
            all_chunks.append(chunk_data)

    result={
        "document_id": document_id,
        "total_chunks": len(all_chunks),
        "chunks": all_chunks,
    }

    output_path=processed_dir/f"{document_id}_chunks.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    return result
