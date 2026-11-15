
import pymupdf
import json
from pathlib import Path

def extract_pdf_text(pdf_path: Path, document_id: str):
    doc = pymupdf.open(pdf_path)
    try:
        extracted_pages = []
        for page_number, page in enumerate(doc):
            text = page.get_text("text")
            page_data = {
                "page_number":page_number+1,
                "text":text
            }

            extracted_pages.append(page_data)
        result = {
            "document_id":document_id,
            "total_pages":len(doc),
            "pages":extracted_pages
        }

        return result

    finally:
        doc.close()


def save_extracted_text(data: dict, document_id: str):

    base_dir = Path(__file__).resolve().parents[3]
    processed_dir = base_dir / "storage" / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)
    json_path = processed_dir / f"{document_id}.json"
    with json_path.open("w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    return json_path
