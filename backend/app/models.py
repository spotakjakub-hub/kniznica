from sqlalchemy import (
    Column, String, Integer, Text, DateTime,
    ForeignKey, Float, Enum as SAEnum, JSON,
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum
import uuid


class Base(DeclarativeBase):
    pass


def gen_uuid():
    return str(uuid.uuid4())


class BookStatus(str, enum.Enum):
    available = "available"
    missing = "missing"
    damaged = "damaged"


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    books = relationship("Book", back_populates="category")


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    books = relationship("BookAuthor", back_populates="author")


class Book(Base):
    __tablename__ = "books"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String(500), nullable=False)
    subtitle = Column(String(500))
    # no unique constraint: a family library can hold duplicate copies
    isbn = Column(String(20), index=True)
    isbn13 = Column(String(20), index=True)
    publisher = Column(String(200))
    published_year = Column(Integer)
    language = Column(String(50), default="en")
    pages = Column(Integer)
    edition = Column(String(100))
    description = Column(Text)
    notes = Column(Text)
    cover_image_url = Column(String(1000))
    location = Column(String(200), index=True)
    condition = Column(String(50))
    status = Column(SAEnum(BookStatus), default=BookStatus.available)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    ai_confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="books")
    authors = relationship("BookAuthor", back_populates="book", cascade="all, delete-orphan")
    tags = relationship("BookTag", back_populates="book", cascade="all, delete-orphan")


class BookAuthor(Base):
    __tablename__ = "book_authors"
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    author_id = Column(Integer, ForeignKey("authors.id"), primary_key=True)
    role = Column(String(50), default="author", primary_key=True)  # author / editor / translator
    book = relationship("Book", back_populates="authors")
    author = relationship("Author", back_populates="books")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    books = relationship("BookTag", back_populates="tag")


class BookTag(Base):
    __tablename__ = "book_tags"
    book_id = Column(String, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
    book = relationship("Book", back_populates="tags")
    tag = relationship("Tag", back_populates="books")


class ScanJob(Base):
    """Batch-mode queue: one uploaded cover photo waiting for AI identification."""
    __tablename__ = "scan_jobs"
    id = Column(String, primary_key=True, default=gen_uuid)
    cover_url = Column(String(1000), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending / processing / done / failed
    location = Column(String(200))   # optional batch-wide shelf location
    result = Column(JSON)            # prefill dict once identified
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
