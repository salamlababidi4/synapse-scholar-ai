import re


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Invalid chunk size or overlap")

    chunks = []
    chunk_index = 0

    for page in pages:
        text = page["text"]

        # Normalize whitespace while preserving readable sentences.
        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # Prefer ending chunks at sentence boundaries.
            if end < len(text):
                boundary = text.rfind(". ", start + chunk_size // 2, end)
                if boundary != -1:
                    end = boundary + 1

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "chunk_index": chunk_index,
                    "page_number": page["page_number"],
                    "text": chunk_text,
                })
                chunk_index += 1

            if end >= len(text):
                break

            start = max(start + 1, end - overlap)

    return chunks