import csv
import io
import uuid
from threading import Thread, Lock

from app.config import settings
from app.database import SessionLocal
from app.orchestrator import run_evaluation
from app.schemas import BatchJobStatus, BatchRowResult, EvaluationRequest
from app import db

_jobs: dict[str, BatchJobStatus] = {}
_job_owners: dict[str, str] = {}  # job_id -> organization_id, checked on every status poll
_lock = Lock()


def parse_csv(file_bytes: bytes) -> list[dict]:
    text = file_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        question = (row.get("question") or "").strip()
        ai_response = (row.get("ai_response") or "").strip()
        if not question or not ai_response:
            continue
        rows.append({
            "question": question,
            "ai_response": ai_response,
            "reference_answer": (row.get("reference_answer") or "").strip() or None,
        })
    return rows


def _process_job(job_id: str, rows: list[dict], organization_id: str, user_id: str, system_name: str, dataset_name: str | None) -> None:
    # Background thread needs its own DB session — SQLAlchemy sessions
    # aren't safe to share across threads.
    thread_db = SessionLocal()
    try:
        for i, row in enumerate(rows):
            try:
                req = EvaluationRequest(
                    question=row["question"], ai_response=row["ai_response"],
                    reference_answer=row.get("reference_answer"), source_document_id=None,
                    system_name=system_name, dataset_name=dataset_name,
                )
                result = run_evaluation(req)
                db.save_evaluation(
                    thread_db, result=result, question=row["question"], ai_response=row["ai_response"],
                    reference_answer=row.get("reference_answer"), mode="batch", model_used=settings.groq_model,
                    organization_id=organization_id, user_id=user_id,
                    system_name=system_name, dataset_name=dataset_name, batch_job_id=job_id,
                )
                row_result = BatchRowResult(row_index=i, question=row["question"], ai_response=row["ai_response"], result=result)
            except Exception as exc:
                row_result = BatchRowResult(row_index=i, question=row["question"], ai_response=row["ai_response"], error=str(exc))

            with _lock:
                job = _jobs[job_id]
                job.rows.append(row_result)
                job.completed += 1
    finally:
        thread_db.close()

    with _lock:
        _jobs[job_id].status = "done"


def start_batch_job(rows: list[dict], organization_id: str, user_id: str, system_name: str = "Unspecified", dataset_name: str | None = None) -> str:
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = BatchJobStatus(job_id=job_id, status="running", total=len(rows), completed=0, rows=[])
        _job_owners[job_id] = organization_id
    thread = Thread(target=_process_job, args=(job_id, rows, organization_id, user_id, system_name, dataset_name), daemon=True)
    thread.start()
    return job_id


def get_job(job_id: str, organization_id: str) -> BatchJobStatus | None:
    """Returns None if the job doesn't exist OR belongs to a different
    organization — callers can't distinguish "not found" from "not yours",
    which is the correct behavior (don't confirm another org's job_id is valid)."""
    with _lock:
        if _job_owners.get(job_id) != organization_id:
            return None
        return _jobs.get(job_id)
