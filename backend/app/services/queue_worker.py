"""In-process worker for the batch scan queue.

Render's free tier has no separate worker dyno, so jobs are processed by a
daemon thread inside the API process: kicked on upload and on startup, one job
at a time (gentle on the free-tier Gemini rate limits). If the dyno restarts
mid-queue, startup resets stale jobs and resumes.
"""
import threading
import time

import httpx

from app.database import SessionLocal
from app.models import ScanJob
from app.services import gemini, lookup

_lock = threading.Lock()
_running = False

PAUSE_BETWEEN_JOBS = 3  # seconds


def kick():
    """Starts the worker thread unless it is already running."""
    global _running
    with _lock:
        if _running:
            return
        _running = True
    threading.Thread(target=_run, daemon=True).start()


def resume_on_startup():
    """Resets jobs stuck in 'processing' (e.g. after a dyno restart) and resumes."""
    db = SessionLocal()
    try:
        stale = db.query(ScanJob).filter(ScanJob.status == "processing").all()
        for job in stale:
            job.status = "pending"
        db.commit()
        has_pending = db.query(ScanJob).filter(ScanJob.status == "pending").count() > 0
    finally:
        db.close()
    if has_pending:
        kick()


def _process(job: ScanJob) -> dict:
    img = httpx.get(job.cover_url, timeout=60).content
    ai = gemini.identify([(img, "image/jpeg")])

    candidates = []
    if ai.get("isbn"):
        candidates = lookup.by_isbn(ai["isbn"])
    if not candidates and ai.get("title"):
        first_author = next((a.get("name") for a in ai.get("authors") or []), None)
        candidates = lookup.by_title_author(ai["title"], first_author)

    prefill = lookup.merge_prefill(ai, candidates, job.cover_url)
    if any(not prefill.get(k) for k in ("publisher", "published_year", "pages", "isbn13")):
        enriched = gemini.web_enrich(ai)
        if enriched:
            prefill = lookup.apply_enrichment(prefill, enriched)
    if job.location and not prefill.get("location"):
        prefill["location"] = job.location
    return prefill


def _run():
    global _running
    try:
        while True:
            db = SessionLocal()
            try:
                job = (
                    db.query(ScanJob)
                    .filter(ScanJob.status == "pending")
                    .order_by(ScanJob.created_at)
                    .first()
                )
                if not job:
                    break
                job.status = "processing"
                db.commit()
                try:
                    job.result = _process(job)
                    job.status = "done"
                    job.error = None
                except Exception as e:  # noqa: BLE001 — job must fail, not the worker
                    job.status = "failed"
                    job.error = str(e)[:500]
                db.commit()
            finally:
                db.close()
            time.sleep(PAUSE_BETWEEN_JOBS)
    finally:
        with _lock:
            _running = False