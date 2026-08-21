# Agile Development Documentation

**Project:** Development of AI Response Validation System with Hallucination Detection Assistance
**Team:** Group 1
**Methodology:** Milestone-driven Agile (Scrum-inspired), 4 sprints, each with mentor review as the sprint demo/retrospective gate

> Formal Agile documentation in the mentor's template format (Product
> Backlog, Sprint Backlog, Stand-up log, Retrospectives, Defect Tracker,
> Unit Test Plan) lives in [`agile_docs/`](./agile_docs) as Excel files.
> This document is the readable narrative version of the same sprints.

---

## 1. Agile Approach

Development was organized as four sequential sprints, each ending in a
mentor review that served as both the **Sprint Review** (demo working
software) and **Sprint Retrospective** (assess what's done, what's not,
what to adjust). Each sprint had a defined goal, a backlog of user
stories, and concrete, demoable deliverables — consistent with Agile's
core principle of shipping working software incrementally rather than
a single big-bang delivery at the end.

## 2. Product Backlog (Full Epic List)

| Epic | Priority | Sprint |
|---|---|---|
| Core evaluation agents (Relevance, Accuracy, Hallucination) | High | 2 |
| Benchmark validation against real datasets | High | 2 |
| Completeness agent + weighted Verdict agent | High | 3 |
| Results interface (per-dimension display) | High | 3 |
| Batch (CSV) evaluation | Medium | 3 |
| Scoring dashboard with filters & trends | High | 4 |
| PDF report export | Medium | 4 |
| End-to-end automated testing | High | 4 |
| Scoring consistency validation | Medium | 4 |
| Technical documentation & project report | High | 4 |

## 3. Sprint Breakdown

### Sprint 1 — Foundation & Prototype
**Sprint Goal:** Stand up a working single-user evaluation prototype end-to-end.

User Stories:
- As a developer, I need a basic FastAPI + React scaffold so subsequent features have a foundation.
- As a user, I want to submit a question and AI response and get some evaluation output, even if crude.

Sprint outcome: Working single-agent prototype, initial UI shell, LLM
backend selection (iterated through Claude API, then Ollama, then Gemini,
then Groq based on availability/cost/reliability constraints discovered
during the sprint — an example of Agile's adapt-as-you-learn principle
in practice).

---

### Sprint 2 — Core Judge Agents (10 Jul - 21 Jul)
**Sprint Goal:** Build and validate the first three evaluation agents.

| User Story | Acceptance Criteria | Status |
|---|---|---|
| As a user, I want a Relevance score for my AI response so I know if it's on-topic. | Score 0-100 + reasoning returned per evaluation | Done |
| As a user, I want an Accuracy score checked against a reference answer. | Score + reasoning, checks against reference/RAG context | Done |
| As a user, I want hallucinated claims flagged specifically, not just scored. | Specific unsupported claims listed, not just a number | Done |
| As a QA reviewer, I want proof the agents score consistently across varied inputs. | Validated against 20 real TruthfulQA/SQuAD cases | Done |

**Sprint Review:** Demoed all three agents scoring real benchmark
questions with correct directional behavior (rewarding correct answers,
penalizing wrong/fabricated ones).

**Retrospective notes:** LLM backend instability (API key issues, rate
limits) was the biggest blocker, addressed by building a fallback
heuristic scorer so the pipeline never hard-fails, a pattern carried
into all future sprints.

---

### Sprint 3 — Aggregation, Interface, Batch Mode
**Sprint Goal:** Turn four independent scores into one usable verdict, and support evaluating many responses at once.

| User Story | Acceptance Criteria | Status |
|---|---|---|
| As a user, I want a Completeness score identifying what's missing from an answer. | Score + specific omissions named | Done |
| As a user, I want one overall verdict, not four separate numbers to interpret myself. | Weighted final score + Pass/Needs Improvement/Fail label | Done |
| As a user, I want a clean results screen showing everything: scores, reasoning, flags, verdict. | All 9 required interface components present | Done |
| As a user, I want to evaluate many Q&A pairs at once instead of one at a time. | CSV upload, background job, progress, results table | Done |

**Sprint Review:** Live demo of a single evaluation end-to-end and a
batch CSV upload with expandable per-row detail.

**Retrospective notes:** Initial batch table was missing 3 required
interface fields (full response, hallucination findings, reasoning),
caught during review, fixed with expandable rows before sign-off. Good
example of the review step catching a real gap before it reached "done."

---

### Sprint 4 — Observability, Reliability, Proof (Milestone 4)
**Sprint Goal:** Move from "the system works" to "the system is provably reliable and reportable."

| User Story | Acceptance Criteria | Status |
|---|---|---|
| As a manager, I want a dashboard showing pass/fail rates and trends across all evaluations. | Stat cards, pie/bar/line charts, filters | Done |
| As a manager, I want to export results as a shareable PDF. | Structured PDF: summary, flagged responses, recommendations | Done |
| As a QA engineer, I want automated tests proving every workflow actually works. | 22 tests covering all required areas | Done (21/22 pass, 1 environment-skip) |
| As a QA engineer, I want proof the same input scores consistently across repeated runs. | Consistency validation script + report | Built (requires a live run against a real API key) |
| As a mentor, I want full technical and project documentation. | All required sections present | Done |

**Sprint Review:** Full walkthrough: single eval, batch, dashboard, PDF
export, testing results.

**Retrospective notes:** End-to-end testing surfaced a real bug (RAG
retrieval failures weren't isolated from the rest of the pipeline),
fixed and re-verified within the same sprint. This is the sprint's
clearest example of Agile testing paying for itself: the bug was found
and closed before it ever reached a user.

---

## 4. Tools & Practices

- **Version control:** Git / GitHub
- **Review cadence:** Milestone-end mentor review acting as sprint review + retrospective
- **Definition of Done:** A feature is "done" when it is (1) implemented, (2) manually or automatically tested, (3) demoed working end-to-end, not just code-complete
- **Backlog prioritization:** High-priority items (core scoring correctness, reliability/fallback behavior) were consistently pulled ahead of nice-to-have polish, reflecting Agile's value-first prioritization
