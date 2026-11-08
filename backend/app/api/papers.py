from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.paper import Paper
from backend.app.schemas.paper import PaperCreate, PaperResponse

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


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, db: DbSession):
    paper = db.get(Paper, paper_id)

    if paper is None:
        raise HTTPException(
            status_code=404,
            detail="Paper not found",
        )

    return paper