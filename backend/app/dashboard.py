from collections import defaultdict

from sqlalchemy.orm import Session

from app import db
from app.schemas import DashboardSummary


def compute_summary(
    db_session: Session,
    organization_id: str,
    date_from: str | None = None,
    date_to: str | None = None,
    mode: str | None = None,
    system_name: str | None = None,
    dataset_name: str | None = None,
    verdict_label: str | None = None,
) -> DashboardSummary:
    rows = db.query_evaluations(
        db_session, organization_id=organization_id,
        date_from=date_from, date_to=date_to, mode=mode,
        system_name=system_name, dataset_name=dataset_name, verdict_label=verdict_label,
        limit=10000,
    )

    total = len(rows)
    if total == 0:
        return DashboardSummary(
            total_evaluations=0,
            verdict_counts={"Pass": 0, "Needs Improvement": 0, "Fail": 0},
            avg_relevance=0, avg_accuracy=0, avg_hallucination=0, avg_completeness=0,
            avg_final_score=0, hallucination_frequency_pct=0,
            quality_trend=[],
            available_systems=db.get_distinct_values(db_session, organization_id, "system_name"),
            available_datasets=db.get_distinct_values(db_session, organization_id, "dataset_name"),
        )

    verdict_counts = {"Pass": 0, "Needs Improvement": 0, "Fail": 0}
    for r in rows:
        verdict_counts[r["verdict_label"]] = verdict_counts.get(r["verdict_label"], 0) + 1

    avg_relevance = sum(r["relevance_score"] for r in rows) / total
    avg_accuracy = sum(r["accuracy_score"] for r in rows) / total
    avg_hallucination = sum(r["hallucination_score"] for r in rows) / total
    avg_completeness = sum(r["completeness_score"] for r in rows) / total
    avg_final = sum(r["final_score"] for r in rows) / total

    flagged_count = sum(1 for r in rows if len(r["hallucination_flags"]) > 0)
    hallucination_freq_pct = round(100 * flagged_count / total, 1)

    by_day = defaultdict(list)
    for r in rows:
        day = r["created_at"][:10]
        by_day[day].append(r["final_score"])

    trend = [
        {"date": day, "avg_final_score": round(sum(scores) / len(scores), 2), "count": len(scores)}
        for day, scores in sorted(by_day.items())
    ]

    return DashboardSummary(
        total_evaluations=total,
        verdict_counts=verdict_counts,
        avg_relevance=round(avg_relevance, 1),
        avg_accuracy=round(avg_accuracy, 1),
        avg_hallucination=round(avg_hallucination, 1),
        avg_completeness=round(avg_completeness, 1),
        avg_final_score=round(avg_final, 1),
        hallucination_frequency_pct=hallucination_freq_pct,
        quality_trend=trend,
        available_systems=db.get_distinct_values(db_session, organization_id, "system_name"),
        available_datasets=db.get_distinct_values(db_session, organization_id, "dataset_name"),
    )
