from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ScanJob
from app.services import queue_worker, storage

router = APIRouter(prefix="/api/queue", tags=["queue"])

MAX_IMAGE_BYTES = 15 * 1024 * 1024


def _job_out(job: ScanJob) -> dict:
    return {
        "id": job.id,
        "cover_url": job.cover_url,
        "status": job.status,
        "location": job.location,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.post("/upload", status_code=201)
async def upload_to_queue(
    files: List[UploadFile] = File(...),
    location: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Stores the photos and queues them for background identification."""
    jobs = []
    for f in files:
        data = await f.read()
        if not data:
            continue
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(413, f"{f.filename}: image too large (max 15 MB)")
        try:
            url = storage.upload_cover(data, f.content_type)
        except storage.StorageError as e:
            raise HTTPException(502, f"Photo upload failed: {e}")
        job = ScanJob(cover_url=url, location=(location or "").strip() or None)
        db.add(job)
        jobs.append(job)
    if not jobs:
        raise HTTPException(422, "No usable image files")
    db.commit()
    queue_worker.kick()
    return {"jobs": [_job_out(j) for j in jobs]}


@router.get("/")
def list_queue(db: Session = Depends(get_db)):
    jobs = db.query(ScanJob).order_by(ScanJob.created_at).all()
    counts = {}
    for j in jobs:
        counts[j.status] = counts.get(j.status, 0) + 1
    return {"jobs": [_job_out(j) for j in jobs], "counts": counts}


@router.post("/{job_id}/retry")
def retry_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "failed":
        raise HTTPException(409, "Only failed jobs can be retried")
    job.status = "pending"
    job.error = None
    db.commit()
    queue_worker.kick()
    return _job_out(job)


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Removes a job — used both for reject and after a confirmed save."""
    job = db.query(ScanJob).filter(ScanJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    db.delete(job)
    db.commit()