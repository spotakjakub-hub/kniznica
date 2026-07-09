from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models import BookStatus


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryOut(CategoryBase):
    id: int
    model_config = {"from_attributes": True}


class AuthorIn(BaseModel):
    name: str
    role: str = "author"  # author / editor / translator


class AuthorOut(AuthorIn):
    id: int


class TagOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class BookBase(BaseModel):
    title: str = Field(min_length=1)
    subtitle: Optional[str] = None
    isbn: Optional[str] = None
    isbn13: Optional[str] = None
    publisher: Optional[str] = None
    published_year: Optional[int] = None
    language: Optional[str] = "sk"
    pages: Optional[int] = None
    edition: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    cover_image_url: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    status: BookStatus = BookStatus.available
    category_id: Optional[int] = None
    ai_confidence: Optional[float] = None


class BookCreate(BookBase):
    authors: List[AuthorIn] = []
    tag_names: List[str] = []


class BookUpdate(BookCreate):
    pass


class BookOut(BookBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    category: Optional[CategoryOut] = None
    authors: List[AuthorOut] = []
    tags: List[TagOut] = []


class BookListItem(BaseModel):
    id: str
    title: str
    subtitle: Optional[str] = None
    cover_image_url: Optional[str] = None
    published_year: Optional[int] = None
    language: Optional[str] = None
    location: Optional[str] = None
    status: BookStatus
    authors: List[AuthorOut] = []
    category: Optional[CategoryOut] = None


class BookListPage(BaseModel):
    items: List[BookListItem]
    total: int


class StatsOut(BaseModel):
    total_books: int
    total_authors: int
    total_categories: int
    by_status: dict
    by_language: dict
    by_location: dict
