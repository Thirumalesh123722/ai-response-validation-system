import logging
import time

from app.agents.relevance import RelevanceJudge
from app.agents.accuracy import AccuracyJudge
from app.agents.hallucination import HallucinationDetector
from app.agents.completeness import CompletenessJudge
from app.agents.verdict import VerdictAgent
from app.agents import fallback
from app.config import settings
from app.rag.chroma_store import knowledge_base
from app.schemas import EvaluationRequest, EvaluationResult

logger = logging.getLogger("orchestrator")

relevance_judge = RelevanceJudge()
accuracy_judge = AccuracyJudge()
hallucination_detector = HallucinationDetector()
completeness_judge = CompletenessJudge()
verdict_agent = VerdictAgent()


def _run_safely(name, agent_call, fallback_call):
    try:
        result = agent_call()
        logger.info("Agent '%s' succeeded via Groq API", name)
        return result
    except Exception as exc:
        logger.exception(
            "Agent '%s' failed with %s: %s — using fallback heuristic",
            name, type(exc).__name__, exc,
        )
        return fallback_call()


def _retrieve_context_safely(req: EvaluationRequest) -> list[str]:
    try:
        if req.source_document_id:
            return knowledge_base.query(query_text=req.question, document_id=req.source_document_id, n_results=5)
        elif req.reference_answer is None:
            return knowledge_base.query(query_text=req.question, n_results=3)
        return []
    except Exception:
        logger.exception("RAG retrieval failed, continuing without retrieved context")
        return []


def run_evaluation(req: EvaluationRequest) -> EvaluationResult:
    retrieved_context: list[str] = _retrieve_context_safely(req)
    delay = settings.groq_inter_call_delay

    relevance = _run_safely("relevance", lambda: relevance_judge.run(req.question, req.ai_response), lambda: fallback.fallback_relevance(req.question, req.ai_response))
    time.sleep(delay)
    accuracy = _run_safely("accuracy", lambda: accuracy_judge.run(req.question, req.ai_response, req.reference_answer, retrieved_context), lambda: fallback.fallback_accuracy(req.ai_response, req.reference_answer, retrieved_context))
    time.sleep(delay)
    hallucination = _run_safely("hallucination", lambda: hallucination_detector.run(req.question, req.ai_response, req.reference_answer, retrieved_context), lambda: fallback.fallback_hallucination(req.ai_response, req.reference_answer, retrieved_context))
    time.sleep(delay)
    completeness = _run_safely("completeness", lambda: completeness_judge.run(req.question, req.ai_response, req.reference_answer, retrieved_context), lambda: fallback.fallback_completeness(req.ai_response, req.reference_answer, retrieved_context))
    time.sleep(delay)

    dimension_results = {"relevance": relevance, "accuracy": accuracy, "hallucination": hallucination, "completeness": completeness}

    final_score = VerdictAgent.compute_final_score(relevance["score"], accuracy["score"], hallucination["score"], completeness["score"])
    verdict_label = VerdictAgent.compute_label(final_score)

    verdict = _run_safely("verdict", lambda: verdict_agent.run(dimension_results, final_score, verdict_label), lambda: fallback.fallback_verdict(final_score, verdict_label))

    return EvaluationResult(
        relevance_score=relevance["score"], accuracy_score=accuracy["score"],
        hallucination_score=hallucination["score"], completeness_score=completeness["score"],
        final_score=final_score, verdict_label=verdict_label, verdict=verdict["verdict"],
        relevance_reasoning=relevance["reasoning"], accuracy_reasoning=accuracy["reasoning"],
        hallucination_reasoning=hallucination["reasoning"], completeness_reasoning=completeness["reasoning"],
        hallucination_flags=hallucination.get("flags", []), retrieved_context=retrieved_context,
    )
