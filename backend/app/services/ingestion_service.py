from pathlib import Path

from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session

from backend.app.models.paper import Paper
from backend.app.models.paper_chunk import PaperChunk
from backend.app.services.pdf_service import extract_pdf_text
from backend.app.services.chunking_service import chunk_pages


def ingest_paper(paper_id: int, db: Session) -> dict:
    paper = db.get(Paper, paper_id)

    if paper is None:
        raise ValueError("Paper not found")

    if not paper.pdf_path:
        raise ValueError("Paper has no attached PDF")

    pdf_path = Path(paper.pdf_path)

    if not pdf_path.is_file():
        raise ValueError("PDF file does not exist")

    extracted = extract_pdf_text(pdf_path)
    chunks = chunk_pages(extracted["pages"])

    if not chunks:
        raise ValueError("No extractable text found in PDF")

    # Replace existing chunks to avoid duplicates on re-ingestion.
    db.execute(
        delete(PaperChunk).where(PaperChunk.paper_id == paper_id)
    )

    db.add_all(
        [
            PaperChunk(
                paper_id=paper_id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                text=chunk["text"],
            )
            for chunk in chunks
        ]
    )

    db.commit()

    return {
        "paper_id": paper_id,
        "page_count": extracted["page_count"],
        "chunk_count": len(chunks),
        "status": "ingested",
    }