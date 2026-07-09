"""Book metadata lookup: Open Library + Google Books (both free, no key needed)."""
import re
from typing import List, Optional

import httpx

TIMEOUT = 15


def normalize_isbn(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    digits = re.sub(r"[^0-9Xx]", "", raw)
    return digits.upper() if len(digits) in (10, 13) else None


def _candidate(source, title=None, subtitle=None, authors=None, publisher=None,
               published_year=None, isbn=None, isbn13=None, pages=None,
               description=None, cover_image_url=None, language=None):
    return {
        "source": source, "title": title, "subtitle": subtitle,
        "authors": authors or [], "publisher": publisher,
        "published_year": published_year, "isbn": isbn, "isbn13": isbn13,
        "pages": pages, "description": description,
        "cover_image_url": cover_image_url, "language": language,
    }


def _year(value) -> Optional[int]:
    if not value:
        return None
    m = re.search(r"\d{4}", str(value))
    return int(m.group()) if m else None


def open_library_by_isbn(isbn: str) -> List[dict]:
    try:
        r = httpx.get(
            "https://openlibrary.org/api/books",
            params={"bibkeys": f"ISBN:{isbn}", "jscmd": "data", "format": "json"},
            timeout=TIMEOUT,
        )
        data = r.json().get(f"ISBN:{isbn}")
    except Exception:
        return []
    if not data:
        return []
    ids = data.get("identifiers", {})
    return [_candidate(
        "openlibrary",
        title=data.get("title"),
        subtitle=data.get("subtitle"),
        authors=[a["name"] for a in data.get("authors", [])],
        publisher=(data.get("publishers") or [{}])[0].get("name"),
        published_year=_year(data.get("publish_date")),
        isbn=(ids.get("isbn_10") or [None])[0],
        isbn13=(ids.get("isbn_13") or [None])[0],
        pages=data.get("number_of_pages"),
        cover_image_url=(data.get("cover") or {}).get("large"),
    )]


def open_library_search(title: str, author: Optional[str] = None) -> List[dict]:
    try:
        params = {"title": title, "limit": 5}
        if author:
            params["author"] = author
        r = httpx.get("https://openlibrary.org/search.json", params=params, timeout=TIMEOUT)
        docs = r.json().get("docs", [])
    except Exception:
        return []
    out = []
    for d in docs[:5]:
        isbns = d.get("isbn", [])
        out.append(_candidate(
            "openlibrary",
            title=d.get("title"),
            subtitle=d.get("subtitle"),
            authors=d.get("author_name", []),
            publisher=(d.get("publisher") or [None])[0],
            published_year=d.get("first_publish_year"),
            isbn=next((i for i in isbns if len(i) == 10), None),
            isbn13=next((i for i in isbns if len(i) == 13), None),
            pages=d.get("number_of_pages_median"),
            cover_image_url=(
                f"https://covers.openlibrary.org/b/id/{d['cover_i']}-L.jpg"
                if d.get("cover_i") else None
            ),
        ))
    return out


def _google_items(params) -> List[dict]:
    try:
        r = httpx.get("https://www.googleapis.com/books/v1/volumes",
                      params={**params, "maxResults": 5}, timeout=TIMEOUT)
        items = r.json().get("items", [])
    except Exception:
        return []
    out = []
    for item in items[:5]:
        v = item.get("volumeInfo", {})
        ids = {i.get("type"): i.get("identifier") for i in v.get("industryIdentifiers", [])}
        out.append(_candidate(
            "googlebooks",
            title=v.get("title"),
            subtitle=v.get("subtitle"),
            authors=v.get("authors", []),
            publisher=v.get("publisher"),
            published_year=_year(v.get("publishedDate")),
            isbn=ids.get("ISBN_10"),
            isbn13=ids.get("ISBN_13"),
            pages=v.get("pageCount"),
            description=v.get("description"),
            cover_image_url=(v.get("imageLinks") or {}).get("thumbnail"),
            language=v.get("language"),
        ))
    return out


def google_books_by_isbn(isbn: str) -> List[dict]:
    return _google_items({"q": f"isbn:{isbn}"})


def google_books_search(title: str, author: Optional[str] = None) -> List[dict]:
    q = f'intitle:"{title}"'
    if author:
        q += f' inauthor:"{author}"'
    return _google_items({"q": q})


def by_isbn(isbn: str) -> List[dict]:
    isbn = normalize_isbn(isbn)
    if not isbn:
        return []
    return open_library_by_isbn(isbn) + google_books_by_isbn(isbn)


def by_title_author(title: str, author: Optional[str] = None) -> List[dict]:
    return open_library_search(title, author) + google_books_search(title, author)


def merge_prefill(ai: dict, candidates: List[dict], cover_url: Optional[str]) -> dict:
    """AI reading of the physical book wins; lookups fill in the gaps."""
    best = candidates[0] if candidates else {}
    isbn_raw = normalize_isbn(ai.get("isbn"))
    prefill = {
        "title": ai.get("title") or best.get("title"),
        "subtitle": ai.get("subtitle") or best.get("subtitle"),
        "authors": [
            {"name": a.get("name"), "role": a.get("role") or "author"}
            for a in (ai.get("authors") or []) if a.get("name")
        ] or [{"name": n, "role": "author"} for n in best.get("authors", [])],
        "publisher": ai.get("publisher") or best.get("publisher"),
        "published_year": ai.get("published_year") or best.get("published_year"),
        "language": ai.get("language") or best.get("language"),
        "edition": ai.get("edition"),
        "isbn": (isbn_raw if isbn_raw and len(isbn_raw) == 10 else None) or best.get("isbn"),
        "isbn13": (isbn_raw if isbn_raw and len(isbn_raw) == 13 else None) or best.get("isbn13"),
        "pages": best.get("pages"),
        "description": best.get("description"),
        "cover_image_url": cover_url or best.get("cover_image_url"),
        "ai_confidence": ai.get("confidence"),
    }
    if ai.get("series"):
        prefill["notes"] = f"Series: {ai['series']}"
    return prefill
