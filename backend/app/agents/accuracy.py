from app.agents.base import BaseAgent

class AccuracyJudge(BaseAgent):
    system_prompt = (
        "You are the Accuracy Judge in a multi-agent AI response evaluation system. "
        "Verify the factual correctness of the AI response against the provided reference "
        "material (reference answer and/or retrieved context). If no reference material is "
        "provided, judge correctness based on well-established general knowledge and say so "
        "in your reasoning. "
        'Respond with ONLY a JSON object: {"score": <0-100 integer>, "reasoning": "<2-3 sentence explanation citing specific discrepancies if any>"}'
    )
    def run(self, question, ai_response, reference_answer, retrieved_context):
        context_block = "\n---\n".join(retrieved_context) if retrieved_context else "(none retrieved)"
        payload = f"Question:\n{question}\n\nAI Response:\n{ai_response}\n\nReference Answer:\n{reference_answer or '(not provided)'}\n\nRetrieved Reference Context:\n{context_block}"
        return self._call(payload)
