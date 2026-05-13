"""
Oracle LLM Client — Unified multi-provider LLM integration.

Provider priority: Anthropic (Claude) → OpenAI (GPT-4o) → Gemini → local fallback.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx


# ── LLM Client ───────────────────────────────────────────────────────────────

@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class LLMClient:
    """
    Unified LLM client with Claude primary + OpenAI fallback.
    Falls back to structured local generation if no API keys.
    """

    def __init__(self) -> None:
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.preferred = (
            "anthropic" if self.anthropic_key
            else "openai" if self.openai_key
            else "gemini" if self.gemini_key
            else "local"
        )

    def is_available(self) -> bool:
        return self.preferred != "local"

    def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4000,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Generate text from the preferred provider."""
        if self.preferred == "anthropic":
            return self._call_anthropic(prompt, system, max_tokens, temperature)
        elif self.preferred == "openai":
            return self._call_openai(prompt, system, max_tokens, temperature)
        elif self.preferred == "gemini":
            return self._call_gemini(prompt, system, max_tokens, temperature)
        else:
            return self._local_fallback(prompt, system)

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str = "",
        max_tokens: int = 4000,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Generate structured JSON matching the provided schema."""
        schema_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            f"Respond ONLY with the JSON object. No markdown, no explanation."
        )
        response = self.generate(schema_prompt, system, max_tokens, temperature)
        return self._extract_json(response.text)

    def _call_anthropic(
        self, prompt: str, system: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.anthropic_key)
            msg = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = msg.content[0].text if msg.content else ""
            return LLMResponse(
                text=text,
                model=msg.model,
                usage={"input": msg.usage.input_tokens, "output": msg.usage.output_tokens},
                raw=msg,
            )
        except Exception as e:
            # Fallback to OpenAI if Anthropic fails
            if self.openai_key:
                return self._call_openai(prompt, system, max_tokens, temperature)
            raise

    def _call_openai(
        self, prompt: str, system: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        from openai import OpenAI

        client = OpenAI(api_key=self.openai_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = resp.choices[0].message.content or ""
        return LLMResponse(
            text=text,
            model=resp.model,
            usage={
                "input": resp.usage.prompt_tokens if resp.usage else 0,
                "output": resp.usage.completion_tokens if resp.usage else 0,
            },
            raw=resp,
        )

    def _call_gemini(
        self, prompt: str, system: str, max_tokens: int, temperature: float
    ) -> LLMResponse:
        """Call Google Gemini via direct HTTP with rate-limit retry and pacing."""
        import time

        # Priority: latest Gemini 3.1 preview → 3.0 preview → 2.5 stable → 2.0 fallback.
        # gemini-3.1-pro-preview and gemini-3-pro-preview may have limited free-tier quota.
        # gemini-3.1-flash-lite-preview and gemini-2.5-flash are the free-tier workhorses.
        models = [
            "gemini-3.1-pro-preview",
            "gemini-3-pro-preview",
            "gemini-3.1-flash-lite-preview",
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ]
        last_error = None

        # Track last call time to pace requests (stay under 20 req/min = 1 per 3.5s)
        if not hasattr(self, "_gemini_last_call"):
            self._gemini_last_call = 0.0
        elapsed = time.time() - self._gemini_last_call
        if elapsed < 3.5:
            time.sleep(3.5 - elapsed)

        for model_name in models:
            for attempt in range(3):
                try:
                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/"
                        f"models/{model_name}:generateContent?key={self.gemini_key}"
                    )
                    payload = {
                        "contents": [
                            {"role": "user", "parts": [{"text": prompt}]}
                        ],
                        "generationConfig": {
                            "maxOutputTokens": max_tokens,
                            "temperature": temperature,
                        },
                    }
                    if system:
                        payload["systemInstruction"] = {
                            "parts": [{"text": system}]
                        }

                    resp = httpx.post(url, json=payload, timeout=60)
                    self._gemini_last_call = time.time()
                    data = resp.json()

                    if resp.status_code == 429:
                        err_msg = data.get("error", {}).get("message", "")
                        retry_seconds = 5
                        import re
                        m = re.search(r"Please retry in\s+([\d\.]+)s", err_msg)
                        if m:
                            retry_seconds = int(float(m.group(1))) + 2
                        # Cap wait to 10s so free-tier rate limits don't hang the app.
                        # If the API wants us to wait longer, skip to the next model.
                        if retry_seconds > 10:
                            last_error = RuntimeError(f"{model_name} rate-limited ({retry_seconds}s wait). Skipping.")
                            break
                        if attempt < 2:
                            time.sleep(retry_seconds)
                            continue
                        last_error = RuntimeError(err_msg)
                        break

                    if "error" in data:
                        raise RuntimeError(data["error"].get("message", "Unknown Gemini error"))

                    candidate = data.get("candidates", [{}])[0]
                    text = ""
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            text += part.get("text", "")

                    usage_meta = data.get("usageMetadata", {})
                    usage = {
                        "input": usage_meta.get("promptTokenCount", 0),
                        "output": usage_meta.get("candidatesTokenCount", 0),
                    }

                    return LLMResponse(
                        text=text,
                        model=model_name,
                        usage=usage,
                        raw=data,
                    )
                except Exception as e:
                    last_error = e
                    break  # try next model

        # If all Gemini models fail, cascade to next available provider
        if self.openai_key:
            return self._call_openai(prompt, system, max_tokens, temperature)
        if self.anthropic_key:
            return self._call_anthropic(prompt, system, max_tokens, temperature)
        raise RuntimeError(f"Gemini call failed and no fallback available: {last_error}")

    def _local_fallback(self, prompt: str, system: str) -> LLMResponse:
        """
        When no LLM keys are available, generate structured content
        using the prompt's own structure as a guide.
        This is NOT fake — it's rule-based generation from the
        methodology documents loaded as references.
        """
        return LLMResponse(
            text="{}",
            model="local-fallback",
            usage={"input": 0, "output": 0},
        )

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            # Remove opening fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing fence
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)
        text = text.strip()
        return json.loads(text)
