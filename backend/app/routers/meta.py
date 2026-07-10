from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import Book, Author, BookAuthor, Category, Loan
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

    by_category = dict(
        db.query(Category.name, func.count(Book.id))
        .join(Book, Book.category_id == Category.id)
        .group_by(Category.name).all()
    )
    top_authors = [
        {"name": name, "count": count}
        for name, count in (
            db.query(Author.name, func.count(BookAuthor.book_id))
            .join(BookAuthor, BookAuthor.author_id == Author.id)
            .group_by(Author.name)
            .order_by(func.count(BookAuthor.book_id).desc(), Author.name)
            .limit(10).all()
        )
    ]
    by_decade = {}
    for year, count in (
        db.query(Book.published_year, func.count(Book.id))
        .filter(Book.published_year.isnot(None))
        .group_by(Book.published_year).all()
    ):
        decade = f"{(year // 10) * 10}s"
        by_decade[decade] = by_decade.get(decade, 0) + count

    return {
        "total_books": db.query(func.count(Book.id)).scalar() or 0,
        "total_authors": db.query(func.count(func.distinct(BookAuthor.author_id))).scalar() or 0,
        "total_categories": db.query(func.count(Category.id)).scalar() or 0,
        "by_status": grouped(Book.status),
        "by_language": grouped(Book.language),
        "by_location": grouped(Book.location),
        "by_category": by_category,
        "top_authors": top_authors,
        "by_decade": dict(sorted(by_decade.items())),
        "loans_active": db.query(func.count(Loan.id)).filter(Loan.returned_at.is_(None)).scalar() or 0,
    }
