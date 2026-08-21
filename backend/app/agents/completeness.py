from app.agents.base import BaseAgent

class CompletenessJudge(BaseAgent):
    system_prompt = (
        "You are the Completeness Judge in a multi-agent AI response evaluation system. "
        "Determine whether the AI response adequately covers everything the question asks "
        "for, and whether it covers the key points present in the reference answer or "
        "retrieved context (if provided). Identify specific omissions if any exist. "
        'Respond with ONLY a JSON object: {"score": <0-100 integer>, "reasoning": "<2-3 sentence explanation of what, if anything, is missing>"}'
    )
    def run(self, question, ai_response, reference_answer, retrieved_context):
        context_block = "\n---\n".join(retrieved_context) if retrieved_context else "(none retrieved)"
        payload = f"Question:\n{question}\n\nAI Response:\n{ai_response}\n\nReference Answer:\n{reference_answer or '(not provided)'}\n\nRetrieved Reference Context:\n{context_block}"
        return self._call(payload)
