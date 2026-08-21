from app.agents.base import BaseAgent

WEIGHTS = {"relevance": 0.20, "accuracy": 0.35, "hallucination": 0.25, "completeness": 0.20}
PASS_THRESHOLD = 75
NEEDS_IMPROVEMENT_THRESHOLD = 45

class VerdictAgent(BaseAgent):
    system_prompt = (
        "You are the Verdict Agent in a multi-agent AI response evaluation system. You are "
        "given the scores and reasoning produced by four judge agents (Relevance, Accuracy, "
        "Hallucination/Groundedness, Completeness), a pre-computed weighted final score, and "
        "a categorical verdict label (Pass, Needs Improvement, or Fail). "
        "Write a short, decisive overall verdict summary (2-4 sentences) that a human reader "
        "can use to quickly understand whether the AI response is trustworthy, consistent "
        "with the given label. "
        'Respond with ONLY a JSON object: {"verdict": "<summary>"}'
    )

    @staticmethod
    def compute_final_score(relevance, accuracy, hallucination, completeness) -> float:
        return round(relevance * WEIGHTS["relevance"] + accuracy * WEIGHTS["accuracy"] + hallucination * WEIGHTS["hallucination"] + completeness * WEIGHTS["completeness"], 2)

    @staticmethod
    def compute_label(final_score: float) -> str:
        if final_score >= PASS_THRESHOLD:
            return "Pass"
        if final_score >= NEEDS_IMPROVEMENT_THRESHOLD:
            return "Needs Improvement"
        return "Fail"

    def run(self, dimension_results: dict, final_score: float, verdict_label: str) -> dict:
        payload = (
            f"Relevance: score={dimension_results['relevance']['score']}, reasoning={dimension_results['relevance']['reasoning']}\n\n"
            f"Accuracy: score={dimension_results['accuracy']['score']}, reasoning={dimension_results['accuracy']['reasoning']}\n\n"
            f"Hallucination/Groundedness: score={dimension_results['hallucination']['score']}, reasoning={dimension_results['hallucination']['reasoning']}, flags={dimension_results['hallucination'].get('flags', [])}\n\n"
            f"Completeness: score={dimension_results['completeness']['score']}, reasoning={dimension_results['completeness']['reasoning']}\n\n"
            f"Weighted Final Score: {final_score}/100\nVerdict Label: {verdict_label}"
        )
        return self._call(payload, max_tokens=300)
