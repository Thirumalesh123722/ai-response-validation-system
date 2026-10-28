import httpx
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pypdf import PdfReader
from sqlalchemy.orm import Session
import io

from app.config import settings
from app.schemas import EvaluationRequest, EvaluationResult, IngestResponse, BatchJobStatus, DashboardSummary, EvaluationRecord
from app.orchestrator import run_evaluation
from app.rag.chroma_store import knowledge_base
from app.database import get_db, init_db
from app.deps import get_current_user, CurrentUser
from app import batch, db, dashboard, report
from app.auth_routes import router as auth_router

app = FastAPI(title="AI Response Validation System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "AI Response Validation System",
        "version": "2.0.0",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    key = settings.groq_api_key
    if not key:
        return {
            "status": "ok",
            "groq": "GROQ_API_KEY not set — add it in Render Environment Variables or backend/.env",
            "model": settings.groq_model,
            "fix": "Get a free key at https://console.groq.com/keys and set GROQ_API_KEY",
        }

    groq_status = "unreachable"
    available_models = []
    model_available = False

    try:
        resp = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            groq_status = "ok"
            models_data = resp.json().get("data", [])
            available_models = sorted([m["id"] for m in models_data])
            model_available = settings.groq_model in available_models
            if not model_available:
                groq_status = f"connected but model '{settings.groq_model}' not found"
        elif resp.status_code in (401, 403):
            groq_status = f"invalid API key ({resp.status_code})"
        else:
            groq_status = f"unexpected response: {resp.status_code} {resp.text[:150]}"
    except Exception as exc:
        groq_status = f"unreachable: {exc}"

    result = {
        "status": "ok",
        "groq": groq_status,
        "model": settings.groq_model,
        "model_available": model_available,
    }

    if available_models:
        result["available_models"] = available_models

    if not model_available and available_models:
        result["fix"] = (
            f"Model '{settings.groq_model}' is not available. "
            f"Set GROQ_MODEL to one of: {', '.join(available_models[:5])}"
        )

    return result


# ---- Everything below requires authentication and is scoped to the caller's organization ----

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...), current: CurrentUser = Depends(get_current_user)):
    raw = await file.read()
    filename = file.filename or "uploaded_document"

    if filename.lower().endswith(".pdf"):
        try:
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse PDF: {exc}")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Unsupported file encoding; use .txt, .md, or .pdf")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in document")

    try:
        document_id, chunk_count = knowledge_base.ingest(text, source_name=filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not index document into knowledge base: {exc}")
    return IngestResponse(document_id=document_id, chunks_indexed=chunk_count)


@app.post("/evaluate", response_model=EvaluationResult)
def evaluate(request: EvaluationRequest, current: CurrentUser = Depends(get_current_user), db_session: Session = Depends(get_db)):
    try:
        result = run_evaluation(request)
        db.save_evaluation(
            db_session, result=result, question=request.question, ai_response=request.ai_response,
            reference_answer=request.reference_answer, mode="single", model_used=settings.groq_model,
            organization_id=current.organization_id, user_id=current.user_id,
            system_name=request.system_name, dataset_name=request.dataset_name,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/batch/upload")
async def batch_upload(
    file: UploadFile = File(...),
    system_name: str = Form("Unspecified"),
    dataset_name: str | None = Form(None),
    current: CurrentUser = Depends(get_current_user),
):
    raw = await file.read()
    try:
        rows = batch.parse_csv(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")

    if not rows:
        raise HTTPException(status_code=400, detail="No valid rows found. CSV must have 'question' and 'ai_response' columns.")

    resolved_dataset_name = dataset_name or file.filename or "batch_upload"
    job_id = batch.start_batch_job(rows, organization_id=current.organization_id, user_id=current.user_id, system_name=system_name, dataset_name=resolved_dataset_name)
    return {"job_id": job_id, "total": len(rows)}


@app.get("/batch/status/{job_id}", response_model=BatchJobStatus)
def batch_status(job_id: str, current: CurrentUser = Depends(get_current_user)):
    job = batch.get_job(job_id, organization_id=current.organization_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    date_from: str | None = None, date_to: str | None = None, mode: str | None = None,
    system_name: str | None = None, dataset_name: str | None = None, verdict_label: str | None = None,
    current: CurrentUser = Depends(get_current_user), db_session: Session = Depends(get_db),
):
    return dashboard.compute_summary(
        db_session, organization_id=current.organization_id,
        date_from=date_from, date_to=date_to, mode=mode,
        system_name=system_name, dataset_name=dataset_name, verdict_label=verdict_label,
    )


@app.get("/dashboard/evaluations", response_model=list[EvaluationRecord])
def dashboard_evaluations(
    date_from: str | None = None, date_to: str | None = None, mode: str | None = None,
    system_name: str | None = None, dataset_name: str | None = None, verdict_label: str | None = None, limit: int = 500,
    current: CurrentUser = Depends(get_current_user), db_session: Session = Depends(get_db),
):
    return db.query_evaluations(
        db_session, organization_id=current.organization_id,
        date_from=date_from, date_to=date_to, mode=mode,
        system_name=system_name, dataset_name=dataset_name, verdict_label=verdict_label, limit=limit,
    )


@app.get("/report/pdf")
def report_pdf(
    date_from: str | None = None, date_to: str | None = None, mode: str | None = None,
    system_name: str | None = None, dataset_name: str | None = None, verdict_label: str | None = None,
    current: CurrentUser = Depends(get_current_user), db_session: Session = Depends(get_db),
):
    try:
        pdf_bytes = report.generate_report_pdf(
            db_session, organization_id=current.organization_id, organization_name=current.full_name,
            date_from=date_from, date_to=date_to, mode=mode,
            system_name=system_name, dataset_name=dataset_name, verdict_label=verdict_label,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    filename = f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
