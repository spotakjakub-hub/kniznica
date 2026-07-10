from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.services import gemini, lookup, storage

router = APIRouter(prefix="/api/scan", tags=["scan"])

MAX_IMAGE_BYTES = 15 * 1024 * 1024


async def _read_image(f: UploadFile) -> bytes:
    data = await f.read()
    if not data:
        raise HTTPException(422, "Empty image file")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image too large (max 15 MB)")
    return data


@router.post("/identify")
async def identify_book(
    cover: UploadFile = File(..., description="Cover photo"),
    extra: Optional[UploadFile] = File(None, description="Optional title/imprint page photo"),
):
    """Photo(s) -> Gemini identification -> Open Library/Google Books enrichment."""
    images = [(await _read_image(cover), cover.content_type)]
    if extra is not None:
        images.append((await _read_image(extra), extra.content_type))

    try:
        ai = gemini.identify(images)
    except gemini.GeminiError as e:
        raise HTTPException(502, f"AI identification failed: {e}")

    # keep the user's own photo as the cover
    try:
        cover_url = storage.upload_cover(images[0][0], images[0][1])
    except storage.StorageError:
        cover_url = None  # cover upload must not block identification

    candidates = []
    if ai.get("isbn"):
        candidates = lookup.by_isbn(ai["isbn"])
    if not candidates and ai.get("title"):
        first_author = next((a.get("name") for a in ai.get("authors") or []), None)
        candidates = lookup.by_title_author(ai["title"], first_author)

    prefill = lookup.merge_prefill(ai, candidates, cover_url)

    # best-effort web-search enrichment for whatever is still missing
    # (no-op on the free Gemini tier, activates automatically with billing)
    if any(not prefill.get(k) for k in ("publisher", "published_year", "pages", "isbn13")):
        enriched = gemini.web_enrich(ai)
        if enriched:
            prefill = lookup.apply_enrichment(prefill, enriched)

    return {"prefill": prefill, "ai": ai, "candidates": candidates}


@router.get("/isbn/{isbn}")
def lookup_isbn(isbn: str):
    normalized = lookup.normalize_isbn(isbn)
    if not normalized:
        raise HTTPException(422, "Invalid ISBN (expected 10 or 13 digits)")
    candidates = lookup.by_isbn(normalized)
    if not candidates:
        raise HTTPException(404, "No book found for this ISBN")
    prefill = lookup.merge_prefill({}, candidates, None)
    if len(normalized) == 13:
        prefill["isbn13"] = prefill.get("isbn13") or normalized
    else:
        prefill["isbn"] = prefill.get("isbn") or normalized
    return {"prefill": prefill, "candidates": candidates}


@router.get("/search")
def search_books(title: str = Query(..., min_length=2), author: Optional[str] = None):
    candidates = lookup.by_title_author(title, author)
    return {"candidates": candidates}
