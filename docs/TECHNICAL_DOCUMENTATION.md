# Technical Documentation

**Project:** Development of AI Response Validation System with Hallucination Detection Assistance — Group 1

## 1. Project Overview

This system evaluates AI-generated responses using a multi-agent LLM
pipeline combined with Retrieval-Augmented Generation (RAG). Given a
question, an AI response, and optionally a reference answer or source
document, it produces four dimension scores (Relevance, Accuracy,
Hallucination/Groundedness, Completeness), a weighted overall score, a
categorical verdict (Pass / Needs Improvement / Fail), and specific
flagged claims where the response is unsupported.

The system supports evaluating a single response, batch-evaluating many
question-response pairs from a CSV file, viewing aggregated results on a
dashboard with filters and trend charts, and exporting a structured PDF
report.

## 2. Problem Statement

There is no consistent, automated way to answer "is this AI response
actually trustworthy?" at scale. Manual review does not scale; this
system uses LLMs themselves as specialized judges to produce consistent,
explainable, auditable assessments.

## 3. Objectives

1. Build independent judge agents for four evaluation dimensions:
   Relevance, Accuracy, Hallucination/Groundedness, and Completeness.
2. Aggregate these into a single weighted quality verdict.
3. Support grounding evaluation against reference material via RAG
   (ChromaDB), not just the judge's own background knowledge.
4. Provide both single-response and batch (CSV) evaluation workflows.
5. Persist every evaluation and expose it through a dashboard with
   filters, charts, and trend analysis.
6. Support exporting evaluation results as a structured PDF report.
7. Validate that the agents produce scoring that is both correct
   (rewards good answers, penalizes bad ones) and consistent (stable
   across repeated runs).

## 4. System Architecture

```
                        +----------------------+
   User (browser)  ---> |   React Frontend     |
                        |  (Vite + Tailwind)   |
                        +----------+-----------+
                                   | REST / JSON
                                   v
                        +----------------------+
                        |   FastAPI Backend     |
                        |                       |
                        |  +-----------------+  |
                        |  |  Orchestrator   |  |
                        |  +--------+--------+  |
                        |           |           |
                 +------+-----------+-----------+------+
                 v              v              v        v
          +----------+  +-------------+ +---------+ +----------+
          | ChromaDB |  |  5 Agents   | | SQLite  | | Groq API |
          |  (RAG)   |  |(Relevance,  | |(history)| |  (LLM)   |
          |          |  | Accuracy,   | |         | |          |
          |          |  | Halluc.,    | |         | |          |
          |          |  | Complete.,  | |         | |          |
          |          |  | Verdict)    | |         | |          |
          +----------+  +-------------+ +---------+ +----------+
```

**Request flow for a single evaluation:**
1. Client sends `{question, ai_response, reference_answer?, source_document_id?}` to `POST /evaluate`.
2. Orchestrator retrieves relevant context from ChromaDB if a source document was linked, or no reference answer was given.
3. Four judge agents run in sequence (paced ~1.5s apart to respect API rate limits), each calling Groq with a dimension-specific prompt.
4. Verdict Agent combines the four scores using fixed weights into a final score and Pass/Needs Improvement/Fail label, then writes a consolidated reasoning summary.
5. The full result is saved to the database and returned to the client.
6. If any agent call fails (bad key, rate limit, network), that agent's fallback heuristic (word-overlap scoring) is used instead, so the pipeline never hard-fails.

**Batch flow:** a CSV is parsed into rows, a background thread processes each row through the same pipeline above, and the client polls `/batch/status/{job_id}` for live progress.

## 5. Folder Structure

