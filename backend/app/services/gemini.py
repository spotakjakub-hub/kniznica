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
