import re

DISCLAIMER = " [Fallback heuristic used — AI judging API was unavailable for this call.]"

def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", (text or "").lower()))

def _overlap_score(a: str, b: str, base: float = 45.0, spread: float = 45.0) -> float:
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return round(base, 1)
    jaccard = len(wa & wb) / len(wa | wb)
    return round(min(100.0, base + jaccard * spread * 2), 1)

def fallback_relevance(question, ai_response):
    return {"score": _overlap_score(question, ai_response), "reasoning": "Estimated from keyword overlap between the question and response." + DISCLAIMER}

def fallback_accuracy(ai_response, reference_answer, context):
    ref_text = reference_answer or " ".join(context)
    score = _overlap_score(ai_response, ref_text) if ref_text.strip() else 55.0
    return {"score": score, "reasoning": "Estimated from overlap between the response and available reference material (no real fact-checking was performed)." + DISCLAIMER}

def fallback_hallucination(ai_response, reference_answer, context):
    ref_text = reference_answer or " ".join(context)
    score = _overlap_score(ai_response, ref_text) if ref_text.strip() else 55.0
    return {"score": score, "reasoning": "Groundedness estimated from vocabulary overlap with reference material; no claim-level fact verification was performed." + DISCLAIMER, "flags": []}

def fallback_completeness(ai_response, reference_answer, context):
    ref_text = reference_answer or " ".join(context)
    score = _overlap_score(ai_response, ref_text, base=50.0) if ref_text.strip() else 60.0
    return {"score": score, "reasoning": "Estimated from how much of the reference material's vocabulary is reflected in the response." + DISCLAIMER}

def fallback_verdict(final_score, verdict_label):
    return {"verdict": f"Verdict: {verdict_label} (weighted score {final_score}/100), computed from fallback heuristic scoring because the AI judging API was unavailable for this evaluation. This is not a genuine AI-judged result — check backend/.env and /health once the API key is working to get real scores."}