```
ai-eval-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, all HTTP endpoints
│   │   ├── config.py             # Settings (API key/model, DB paths, CORS)
│   │   ├── schemas.py            # Pydantic request/response models
│   │   ├── orchestrator.py       # Runs the full single-evaluation pipeline
│   │   ├── batch.py              # Background batch job processing
│   │   ├── db.py                 # Persistence layer
│   │   ├── dashboard.py          # Aggregation logic for dashboard stats
│   │   ├── report.py             # PDF report generation (reportlab)
│   │   ├── agents/
│   │   │   ├── base.py           # Shared LLM API call logic + retry/backoff
│   │   │   ├── relevance.py      # Relevance Judge
│   │   │   ├── accuracy.py       # Accuracy Judge
│   │   │   ├── hallucination.py  # Hallucination Detector
│   │   │   ├── completeness.py   # Completeness Judge
│   │   │   ├── verdict.py        # Verdict Agent (weighting + labeling)
│   │   │   └── fallback.py       # Heuristic fallback scorer
│   │   └── rag/
│   │       └── chroma_store.py   # ChromaDB ingest/chunk/query wrapper
│   ├── tests/
│   │   ├── test_e2e.py           # End-to-end test suite
│   │   └── E2E_TESTING_REPORT.md
│   ├── validation/
│   │   ├── benchmark_dataset.json     # Real TruthfulQA/SQuAD cases
│   │   ├── run_validation.py          # Scoring correctness validation
│   │   └── run_consistency_check.py   # Scoring stability validation
│   ├── data/                     # Database + ChromaDB storage (gitignored)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx                # Tab layout: Single / Batch / Dashboard
│       ├── components/
│       │   ├── EvaluationForm.jsx
│       │   ├── ScoreCard.jsx
│       │   ├── Gauge.jsx
│       │   ├── VerdictBanner.jsx
│       │   ├── DimensionRadar.jsx
│       │   ├── BatchEvaluation.jsx
│       │   ├── Dashboard.jsx
│       │   ├── SubmissionSummary.jsx
│       │   ├── ConnectionStatus.jsx
│       │   └── PipelineLoader.jsx
│       └── lib/api.js             # All backend API calls
└── docs/
    ├── TECHNICAL_DOCUMENTATION.md  # This file
    └── PROJECT_REPORT.md
```

## 6. Installation Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- An LLM API key (free tier available) from https://console.groq.com/keys

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env, set GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Visit `http://localhost:5173`.

## 7. API Documentation

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check + API key validity |
| POST | `/ingest` | Upload a document (.pdf/.txt/.md) into the RAG knowledge base |
| POST | `/evaluate` | Run the full pipeline on one question/response |
| POST | `/batch/upload` | Upload a CSV, start a background batch evaluation job |
| GET | `/batch/status/{job_id}` | Poll batch job progress/results |
| GET | `/dashboard/summary` | Aggregated stats (totals, verdict counts, averages, trend) |
| GET | `/dashboard/evaluations` | Raw evaluation history, filterable |
| GET | `/report/pdf` | Generate and download a structured PDF report |

All list/summary endpoints accept optional query filters: `date_from`,
`date_to`, `mode` (`single`/`batch`), `system_name`, `dataset_name`,
`verdict_label`.

Full interactive API docs (auto-generated by FastAPI) are available at
`http://localhost:8000/docs` while the backend is running.

### Example: `POST /evaluate`

Request:
```json
{
  "question": "What is the capital of France?",
  "ai_response": "Paris is the capital of France.",
  "reference_answer": "Paris is the capital of France.",
  "system_name": "ChatGPT"
}
```

Response:
```json
{
  "relevance_score": 95.0,
  "accuracy_score": 100.0,
  "hallucination_score": 100.0,
  "completeness_score": 90.0,
  "final_score": 97.25,
  "verdict_label": "Pass",
  "verdict": "The response directly and correctly answers the question...",
  "relevance_reasoning": "...",
  "accuracy_reasoning": "...",
  "hallucination_reasoning": "...",
  "completeness_reasoning": "...",
  "hallucination_flags": [],
  "retrieved_context": []
}
```

## 8. Database Schema

Single table capturing every evaluation:

```sql
CREATE TABLE evaluations (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    mode TEXT NOT NULL,                 -- 'single' | 'batch'
    batch_job_id TEXT,                  -- null for single evaluations
    system_name TEXT NOT NULL,          -- which AI system produced the response
    dataset_name TEXT,                  -- optional grouping label
    question TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    reference_answer TEXT,
    relevance_score REAL NOT NULL,
    accuracy_score REAL NOT NULL,
    hallucination_score REAL NOT NULL,
    completeness_score REAL NOT NULL,
    final_score REAL NOT NULL,
    verdict_label TEXT NOT NULL,
    verdict_reasoning TEXT NOT NULL,
    relevance_reasoning TEXT NOT NULL,
    accuracy_reasoning TEXT NOT NULL,
    hallucination_reasoning TEXT NOT NULL,
    completeness_reasoning TEXT NOT NULL,
    hallucination_flags TEXT NOT NULL,  -- JSON array, stored as text
    model_used TEXT NOT NULL
);
```
Indexed on `created_at`, `verdict_label`, `system_name`, `mode` for fast
dashboard filtering.

ChromaDB (separate, vector storage) stores document chunks for RAG
retrieval: `document_id`, chunk text, and `{document_id, source,
chunk_index}` metadata per chunk.

## 9. RAG Workflow

1. A source document (PDF/TXT/MD) is uploaded via `POST /ingest`.
2. Text is extracted (via `pypdf` for PDFs) and split into overlapping
   ~800-word chunks (120-word overlap) to preserve context across chunk
   boundaries.
3. Each chunk is embedded (ChromaDB's default `all-MiniLM-L6-v2` sentence
   embedding model) and stored with a shared `document_id`.
