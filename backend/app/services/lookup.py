"""Book metadata lookup: Open Library + Google Books + Crossref (all free, no key needed)."""
import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Optional

import httpx

TIMEOUT = 15


def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def title_similarity(a: Optional[str], b: Optional[str]) -> float:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0
    # allow subtitle-included vs bare-title matches
    if na.startswith(nb) or nb.startswith(na):
        return 0.95
    ratio = SequenceMatcher(None, na, nb).ratio()
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    return (ratio + jaccard) / 2


def rank_candidates(candidates: List[dict], title: Optional[str], author: Optional[str] = None) -> List[dict]:
    """Sorts candidates by similarity to the wanted title/author; drops clear mismatches."""
    if not title:
        return candidates
    scored = []
    for c in candidates:
        title_score = title_similarity(c.get("title"), title)
        if title_score < 0.65:
            continue  # the author bonus must not rescue a wrong title
        bonus = 0.0
        if author and c.get("authors"):
            surname = _norm(author).split()[-1] if _norm(author) else ""
            if surname and any(surname in _norm(a) for a in c["authors"]):
                bonus = 0.15
        scored.append((title_score + bonus, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored]


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
    strict = _google_items({"q": q})
    if strict:
        return strict
    # loose retry: academic titles often differ slightly from the cover text
    return _google_items({"q": f"{title} {author or ''}".strip()})


def crossref_search(title: str, author: Optional[str] = None) -> List[dict]:
    """Crossref covers academic monographs and edited volumes well."""
    try:
        r = httpx.get("https://api.crossref.org/works", params={
            "query.bibliographic": f"{title} {author or ''}".strip(),
            "filter": "type:book,type:monograph,type:edited-book,type:reference-book",
            "rows": 5,
        }, timeout=TIMEOUT)
        items = r.json().get("message", {}).get("items", [])
    except Exception:
        return []
    out = []
    for it in items[:5]:
        date = it.get("published-print") or it.get("published") or {}
        year = (date.get("date-parts") or [[None]])[0][0]
        isbns = it.get("ISBN") or []
        isbns = [re.sub(r"[^0-9Xx]", "", i) for i in isbns]
        out.append(_candidate(
            "crossref",
            title=(it.get("title") or [None])[0],
            subtitle=(it.get("subtitle") or [None])[0],
            authors=[
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in it.get("author", []) + it.get("editor", [])
            ],
            publisher=it.get("publisher"),
            published_year=year,
            isbn=next((i for i in isbns if len(i) == 10), None),
            isbn13=next((i for i in isbns if len(i) == 13), None),
        ))
    return out


def by_isbn(isbn: str) -> List[dict]:
    isbn = normalize_isbn(isbn)
    if not isbn:
        return []
    return open_library_by_isbn(isbn) + google_books_by_isbn(isbn)


def by_title_author(title: str, author: Optional[str] = None) -> List[dict]:
    candidates = (
        open_library_search(title, author)
        + google_books_search(title, author)
        + crossref_search(title, author)
    )
    return rank_candidates(candidates, title, author)


def merge_prefill(ai: dict, candidates: List[dict], cover_url: Optional[str]) -> dict:
    """AI reading of the physical book wins; lookups fill in the gaps."""
    def from_candidates(field):
        # first candidate that actually knows the field
        for c in candidates:
            if c.get(field):
                return c[field]
        return None

    isbn_raw = normalize_isbn(ai.get("isbn"))
    prefill = {
        "title": ai.get("title") or from_candidates("title"),
        "subtitle": ai.get("subtitle") or from_candidates("subtitle"),
        "authors": [
            {"name": a.get("name"), "role": a.get("role") or "author"}
            for a in (ai.get("authors") or []) if a.get("name")
        ] or [{"name": n, "role": "author"} for n in (from_candidates("authors") or [])],
        "publisher": ai.get("publisher") or from_candidates("publisher"),
        "published_year": ai.get("published_year") or from_candidates("published_year"),
        "language": ai.get("language") or from_candidates("language"),
        "edition": ai.get("edition"),
        "isbn": (isbn_raw if isbn_raw and len(isbn_raw) == 10 else None) or from_candidates("isbn"),
        "isbn13": (isbn_raw if isbn_raw and len(isbn_raw) == 13 else None) or from_candidates("isbn13"),
        "pages": from_candidates("pages"),
        "description": from_candidates("description"),
        "cover_image_url": cover_url or from_candidates("cover_image_url"),
        "ai_confidence": ai.get("confidence"),
    }
    if ai.get("series"):
        prefill["notes"] = f"Series: {ai['series']}"
    return prefill


def apply_enrichment(prefill: dict, enriched: dict) -> dict:
    """Web-search enrichment fills only fields that are still empty."""
    for k in ("publisher", "published_year", "pages", "isbn", "isbn13",
              "edition", "description", "subtitle", "language"):
        if not prefill.get(k) and enriched.get(k):
            prefill[k] = enriched[k]
    return prefill
