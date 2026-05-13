"""
Oracle LLM Client v2 — Multi-modal with Gemini native video.

Provider priority: Gemini 2.5 Pro (video) → Gemini 3.1 Pro (text/reasoning) → fallback
Uses Google's official genai SDK for video uploads.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import google.generativeai as genai
import httpx


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class LLMClientV2:
    """
    Unified LLM client with Gemini native video support.
    
    Text/reasoning: Gemini 3.1 Pro Preview
    Video analysis: Gemini 2.5 Pro Preview
    Fallback: Gemini 2.5 Flash
    """

    TEXT_MODEL = "gemini-3.1-pro-preview"
    VIDEO_MODEL = "gemini-2.5-pro-preview"
    FALLBACK_MODEL = "gemini-2.5-flash"

    def __init__(self) -> None:
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.text_model = self.TEXT_MODEL
        self.video_model = self.VIDEO_MODEL
        self.fallback_model = self.FALLBACK_MODEL
        
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 4000,
        temperature: float = 0.3,
        model: str | None = None,
    ) -> LLMResponse:
        """Generate text. Defaults to Gemini 3.1 Pro for reasoning."""
        model_name = model or self.text_model
        return self._call_gemini_text(prompt, system, max_tokens, temperature, model_name)

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system: str = "",
        max_tokens: int = 4000,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Generate structured JSON."""
        schema_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond with valid JSON matching this schema:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            f"Respond ONLY with the JSON object. No markdown, no explanation."
        )
        response = self.generate(schema_prompt, system, max_tokens, temperature, model)
        return self._extract_json(response.text)

    def analyze_video(
        self,
        video_path: Path,
        prompt: str,
        system: str = "",
        max_tokens: int = 8000,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """
        Upload a video to Gemini 2.5 Pro and analyze it natively.
        Gemini sees motion, facial expressions, voice, body language in one pass.
        """
        if not self.api_key:
            raise RuntimeError("No Gemini API key available")
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Upload video via genai SDK
        video_file = genai.upload_file(str(video_path), mime_type="video/mp4")
        
        model = genai.GenerativeModel(
            model_name=self.video_model,
            system_instruction=system or None,
        )
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
        )
        
        response = model.generate_content(
            [video_file, prompt],
            generation_config=generation_config,
        )
        
        # Clean up uploaded file
        try:
            genai.delete_file(video_file.name)
        except Exception:
            pass
        
        text = response.text if response and response.text else ""
        return LLMResponse(
            text=text,
            model=self.video_model,
            usage={"input": 0, "output": 0},  # Gemini SDK doesn't expose usage easily
            raw=response,
        )

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding using Gemini embedding model."""
        if not self.api_key:
            raise RuntimeError("No Gemini API key available")
        
        model = genai.GenerativeModel("models/text-embedding-004")
        result = model.embed_content(
            content=text,
            task_type="retrieval_document",
        )
        return result.embedding

    def _call_gemini_text(
        self,
        prompt: str,
        system: str,
        max_tokens: int,
        temperature: float,
        model_name: str,
    ) -> LLMResponse:
        """Call Gemini via direct HTTP (more reliable than SDK for text)."""
        if not self.api_key:
            raise RuntimeError("No Gemini API key available")

        # Try primary model, fall back if rate limited
        models_to_try = [model_name, self.fallback_model]
        last_error = None

        for m in models_to_try:
            try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/"
                    f"models/{m}:generateContent?key={self.api_key}"
                )
                payload: dict[str, Any] = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature,
                    },
                }
                if system:
                    payload["systemInstruction"] = {"parts": [{"text": system}]}

                resp = httpx.post(url, json=payload, timeout=120)
                data = resp.json()

                if "error" in data:
                    err_msg = data["error"].get("message", "Unknown Gemini error")
                    if "429" in str(data["error"].get("code", "")) or "quota" in err_msg.lower():
                        last_error = RuntimeError(err_msg)
                        continue
                    raise RuntimeError(err_msg)

                candidate = data.get("candidates", [{}])[0]
                text = ""
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        text += part.get("text", "")

                usage_meta = data.get("usageMetadata", {})
                return LLMResponse(
                    text=text,
                    model=m,
                    usage={
                        "input": usage_meta.get("promptTokenCount", 0),
                        "output": usage_meta.get("candidatesTokenCount", 0),
                    },
                    raw=data,
                )
            except Exception as e:
                last_error = e
                continue

        raise RuntimeError(f"All Gemini models failed: {last_error}")

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines)
        text = text.strip()
        return json.loads(text)
