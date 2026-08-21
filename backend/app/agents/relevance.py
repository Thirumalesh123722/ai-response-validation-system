from app.agents.base import BaseAgent

class RelevanceJudge(BaseAgent):
    system_prompt = (
        "You are the Relevance Judge in a multi-agent AI response evaluation system. "
        "Determine how well the AI response addresses the given question, ignoring "
        "factual correctness (that is scored elsewhere). "
        'Respond with ONLY a JSON object: {"score": <0-100 integer>, "reasoning": "<2-3 sentence explanation>"}'
    )
    def run(self, question: str, ai_response: str) -> dict:
        payload = f"Question:\n{question}\n\nAI Response:\n{ai_response}"
        return self._call(payload)
