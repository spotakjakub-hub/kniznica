import os
import base64
import json
from typing import List, Optional, Tuple

import httpx

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Free-tier models come and go / get overloaded, so we walk a fallback chain.
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite", "gemini-2.0-flash"]

PROMPT = """You are cataloguing books for a research library on Mesoamerica \
(archaeology, anthropology, ethnohistory, Maya and Aztec studies). \
The image(s) show one book: its cover, and possibly a title page or imprint page.

Extract the bibliographic metadata exactly as printed on the book. \
Academic publishers (Thames & Hudson, University of Texas Press, Cambridge UP, \
Fondo de Cultura Económica, INAH, Dumbarton Oaks...), edited volumes and \
monograph series are common. Books may be in English, Spanish, German or other languages.

Rules:
- Use null for anything not actually visible or readable; never invent values.
- authors: people printed on the book, with role "author", "editor" (eds./coordinador), \
"translator" or "illustrator".
- language: the language of the book's text, as ISO 639-1 code (en, es, de, fr...); \
if unusual, the English name.
- published_year: integer year if printed (title page/imprint), else null.
- confidence: your overall certainty (0-1) that the identification is correct.
"""

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING", "nullable": True},
        "subtitle": {"type": "STRING", "nullable": True},
        "authors": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "role": {"type": "STRING"},
                },
                "required": ["name"],
            },
        },
        "publisher": {"type": "STRING", "nullable": True},
        "published_year": {"type": "INTEGER", "nullable": True},
        "language": {"type": "STRING", "nullable": True},
        "edition": {"type": "STRING", "nullable": True},
        "isbn": {"type": "STRING", "nullable": True},
        "series": {"type": "STRING", "nullable": True},
        "confidence": {"type": "NUMBER"},
    },
}


class GeminiError(Exception):
    pass


def _models() -> List[str]:
    preferred = os.environ.get("GEMINI_MODEL")
    chain = list(FALLBACK_MODELS)
    if preferred:
        chain = [preferred] + [m for m in chain if m != preferred]
    return chain


def identify(images: List[Tuple[bytes, str]]) -> dict:
    """images: list of (bytes, mime_type). Returns parsed metadata dict."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not configured")

    parts = [{"text": PROMPT}]
    for data, mime in images:
        parts.append({"inline_data": {
            "mime_type": mime or "image/jpeg",
            "data": base64.b64encode(data).decode(),
        }})

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }

    last_err = None
    for model in _models():
        payload = json.loads(json.dumps(body))
        if "2.0" not in model:
            payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
        try:
            r = httpx.post(
                f"{API_BASE}/{model}:generateContent",
                headers={"x-goog-api-key": api_key},
                json=payload,
                timeout=90,
            )
        except httpx.HTTPError as e:
            last_err = f"{model}: {e}"
            continue
        if r.status_code in (404, 429, 503):
            last_err = f"{model}: HTTP {r.status_code}"
            continue
        if r.status_code != 200:
            raise GeminiError(f"Gemini {model}: HTTP {r.status_code}: {r.text[:300]}")
        try:
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text)
            result["_model"] = model
            return result
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            last_err = f"{model}: bad response ({e})"
            continue

    raise GeminiError(f"All Gemini models failed; last error: {last_err}")


ENRICH_PROMPT = """Search the web for the exact bibliographic record of this book \
(publisher catalog pages, WorldCat, Google Books, library catalogs):

{book}

Return ONLY a JSON object (no markdown, no commentary) with these keys, using null \
when the web sources don't confirm a value — never guess: \
publisher, published_year (integer), pages (integer), isbn (10 chars), \
isbn13 (13 digits), edition, subtitle, language (ISO 639-1), \
description (1-2 neutral sentences about the book)."""

# flips to False after the first quota rejection so we don't retry every request
_grounding_available = True


def web_enrich(meta: dict) -> dict:
    """Optional Google-Search-grounded enrichment. Returns {} whenever grounding
    is unavailable (free tier) or anything fails — callers treat it as best-effort."""
    global _grounding_available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not _grounding_available or not meta.get("title"):
        return {}

    desc = f"Title: {meta['title']}"
    authors = ", ".join(a.get("name", "") for a in meta.get("authors") or [])
    if authors:
        desc += f"\nAuthors: {authors}"
    for label, key in (("Publisher", "publisher"), ("Year", "published_year"), ("Edition", "edition")):
        if meta.get(key):
            desc += f"\n{label}: {meta[key]}"

    body = {
        "contents": [{"parts": [{"text": ENRICH_PROMPT.format(book=desc)}]}],
        "tools": [{"google_search": {}}],
    }
    for model in _models():
        payload = json.loads(json.dumps(body))
        if "2.0" not in model:
            payload["generationConfig"] = {"thinkingConfig": {"thinkingBudget": 0}}
        try:
            r = httpx.post(f"{API_BASE}/{model}:generateContent",
                           headers={"x-goog-api-key": api_key}, json=payload, timeout=60)
        except httpx.HTTPError:
            continue
        if r.status_code == 429:
            _grounding_available = False  # free tier: no grounding quota
            return {}
        if r.status_code != 200:
            continue
        try:
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(text)
        except Exception:
            continue
    return {}
