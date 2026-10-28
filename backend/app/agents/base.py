import json
import logging
import re
import time
import httpx

from app.config import settings

logger = logging.getLogger("agents.base")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Fallback model chain — if the configured model is unavailable we try alternatives.
FALLBACK_MODELS = [
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "llama-3.1-70b-versatile",
]


class BaseAgent:
    system_prompt: str = ""

    def _call(self, user_content: str, max_tokens: int = 1024, max_retries: int = 4) -> dict:
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to backend/.env "
                "(get one free at https://console.groq.com/keys)."
            )

        # Build the ordered list of models to try: configured model first, then fallbacks.
        models_to_try = [settings.groq_model]
        for m in FALLBACK_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        last_error = None

        for model in models_to_try:
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
                "max_tokens": max_tokens,
            }

            for attempt in range(max_retries):
                try:
                    response = httpx.post(
                        GROQ_URL,
                        headers=headers,
                        json=body,
                        timeout=settings.groq_timeout,
                    )
                except httpx.TimeoutException as exc:
                    last_error = exc
                    logger.warning(
                        "Groq API timeout (model=%s, attempt=%d/%d): %s",
                        model, attempt + 1, max_retries, exc,
                    )
                    time.sleep(2 * (2 ** attempt))
                    continue
                except httpx.HTTPError as exc:
                    last_error = exc
                    logger.warning(
                        "Groq API network error (model=%s, attempt=%d/%d): %s",
                        model, attempt + 1, max_retries, exc,
                    )
                    time.sleep(2 * (2 ** attempt))
                    continue

                # --- Rate limited ---
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else (2 * (2 ** attempt))
                    last_error = httpx.HTTPStatusError(
                        f"429 rate limited (model={model}, attempt {attempt + 1}/{max_retries}): "
                        f"{response.text[:500]}",
                        request=response.request,
                        response=response,
                    )
                    logger.warning(
                        "Groq 429 rate limited (model=%s, attempt=%d/%d), waiting %.1fs",
                        model, attempt + 1, max_retries, wait,
                    )
                    time.sleep(wait)
                    continue

                # --- Model not found / unavailable → try next model ---
                if response.status_code == 404:
                    logger.warning(
                        "Groq model '%s' not found (404), trying next model", model
                    )
                    last_error = httpx.HTTPStatusError(
                        f"Model {model} not found",
                        request=response.request,
                        response=response,
                    )
                    break  # break retry loop, move to next model

                # --- Auth error — no point retrying ---
                if response.status_code in (401, 403):
                    detail = response.text[:500]
                    logger.error("Groq auth error (%d): %s", response.status_code, detail)
                    raise RuntimeError(
                        f"Groq API authentication failed ({response.status_code}). "
                        f"Check your GROQ_API_KEY. Detail: {detail}"
                    )

                # --- Other server error → retry ---
                if response.status_code >= 500:
                    last_error = httpx.HTTPStatusError(
                        f"Groq server error {response.status_code}: {response.text[:300]}",
                        request=response.request,
                        response=response,
                    )
                    logger.warning(
                        "Groq server error %d (model=%s, attempt=%d/%d)",
                        response.status_code, model, attempt + 1, max_retries,
                    )
                    time.sleep(2 * (2 ** attempt))
                    continue

                # --- Any other non-2xx ---
                try:
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    last_error = exc
                    logger.warning(
                        "Groq unexpected status %d (model=%s): %s",
                        response.status_code, model, response.text[:300],
                    )
                    break  # try next model

                # --- Success ---
                data = response.json()
                try:
                    text = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    raise ValueError(f"Unexpected Groq response shape: {data}")

                if model != settings.groq_model:
                    logger.info(
                        "Groq call succeeded with fallback model '%s' "
                        "(configured model '%s' was unavailable)",
                        model, settings.groq_model,
                    )
                return self._parse_json(text)

        # All models and retries exhausted
        raise RuntimeError(
            f"All Groq API attempts failed. Last error: {last_error}"
        )

    @staticmethod
    def _parse_json(text: str) -> dict:
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*|\s*```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Agent did not return valid JSON: {text[:200]}")