4. At evaluation time, if a `source_document_id` is provided (or no
   `reference_answer` was given at all), the question is embedded and the
   top-5 (or top-3, for the no-reference case) most similar chunks are
   retrieved.
5. Retrieved chunks are passed as additional context to the Accuracy,
   Hallucination, and Completeness agents, so their judgments are grounded
   in the actual source material rather than the model's own background
   knowledge.

## 10. Agent Descriptions

| Agent | Role | Output |
|---|---|---|
| **Relevance Judge** | Does the response actually address the question asked, independent of correctness? | Score 0-100 + reasoning |
| **Accuracy Judge** | Is the response factually correct against the reference answer / retrieved context? | Score 0-100 + reasoning |
| **Hallucination Detector** | Does the response contain claims not supported by the reference material? | Groundedness score 0-100 (100 = fully grounded) + reasoning + a list of specific flagged claims |
| **Completeness Judge** | Does the response cover everything the question and reference material call for? | Score 0-100 + reasoning naming specific omissions |
| **Verdict Agent** | Combines the four scores via fixed weights into one final score and label | Final score, Pass/Needs Improvement/Fail label, consolidated reasoning |

**Weighting** (`app/agents/verdict.py`): Accuracy 35%, Hallucination 25%,
Relevance 20%, Completeness 20% — accuracy and groundedness are weighted
highest since factual trustworthiness matters most.

**Verdict thresholds**: final score ≥75 → Pass, 45–74 → Needs Improvement,
<45 → Fail.

**Fallback behavior**: if any agent's API call fails (bad/missing key,
rate limit, network issue), that specific agent falls back to a
deterministic word-overlap heuristic instead of crashing the whole
pipeline — clearly labeled as a fallback result in its reasoning text.

## 11. Dashboard Explanation

The Dashboard tab aggregates all persisted evaluations (single + batch)
and provides:
- **Stat cards**: total evaluations, Pass/Needs Improvement/Fail counts,
  average score per dimension, hallucination frequency (% of evaluations
  with at least one flagged claim).
- **Pie chart**: verdict distribution.
- **Bar chart**: average score per dimension.
- **Line chart**: average final score per day (quality trend over time).
- **Filters**: date range, mode (single/batch), AI system name, dataset
  label, verdict — all combinable, all backed by the same query layer
  used by the PDF export, so dashboard and report always agree.
- **Recent evaluations table**: browsable list of the underlying records.

Tagging evaluations with an **AI system name** (e.g. "ChatGPT" vs
"System A") and filtering the dashboard by that field is how two
different AI systems' performance on the same question set can be
compared.

## 12. Report Generation

`GET /report/pdf` (accepting the same filters as the dashboard) builds a
structured PDF via `reportlab`, containing: project details, a batch
summary table (totals, verdict counts, dimension averages, hallucination
frequency), auto-generated improvement recommendations (rule-based, driven
by which averages fall below quality thresholds), a list of flagged
(hallucinated) responses with their specific unsupported claims, and
individual per-evaluation results with all four scores and reasoning.

## 13. Testing Results

See `backend/tests/E2E_TESTING_REPORT.md` for the full report. Summary:
21/22 automated end-to-end tests passing, 1 skipped due to an environment
network restriction (unrelated to application correctness). Testing
surfaced and led to the fix of one real defect: RAG retrieval failures
were not previously isolated from the rest of the pipeline.

See `backend/validation/` for scoring-quality validation (against real
TruthfulQA/SQuAD samples) and scoring-consistency validation (same inputs,
multiple runs).

## 14. Limitations

- Uses a single LLM provider for all five agents; judgments inherit
  whatever biases or blind spots that specific model has.
- Free-tier API rate limits require pacing calls (~1.5s between agent
  calls), so evaluations are not instantaneous — a single evaluation takes
  roughly 10-20 seconds, and batch evaluations scale linearly with row
  count.
- The fallback heuristic scorer (used only when the LLM API is
  unavailable) is a simple word-overlap measure — useful for keeping the
  system operational, but not a substitute for real judgment quality.
- RAG chunking is a simple fixed-size word-count strategy; it does not
  respect semantic or document-structural boundaries (headings, sections).
- Consistency validation requires manual execution with a live API key;
  it is not currently run automatically on a schedule.

## 15. Future Work

- Support multiple LLM providers per agent (e.g. cross-checking one
  agent's judgment against a second, different model) to reduce
  single-model bias.
- Smarter, structure-aware document chunking for RAG.
- Asynchronous/parallel agent calls (with rate-limit-aware queuing) to
  reduce per-evaluation latency.
- Scheduled, automated consistency validation with historical trend
  tracking of agent stability over time.
- Support additional batch input formats (e.g. Excel, JSON Lines).
