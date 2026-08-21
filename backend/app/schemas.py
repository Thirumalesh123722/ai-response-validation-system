from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EvaluationRequest(BaseModel):
    question: str = Field(..., min_length=1)
    ai_response: str = Field(..., min_length=1)
    reference_answer: Optional[str] = None
    source_document_id: Optional[str] = None
    system_name: str = "Unspecified"
    dataset_name: Optional[str] = None


class DimensionResult(BaseModel):
    score: float
    reasoning: str
    flags: list[str] = []


class EvaluationResult(BaseModel):
    relevance_score: float
    accuracy_score: float
    hallucination_score: float
    completeness_score: float
    final_score: float
    verdict_label: str
    verdict: str
    relevance_reasoning: str
    accuracy_reasoning: str
    hallucination_reasoning: str
    completeness_reasoning: str
    hallucination_flags: list[str] = []
    retrieved_context: list[str] = []


class IngestResponse(BaseModel):
    document_id: str
    chunks_indexed: int


class BatchRowResult(BaseModel):
    row_index: int
    question: str
    ai_response: str
    result: Optional[EvaluationResult] = None
    error: Optional[str] = None


class BatchJobStatus(BaseModel):
    job_id: str
    status: str
    total: int
    completed: int
    rows: list[BatchRowResult] = []


class DashboardSummary(BaseModel):
    total_evaluations: int
    verdict_counts: dict[str, int]
    avg_relevance: float
    avg_accuracy: float
    avg_hallucination: float
    avg_completeness: float
    avg_final_score: float
    hallucination_frequency_pct: float
    quality_trend: list[dict]
    available_systems: list[str]
    available_datasets: list[str]


class EvaluationRecord(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    id: str
    created_at: str
    mode: str
    batch_job_id: Optional[str] = None
    system_name: str
    dataset_name: Optional[str] = None
    question: str
    ai_response: str
    reference_answer: Optional[str] = None
    relevance_score: float
    accuracy_score: float
    hallucination_score: float
    completeness_score: float
    final_score: float
    verdict_label: str
    verdict_reasoning: str
    relevance_reasoning: str
    accuracy_reasoning: str
    hallucination_reasoning: str
    completeness_reasoning: str
    hallucination_flags: list[str]
    model_used: str
