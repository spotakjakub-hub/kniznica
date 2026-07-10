from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func

from app.database import get_db
from app.models import Book, Loan

router = APIRouter(prefix="/api", tags=["loans"])


class LoanCreate(BaseModel):
    borrower: str = Field(min_length=1, max_length=200)
    note: Optional[str] = None


def loan_out(loan: Loan, with_book: bool = False) -> dict:
    out = {
        "id": loan.id,
        "book_id": loan.book_id,
        "borrower": loan.borrower,
        "note": loan.note,
        "loaned_at": loan.loaned_at.isoformat() if loan.loaned_at else None,
        "returned_at": loan.returned_at.isoformat() if loan.returned_at else None,
    }
    if with_book and loan.book:
        out["book"] = {"id": loan.book.id, "title": loan.book.title}
    return out


@router.post("/books/{book_id}/lend", status_code=201)
def lend_book(book_id: str, payload: LoanCreate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(404, "Book not found")
    active = db.query(Loan).filter(Loan.book_id == book_id, Loan.returned_at.is_(None)).first()
    if active:
        raise HTTPException(409, f"Already on loan to {active.borrower}")
    loan = Loan(book_id=book_id, borrower=payload.borrower.strip(), note=payload.note)
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return loan_out(loan)


@router.post("/loans/{loan_id}/return")
def return_loan(loan_id: str, db: Session = Depends(get_db)):
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise HTTPException(404, "Loan not found")
    if loan.returned_at is not None:
        raise HTTPException(409, "Already returned")
    loan.returned_at = func.now()
    db.commit()
    db.refresh(loan)
    return loan_out(loan)


@router.get("/loans/active")
def active_loans(db: Session = Depends(get_db)):
    loans = (
        db.query(Loan)
        .options(joinedload(Loan.book))
        .filter(Loan.returned_at.is_(None))
        .order_by(Loan.loaned_at.desc())
        .all()
    )
    return [loan_out(l, with_book=True) for l in loans]