from app.agents.base import BaseAgent

class HallucinationDetector(BaseAgent):
    system_prompt = (
        "You are the Hallucination Detection Agent in a multi-agent AI response evaluation "
        "system. Identify claims in the AI response that are NOT supported by the reference "
        "answer or retrieved context. A claim is a hallucination if it is fabricated, "
        "unverifiable, or contradicts the reference material. "
        "Score is a 'groundedness' score: 100 means fully supported / no hallucinations, "
        "0 means severely fabricated. "
        'Respond with ONLY a JSON object: {"score": <0-100 integer>, "reasoning": "<2-3 sentence explanation>", '
        '"flags": ["<specific unsupported claim 1>", "<specific unsupported claim 2>"]} '
        "The flags array should be empty if no unsupported claims are found."
    )
    def run(self, question, ai_response, reference_answer, retrieved_context):
        context_block = "\n---\n".join(retrieved_context) if retrieved_context else "(none retrieved)"
        payload = f"Question:\n{question}\n\nAI Response:\n{ai_response}\n\nReference Answer:\n{reference_answer or '(not provided)'}\n\nRetrieved Reference Context:\n{context_block}"
        result = self._call(payload)
        result.setdefault("flags", [])
        return result
