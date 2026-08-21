"""
Persistence layer, now backed by Postgres via SQLAlchemy instead of raw
SQLite. The critical difference from the single-user version: every read
and write is scoped to an organization_id. There is no function in this
module that can accidentally return another tenant's data — the
organization_id parameter is required, not optional, on every query.
"""

import json
from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db_models import Evaluation


def save_evaluation(
    db: Session,
    result,  # EvaluationResult pydantic model
    question: str,
    ai_response: str,
    reference_answer: str | None,
    mode: str,
    model_used: str,
    organization_id: str,
    user_id: str | None = None,
    system_name: str = "Unspecified",
    dataset_name: str | None = None,
    batch_job_id: str | None = None,
) -> Evaluation:
    row = Evaluation(
        organization_id=organization_id,
        user_id=user_id,
        mode=mode,
        batch_job_id=batch_job_id,
        system_name=system_name,
        dataset_name=dataset_name,
        question=question,
        ai_response=ai_response,
        reference_answer=reference_answer,
        relevance_score=result.relevance_score,
        accuracy_score=result.accuracy_score,
        hallucination_score=result.hallucination_score,
        completeness_score=result.completeness_score,
        final_score=result.final_score,
        verdict_label=result.verdict_label,
        verdict_reasoning=result.verdict,
        relevance_reasoning=result.relevance_reasoning,
        accuracy_reasoning=result.accuracy_reasoning,
        hallucination_reasoning=result.hallucination_reasoning,
        completeness_reasoning=result.completeness_reasoning,
        hallucination_flags=result.hallucination_flags,
        model_used=model_used,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _row_to_dict(row: Evaluation) -> dict:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat(),
        "mode": row.mode,
        "batch_job_id": row.batch_job_id,
        "system_name": row.system_name,
        "dataset_name": row.dataset_name,
        "question": row.question,
        "ai_response": row.ai_response,
        "reference_answer": row.reference_answer,
        "relevance_score": row.relevance_score,
        "accuracy_score": row.accuracy_score,
        "hallucination_score": row.hallucination_score,
        "completeness_score": row.completeness_score,
        "final_score": row.final_score,
        "verdict_label": row.verdict_label,
        "verdict_reasoning": row.verdict_reasoning,
        "relevance_reasoning": row.relevance_reasoning,
        "accuracy_reasoning": row.accuracy_reasoning,
        "hallucination_reasoning": row.hallucination_reasoning,
        "completeness_reasoning": row.completeness_reasoning,
        "hallucination_flags": row.hallucination_flags or [],
        "model_used": row.model_used,
    }


def query_evaluations(
    db: Session,
    organization_id: str,  # required — this is what makes tenant isolation non-optional
    date_from: str | None = None,
    date_to: str | None = None,
    mode: str | None = None,
    system_name: str | None = None,
    dataset_name: str | None = None,
    verdict_label: str | None = None,
    limit: int = 500,
) -> list[dict]:
    q = db.query(Evaluation).filter(Evaluation.organization_id == organization_id)

    if date_from:
        q = q.filter(Evaluation.created_at >= datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc))
    if date_to:
        q = q.filter(Evaluation.created_at <= datetime.fromisoformat(date_to).replace(tzinfo=timezone.utc))
    if mode:
        q = q.filter(Evaluation.mode == mode)
    if system_name:
        q = q.filter(Evaluation.system_name == system_name)
    if dataset_name:
        q = q.filter(Evaluation.dataset_name == dataset_name)
    if verdict_label:
        q = q.filter(Evaluation.verdict_label == verdict_label)

    rows = q.order_by(desc(Evaluation.created_at)).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


def get_distinct_values(db: Session, organization_id: str, column: str) -> list[str]:
    assert column in ("system_name", "dataset_name", "mode", "verdict_label")
    col = getattr(Evaluation, column)
    rows = (
        db.query(col)
        .filter(Evaluation.organization_id == organization_id, col.isnot(None))
        .distinct()
        .all()
    )
    return sorted(r[0] for r in rows if r[0])
