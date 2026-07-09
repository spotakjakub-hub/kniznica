from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import Optional

import app.database as database
from app.database import get_db
from app.models import Book, Author, BookAuthor, Tag, BookTag
from app.schemas import BookCreate, BookUpdate, BookOut, BookListPage

router = APIRouter(prefix="/api/books", tags=["books"])

SORTS = {
    "title": Book.title,
    "created_at": Book.created_at,
    "published_year": Book.published_year,
    "location": Book.location,
}


def _fold(col):
    """Case- and diacritics-insensitive expression (unaccent when available)."""
    lowered = func.lower(col)
    return func.unaccent(lowered) if database.HAS_UNACCENT else lowered


def _sync_authors(db: Session, book: Book, authors):
    book.authors.clear()
    db.flush()
    seen = set()
    for a in authors:
        name = a.name.strip()
        role = (a.role or "author").strip() or "author"
        if not name or (name.lower(), role) in seen:
            continue
        seen.add((name.lower(), role))
        author = db.query(Author).filter(func.lower(Author.name) == name.lower()).first()
        if not author:
            author = Author(name=name)
            db.add(author)
            db.flush()
        db.add(BookAuthor(book_id=book.id, author_id=author.id, role=role))


def _sync_tags(db: Session, book: Book, tag_names):
    book.tags.clear()
    db.flush()
    seen = set()
    for name in tag_names:
        name = name.strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        db.add(BookTag(book_id=book.id, tag_id=tag.id))


def _book_out(book: Book) -> dict:
    return {
        **{c.name: getattr(book, c.name) for c in Book.__table__.columns},
        "authors": [
            {"id": ba.author.id, "name": ba.author.name, "role": ba.role}
            for ba in book.authors
        ],
        "tags": [{"id": bt.tag.id, "name": bt.tag.name} for bt in book.tags],
        "category": (
            {"id": book.category.id, "name": book.category.name, "description": book.category.description}
            if book.category else None
        ),
    }


@router.get("/", response_model=BookListPage)
def list_books(
    q: Optional[str] = Query(None, description="Fulltext: názov, autor, vydavateľ, ISBN"),
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    language: Optional[str] = None,
    location: Optional[str] = None,
    sort: str = "title",
    order: str = "asc",
    skip: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Book)
    if q:
        pattern = f"%{q.strip()}%"
        query = (
            query.outerjoin(Book.authors).outerjoin(BookAuthor.author)
            .filter(or_(
                _fold(Book.title).like(_fold(pattern)),
                _fold(Book.subtitle).like(_fold(pattern)),
                _fold(Book.publisher).like(_fold(pattern)),
                _fold(Author.name).like(_fold(pattern)),
                Book.isbn.ilike(pattern),
                Book.isbn13.ilike(pattern),
            ))
            .distinct()
        )
    if category_id:
        query = query.filter(Book.category_id == category_id)
    if status:
        query = query.filter(Book.status == status)
    if language:
        query = query.filter(Book.language == language)
    if location:
        query = query.filter(Book.location == location)

    total = query.count()

    sort_col = SORTS.get(sort, Book.title)
    sort_expr = sort_col.desc() if order == "desc" else sort_col.asc()
    books = (
        query.options(
            joinedload(Book.authors).joinedload(BookAuthor.author),
            joinedload(Book.category),
        )
        .order_by(sort_expr, Book.id)
        .offset(skip).limit(limit).all()
    )
    return {"items": [_book_out(b) for b in books], "total": total}


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: str, db: Session = Depends(get_db)):
    book = (
        db.query(Book)
        .options(
            joinedload(Book.authors).joinedload(BookAuthor.author),
            joinedload(Book.tags).joinedload(BookTag.tag),
            joinedload(Book.category),
        )
        .filter(Book.id == book_id).first()
    )
    if not book:
        raise HTTPException(404, "Kniha nenájdená")
    return _book_out(book)


@router.post("/", response_model=BookOut, status_code=201)
def create_book(payload: BookCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"authors", "tag_names"})
    book = Book(**data)
    db.add(book)
    db.flush()
    _sync_authors(db, book, payload.authors)
    _sync_tags(db, book, payload.tag_names)
    db.commit()
    return get_book(book.id, db)


@router.put("/{book_id}", response_model=BookOut)
def update_book(book_id: str, payload: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(404, "Kniha nenájdená")
    for k, v in payload.model_dump(exclude={"authors", "tag_names"}).items():
        setattr(book, k, v)
    _sync_authors(db, book, payload.authors)
    _sync_tags(db, book, payload.tag_names)
    db.commit()
    return get_book(book_id, db)


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: str, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(404, "Kniha nenájdená")
    db.delete(book)
    db.commit()
