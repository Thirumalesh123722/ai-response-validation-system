import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from sqlalchemy.orm import Session

from app import db, dashboard

PROJECT_TITLE = "AI Response Validation Report"
VERDICT_COLOR = {
    "Pass": colors.HexColor("#1E9E8E"),
    "Needs Improvement": colors.HexColor("#B8790C"),
    "Fail": colors.HexColor("#C0392B"),
}


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontSize=18, leading=22, spaceAfter=4, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="ReportSubtitle", fontSize=11, textColor=colors.HexColor("#555555"), spaceAfter=16))
    styles.add(ParagraphStyle(name="SectionHeading", fontSize=13, spaceBefore=18, spaceAfter=8, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SubHeading", fontSize=10.5, spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="Body", fontSize=9.5, leading=13))
    styles.add(ParagraphStyle(name="Small", fontSize=8, textColor=colors.HexColor("#666666"), leading=11))
    return styles


def _recommendations(summary) -> list[str]:
    recs = []
    if summary.avg_accuracy < 70:
        recs.append(f"Average Accuracy score is {summary.avg_accuracy}/100, below the 70 target. Review responses with factual errors.")
    if summary.hallucination_frequency_pct > 15:
        recs.append(f"{summary.hallucination_frequency_pct}% of evaluated responses contained at least one flagged unsupported claim.")
    if summary.avg_completeness < 70:
        recs.append(f"Average Completeness score is {summary.avg_completeness}/100. Responses frequently miss parts of what was asked.")
    if summary.avg_relevance < 70:
        recs.append(f"Average Relevance score is {summary.avg_relevance}/100. A meaningful share of responses drift off-topic.")
    fail_pct = 100 * summary.verdict_counts.get("Fail", 0) / summary.total_evaluations if summary.total_evaluations else 0
    if fail_pct > 20:
        recs.append(f"{round(fail_pct, 1)}% of evaluations resulted in a Fail verdict, exceeding a healthy threshold.")
    if not recs:
        recs.append("No significant quality issues detected across the evaluated set.")
    return recs


def generate_report_pdf(
    db_session: Session,
    organization_id: str,
    organization_name: str,
    date_from: str | None = None,
    date_to: str | None = None,
    mode: str | None = None,
    system_name: str | None = None,
    dataset_name: str | None = None,
    verdict_label: str | None = None,
    max_individual_results: int = 50,
) -> bytes:
    rows = db.query_evaluations(
        db_session, organization_id=organization_id,
        date_from=date_from, date_to=date_to, mode=mode,
        system_name=system_name, dataset_name=dataset_name, verdict_label=verdict_label,
        limit=10000,
    )
    summary = dashboard.compute_summary(
        db_session, organization_id=organization_id,
        date_from=date_from, date_to=date_to, mode=mode,
        system_name=system_name, dataset_name=dataset_name, verdict_label=verdict_label,
    )

    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.7 * inch, bottomMargin=0.7 * inch, leftMargin=0.7 * inch, rightMargin=0.7 * inch)
    story = []

    story.append(Paragraph(PROJECT_TITLE, styles["ReportTitle"]))
    story.append(Paragraph(organization_name, styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 10))

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    filter_desc = []
    if date_from: filter_desc.append(f"From: {date_from}")
    if date_to: filter_desc.append(f"To: {date_to}")
    if mode: filter_desc.append(f"Mode: {mode}")
    if system_name: filter_desc.append(f"System: {system_name}")
    if dataset_name: filter_desc.append(f"Dataset: {dataset_name}")
    if verdict_label: filter_desc.append(f"Verdict: {verdict_label}")
    filter_str = " | ".join(filter_desc) if filter_desc else "All evaluations (no filters applied)"

    meta_table = Table(
        [["Report generated", generated_at], ["Filters applied", filter_str], ["Total evaluations in report", str(summary.total_evaluations)]],
        colWidths=[1.8 * inch, 4.7 * inch],
    )
    meta_table.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 9), ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4)]))
    story.append(meta_table)

    if summary.total_evaluations == 0:
        story.append(Spacer(1, 20))
        story.append(Paragraph("No evaluations matched the selected filters.", styles["Body"]))
        doc.build(story)
        return buf.getvalue()

    story.append(Paragraph("Batch Summary", styles["SectionHeading"]))
    summary_table_data = [
        ["Metric", "Value"],
        ["Total Evaluations", str(summary.total_evaluations)],
        ["Pass", str(summary.verdict_counts.get("Pass", 0))],
        ["Needs Improvement", str(summary.verdict_counts.get("Needs Improvement", 0))],
        ["Fail", str(summary.verdict_counts.get("Fail", 0))],
        ["Average Final Score", f"{summary.avg_final_score}/100"],
        ["Average Relevance", f"{summary.avg_relevance}/100"],
        ["Average Accuracy", f"{summary.avg_accuracy}/100"],
        ["Average Groundedness (Hallucination)", f"{summary.avg_hallucination}/100"],
        ["Average Completeness", f"{summary.avg_completeness}/100"],
        ["Hallucination Frequency", f"{summary.hallucination_frequency_pct}%"],
    ]
    t = Table(summary_table_data, colWidths=[3.3 * inch, 3.2 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#222222")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)

    story.append(Paragraph("Improvement Recommendations", styles["SectionHeading"]))
    for i, rec in enumerate(_recommendations(summary), 1):
        story.append(Paragraph(f"{i}. {rec}", styles["Body"]))
        story.append(Spacer(1, 4))

    flagged = [r for r in rows if r["hallucination_flags"]]
    story.append(Paragraph(f"Flagged Responses ({len(flagged)})", styles["SectionHeading"]))
    if not flagged:
        story.append(Paragraph("No responses had flagged unsupported claims.", styles["Body"]))
    else:
        for r in flagged[:20]:
            story.append(Paragraph(f"Q: {r['question']}", styles["SubHeading"]))
            story.append(Paragraph(f"System: {r['system_name']} | Verdict: {r['verdict_label']}", styles["Small"]))
            for flag in r["hallucination_flags"]:
                story.append(Paragraph(f"&bull; {flag}", styles["Body"]))
            story.append(Spacer(1, 6))
        if len(flagged) > 20:
            story.append(Paragraph(f"...and {len(flagged) - 20} more flagged responses not shown.", styles["Small"]))

    story.append(PageBreak())
    story.append(Paragraph("Individual Evaluation Results", styles["SectionHeading"]))
    shown = rows[:max_individual_results]
    for idx, r in enumerate(shown, 1):
        verdict_color = VERDICT_COLOR.get(r["verdict_label"], colors.black)
        story.append(Paragraph(f"{idx}. {r['question']}", styles["SubHeading"]))
        story.append(Paragraph(f"System: {r['system_name']} &nbsp;|&nbsp; Mode: {r['mode']} &nbsp;|&nbsp; Date: {r['created_at'][:10]}", styles["Small"]))
        story.append(Paragraph(f"<b>Response:</b> {r['ai_response'][:400]}", styles["Body"]))

        score_table = Table(
            [["Relevance", "Accuracy", "Groundedness", "Completeness", "Final", "Verdict"],
             [f"{r['relevance_score']:.0f}", f"{r['accuracy_score']:.0f}", f"{r['hallucination_score']:.0f}", f"{r['completeness_score']:.0f}", f"{r['final_score']:.0f}", r["verdict_label"]]],
            colWidths=[0.95 * inch] * 6,
        )
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFEFEF")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
            ("TEXTCOLOR", (5, 1), (5, 1), verdict_color), ("FONTNAME", (5, 1), (5, 1), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(score_table)
        story.append(Paragraph(f"<b>Reasoning:</b> {r['verdict_reasoning'][:350]}", styles["Small"]))
        story.append(Spacer(1, 12))

    if len(rows) > max_individual_results:
        story.append(Paragraph(f"...and {len(rows) - max_individual_results} more evaluations not shown individually in this report.", styles["Small"]))

    doc.build(story)
    return buf.getvalue()
