import csv
import io
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Book, BookAuthor, BookTag

router = APIRouter(prefix="/api/export", tags=["export"])

COLUMNS = [
    "title", "subtitle", "authors", "publisher", "published_year", "language",
    "pages", "edition", "isbn", "isbn13", "category", "tags", "location",
    "condition", "status", "description", "notes", "cover_image_url", "created_at",
]


@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):
    books = (
        db.query(Book)
        .options(
            joinedload(Book.authors).joinedload(BookAuthor.author),
            joinedload(Book.tags).joinedload(BookTag.tag),
            joinedload(Book.category),
        )
        .order_by(Book.title)
        .all()
    )
    buf = io.StringIO()
    buf.write("\ufeff")  # UTF-8 BOM so Excel opens diacritics correctly
    writer = csv.writer(buf, delimiter=";")  # ; plays nicer with European Excel
    writer.writerow(COLUMNS)
    for b in books:
        authors = "; ".join(
            ba.author.name + (f" ({ba.role})" if ba.role != "author" else "")
            for ba in b.authors
        )
        writer.writerow([
            b.title, b.subtitle or "", authors, b.publisher or "",
            b.published_year or "", b.language or "", b.pages or "",
            b.edition or "", b.isbn or "", b.isbn13 or "",
            b.category.name if b.category else "",
            ", ".join(bt.tag.name for bt in b.tags),
            b.location or "", b.condition or "",
            b.status.value if b.status else "",
            b.description or "", b.notes or "", b.cover_image_url or "",
            b.created_at.date().isoformat() if b.created_at else "",
        ])
    buf.seek(0)
    filename = f"library-export-{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )