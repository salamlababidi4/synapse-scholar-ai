from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.app.models.paper import Paper  # noqa: F401
from backend.app.models.paper_chunk import PaperChunk
from backend.app.services.embedding_service import get_embedding_model


def index_paper_embeddings(paper_id: int, db: Session) -> dict:
    chunks = db.scalars(
        select(PaperChunk)
        .where(PaperChunk.paper_id == paper_id)
        .order_by(PaperChunk.chunk_index)
    ).all()

    if not chunks:
        raise ValueError("No chunks found for this paper")

    model = get_embedding_model()

    texts = [chunk.text for chunk in chunks]

    # Generate embeddings in batches to reduce memory usage.
    embeddings = model.encode(
        texts,
        batch_size=8,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding.tolist()

    db.commit()

    indexed_count = db.scalar(
        select(func.count(PaperChunk.id)).where(
            PaperChunk.paper_id == paper_id,
            PaperChunk.embedding.is_not(None),
        )
    )

    return {
        "paper_id": paper_id,
        "total_chunks": len(chunks),
        "indexed_chunks": indexed_count,
        "status": "indexed",
    }