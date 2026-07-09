from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import Category, Book
from app.schemas import CategoryBase, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])

DEFAULT_CATEGORIES = [
    "Beletria", "Poézia", "Detektívky", "Sci-fi a fantasy", "História",
    "Životopisy", "Cestopisy", "Náučná literatúra", "Umenie", "Náboženstvo",
    "Detské knihy", "Slovníky a encyklopédie", "Učebnice", "Iné",
]


def seed_categories(db: Session):
    if db.query(Category).count() == 0:
        for name in DEFAULT_CATEGORIES:
            db.add(Category(name=name))
        db.commit()


@router.get("/", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryBase, db: Session = Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(422, "Názov kategórie je povinný")
    existing = db.query(Category).filter(func.lower(Category.name) == name.lower()).first()
    if existing:
        return existing
    cat = Category(name=name, description=payload.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(404, "Kategória nenájdená")
    db.query(Book).filter(Book.category_id == category_id).update({"category_id": None})
    db.delete(cat)
    db.commit()
