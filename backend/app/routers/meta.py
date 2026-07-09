from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import Book, Author, Category
from app.schemas import StatsOut

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/locations", response_model=List[str])
def list_locations(db: Session = Depends(get_db)):
    rows = (
        db.query(Book.location)
        .filter(Book.location.isnot(None), Book.location != "")
        .distinct().order_by(Book.location).all()
    )
    return [r[0] for r in rows]


@router.get("/languages", response_model=List[str])
def list_languages(db: Session = Depends(get_db)):
    rows = (
        db.query(Book.language)
        .filter(Book.language.isnot(None), Book.language != "")
        .distinct().order_by(Book.language).all()
    )
    return [r[0] for r in rows]


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    def grouped(col):
        rows = (
            db.query(col, func.count(Book.id))
            .filter(col.isnot(None)).group_by(col).all()
        )
        return {str(getattr(k, "value", k)): v for k, v in rows}

    return {
        "total_books": db.query(func.count(Book.id)).scalar() or 0,
        "total_authors": db.query(func.count(Author.id)).scalar() or 0,
        "total_categories": db.query(func.count(Category.id)).scalar() or 0,
        "by_status": grouped(Book.status),
        "by_language": grouped(Book.language),
        "by_location": grouped(Book.location),
    }
