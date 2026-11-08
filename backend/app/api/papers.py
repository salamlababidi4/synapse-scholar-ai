from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.paper import Paper
from backend.app.schemas.paper import PaperCreate, PaperResponse

from pathlib import Path
from uuid import uuid4

import pymupdf
from fastapi import File, UploadFile

from backend.app.services.pdf_service import extract_pdf_text

router = APIRouter(prefix="/papers", tags=["Papers"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_paper(paper: PaperCreate, db: DbSession):
    new_paper = Paper(**paper.model_dump())

    db.add(new_paper)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A paper with this DOI already exists",
        )

    db.refresh(new_paper)
    return new_paper


@router.get("/", response_model=list[PaperResponse])
def list_papers(db: DbSession):
    return db.scalars(
        select(Paper).order_by(Paper.id.desc()).limit(100)
    ).all()

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB
UPLOAD_DIR = Path(__file__).resolve().parents[3] / "data" / "uploads"


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_paper(file: UploadFile = File(...)):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed",
        )

    # Read at most 20 MB + 1 byte to detect oversized files.
    content = file.file.read(MAX_PDF_SIZE + 1)

    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF exceeds the 20 MB limit",
        )

    # Check PDF file signature.
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file",
        )

    # Verify that PyMuPDF can actually open the PDF.
    try:
        with pymupdf.open(stream=content, filetype="pdf") as document:
            if document.page_count == 0 or document.needs_pass:
                raise ValueError("Empty or password-protected PDF")
    except (pymupdf.FileDataError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot process PDF: {exc}",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}.pdf"
    stored_path = UPLOAD_DIR / stored_filename

    stored_path.write_bytes(content)

    try:
        extracted = extract_pdf_text(stored_path)
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail="PDF text extraction failed",
        )

    return {
        "filename": file.filename,
        "stored_filename": stored_filename,
        "page_count": extracted["page_count"],
        "pages": extracted["pages"],
    }

@router.post("/{paper_id}/attach-pdf")
def attach_pdf_to_paper(
    paper_id: int,
    db: DbSession,
    stored_filename: str,
):
    paper = db.get(Paper, paper_id)

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail="Paper not found",
        )

    # Accept only UUID-generated PDF filenames.
    from uuid import UUID

    try:
        UUID(stored_filename.removesuffix(".pdf"))
        if not stored_filename.endswith(".pdf"):
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid stored filename",
        )

    pdf_path = UPLOAD_DIR / stored_filename

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Uploaded PDF not found",
        )

    paper.pdf_path = str(pdf_path)
    db.commit()
    db.refresh(paper)

    return {
        "message": "PDF attached successfully",
        "paper_id": paper.id,
        "pdf_path": paper.pdf_path,
    }

@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: DbSession):
    paper = db.get(Paper, paper_id)

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail="Paper not found",
        )

    return paper