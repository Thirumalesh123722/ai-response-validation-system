# Project Report

**Development of AI Response Validation System with Hallucination Detection Assistance — Group 1**

## 1. Introduction

AI systems are increasingly relied upon to answer questions across
education, customer support, research, and everyday use. But an AI
response that reads fluently is not necessarily correct, complete, or
grounded in fact. This project builds a system that automatically
evaluates AI-generated responses across four quality dimensions —
Relevance, Accuracy, Groundedness (freedom from hallucination), and
Completeness — using a multi-agent architecture of specialized LLM
judges, combined with Retrieval-Augmented Generation (RAG) so evaluations
can be grounded against real reference material rather than a judge's own
background knowledge alone.

## 2. Objectives

- Build four independent judge agents, each responsible for one
  evaluation dimension, so scoring logic per dimension stays isolated and
  auditable.
- Aggregate the four scores into a single, weighted, interpretable
  verdict (Pass / Needs Improvement / Fail).
- Ground evaluation in retrievable reference material via RAG rather than
  relying solely on a judge model's internal knowledge.
- Support both single-response evaluation and bulk (CSV) batch
  evaluation.
- Persist evaluation history and expose it through an interactive
  dashboard with filtering and trend visualization.
- Support exporting evaluation results as a professional PDF report.
- Empirically validate that the system's scoring is both correct
  (rewards good answers, penalizes bad ones) and consistent (stable
  across repeated runs).

## 3. Methodology

The project was built iteratively across four milestones (see `AGILE.md`
for the full sprint-by-sprint breakdown):

- **Milestone 2** established the core judge agents (Relevance, Accuracy,
  Hallucination Detection) and validated their scoring against real
  samples from two established benchmark datasets — TruthfulQA (correct
  answers vs. known common misconceptions) and SQuAD (correct answers vs.
  evasive non-answers).
- **Milestone 3** added the Completeness Judge and the Verdict Agent
  (weighted aggregation into a Pass/Needs Improvement/Fail label), built
  the results interface, and added CSV batch evaluation.
- **Milestone 4** added persistence, a scoring dashboard, PDF report
  export, an automated end-to-end test suite, and scoring consistency
  validation.

Throughout, a deliberate reliability principle was followed: **the system
should never hard-fail**. Every LLM-dependent component (the four judge
agents, RAG retrieval) has a fallback path, so a transient API failure
degrades gracefully to a heuristic estimate rather than crashing the
evaluation.

## 4. System Design

The system is a two-tier web application:

- **Backend** (FastAPI/Python): exposes REST endpoints for evaluation,
  batch processing, dashboard aggregation, and report generation.
  Internally organized around an orchestrator that sequences the five
  agents, a RAG layer (ChromaDB) for retrieval, and a persistence layer
  that every evaluation is written to.
- **Frontend** (React/Vite): three main views — Single Evaluation, Batch
  Evaluation, and Dashboard — all communicating with the backend over a
  single shared API client.

See `docs/TECHNICAL_DOCUMENTATION.md` for the full architecture diagram,
API reference, and database schema.

**Key design decisions:**
- *Weighted rather than averaged scoring*: Accuracy (35%) and
  Groundedness (25%) are weighted above Relevance and Completeness (20%
  each), reflecting that factual trustworthiness matters more than
  topicality or completeness alone.
- *Categorical verdict alongside numeric score*: a raw 0-100 score is
  harder to act on than a clear Pass/Needs Improvement/Fail label, so both
  are provided.
- *System/dataset tagging*: every evaluation can be tagged with which AI
  system produced the response and which dataset it came from, enabling
  direct side-by-side comparison of two different AI systems on the
  dashboard.

## 5. Implementation

The five agents (`app/agents/`) share a common base class
(`base.py`) that handles the actual LLM API call, JSON-mode response
parsing, and automatic retry-with-backoff on rate-limit (429) responses.
Each agent subclass supplies only its own system prompt and the specific
fields it needs from the request.

The orchestrator (`app/orchestrator.py`) runs the four dimension agents
in sequence (paced to respect free-tier rate limits), computes the
weighted final score and verdict label, and calls the Verdict Agent for a
natural-language consolidated summary. Every step is wrapped so that a
failure in any single agent — or in RAG retrieval — degrades to a
fallback rather than failing the whole request.

Batch evaluation (`app/batch.py`) parses an uploaded CSV and processes
rows in a background thread, exposing progress via a pollable job status
endpoint, so the frontend can show a live progress bar without blocking
on a single long HTTP request.

Persistence (`app/db.py`) captures every field of every evaluation,
indexed for the filter combinations the dashboard and report generator
need. Dashboard aggregation (`app/dashboard.py`) and PDF report
generation (`app/report.py`) both query this same table through the same
filter parameters, so the two views are always consistent with each
other.

## 6. Experimental Results

### Scoring correctness (Milestone 2 validation)
20 real samples from TruthfulQA (10) and SQuAD (10) were run through the
live pipeline, each case designed so a correct answer should score high
on the relevant dimension and a deliberately wrong/evasive answer should
score low. See `backend/validation/run_validation.py` and its generated
report for full results.

### Scoring consistency (Milestone 4 validation)
A subset of the same benchmark dataset was run multiple times each
through the live pipeline, comparing per-dimension scores and verdict
labels across runs. Stability is defined as standard deviation <=10
points and no verdict label change across runs. See
`backend/validation/run_consistency_check.py` and its generated report
for full results.

### Dashboard example

*[Insert screenshot of the Dashboard tab here, showing stat cards, the
pie/bar/line charts, and applied filters, after running a representative
set of evaluations.]*

### PDF report example

*[Insert a screenshot or excerpt of a generated PDF report here.]*

## 7. Evaluation Analysis

Across validation runs, the system correctly distinguishes:
- Correct vs. factually wrong answers (Accuracy dimension)
- Grounded vs. fabricated claims (Hallucination dimension, including
  identifying the *specific* unsupported claim, not just a low score)
- On-topic vs. evasive/off-topic responses (Relevance dimension)
- Complete vs. partial answers (Completeness dimension)

The weighted final score and categorical verdict track these dimension
scores as expected — cases with a factual error or fabricated claim
reliably surface as "Needs Improvement" or "Fail" even when the response
is fluent and superficially plausible, which is the core value
proposition of the system: catching issues a casual read would miss.

## 8. Testing

A 22-test automated end-to-end suite (`backend/tests/test_e2e.py`) covers
single evaluation, batch evaluation, dashboard updates, report generation,
RAG retrieval, agent scoring, verdict generation, and both error handling
and invalid-input handling. 21 tests pass; 1 is skipped due to a
network-restricted test environment unrelated to application correctness.
Testing surfaced and led to the fix of one real defect (RAG retrieval
failures were not previously isolated from the rest of the evaluation
pipeline). Full detail in `backend/tests/E2E_TESTING_REPORT.md`.

## 9. Conclusion

This project delivers a complete, tested, end-to-end system for
automated AI response quality evaluation: five specialized judge agents,
RAG-grounded evaluation, single and batch workflows, persistent history,
an interactive dashboard, PDF reporting, and validated scoring
correctness and consistency. The architecture's central reliability
principle — graceful degradation rather than hard failure at every
LLM-dependent step — makes the system usable even under real-world
conditions like API rate limits or transient outages, which is a
meaningful outcome beyond just "the happy path works."

Future improvements identified for continued development include
multi-provider cross-checking to reduce single-model bias, smarter
document chunking for RAG, and scheduled automated consistency monitoring
over time. Full detail in `docs/TECHNICAL_DOCUMENTATION.md`, Section 15.
