# Development of AI Response Validation System with Hallucination Detection Assistance

*(internal codename: Veritas)* — Group 1

A multi-agent LLM pipeline that evaluates AI-generated responses across
four dimensions — Relevance, Accuracy, Hallucination/Groundedness, and
Completeness — grounded in retrieved reference material via RAG, and
aggregated into a weighted Pass / Needs Improvement / Fail verdict.

Supports single-response evaluation, CSV batch evaluation, a filterable
scoring dashboard, and PDF report export.

## License

MIT — see [LICENSE](./LICENSE).

## Documentation

- [`AGILE.md`](./AGILE.md) — sprint breakdown, backlog, retrospectives
- [`agile_docs/`](./agile_docs) — Agile Documentation, Defect Tracker, and Unit Test Plan (Excel, mentor template format)
- [`docs/TECHNICAL_DOCUMENTATION.md`](./docs/TECHNICAL_DOCUMENTATION.md) — architecture, API reference, database schema
- [`docs/PROJECT_REPORT.md`](./docs/PROJECT_REPORT.md) — formal project report
- [`backend/tests/E2E_TESTING_REPORT.md`](./backend/tests/E2E_TESTING_REPORT.md) — test results
- [`DEPLOYMENT.md`](./DEPLOYMENT.md) — how to deploy this project

## Stack

```
backend/   FastAPI + PostgreSQL (SQLAlchemy) + ChromaDB + Groq API
frontend/  React + Vite + Tailwind
```

## Quick Start (local development)

### 1. Database
You need a Postgres database. Easiest options: Neon (neon.tech) or
Supabase (supabase.com), both have a free tier, or run Postgres locally.

### 2. Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set DATABASE_URL, GROQ_API_KEY, and a real JWT_SECRET
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`, create an account, log in, and go.

## Testing & Validation

```bash
cd backend
pytest tests/test_e2e.py -v                       # 22 automated end-to-end tests
python validation/run_validation.py                # scoring correctness (TruthfulQA + SQuAD)
python validation/run_consistency_check.py          # scoring consistency (needs live Groq key)
```

## Deployment

See `DEPLOYMENT.md` for step-by-step deployment instructions.
