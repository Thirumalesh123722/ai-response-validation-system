import json
import re
import time
import httpx

from app.config import settings

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class BaseAgent:
    system_prompt: str = ""

    def _call(self, user_content: str, max_tokens: int = 1024, max_retries: int = 4) -> dict:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set. Add it to backend/.env (get one at https://console.groq.com/keys).")

        headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}
        body = {
            "model": settings.groq_model,
            "messages": [{"role": "system", "content": self.system_prompt}, {"role": "user", "content": user_content}],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }

        last_error = None
        for attempt in range(max_retries):
            response = httpx.post(GROQ_URL, headers=headers, json=body, timeout=60)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else (2 * (2 ** attempt))
                last_error = httpx.HTTPStatusError(f"429 rate limited (attempt {attempt + 1}/{max_retries}): {response.text[:500]}", request=response.request, response=response)
                time.sleep(wait)
                continue
            response.raise_for_status()
            data = response.json()
            try:
                text = data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise ValueError(f"Unexpected Groq response shape: {data}")
            return self._parse_json(text)
        raise last_error

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
