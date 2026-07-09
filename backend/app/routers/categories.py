from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models import Category, Book
from app.schemas import CategoryBase, CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])

# Subject categories for a Mesoamerican studies research library
DEFAULT_CATEGORIES = [
    "Archaeology",
    "Anthropology & Ethnography",
    "Ethnohistory",
    "Maya Studies",
    "Aztec & Nahua Studies",
    "Other Mesoamerican Cultures",
    "Epigraphy & Writing Systems",
    "Codices & Manuscripts",
    "Linguistics",
    "Art & Iconography",
    "Religion, Myth & Cosmology",
    "Conquest & Colonial History",
    "Excavation & Field Reports",
    "Museum & Exhibition Catalogs",
    "Travel Accounts & Exploration",
    "Reference & Dictionaries",
    "Journals & Periodicals",
    "General & Other",
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
        raise HTTPException(422, "Category name is required")
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
        raise HTTPException(404, "Category not found")
    db.query(Book).filter(Book.category_id == category_id).update({"category_id": None})
    db.delete(cat)
    db.commit()
