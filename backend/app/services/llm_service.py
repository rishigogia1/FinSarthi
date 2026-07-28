"""
services/llm_service.py — Unified abstraction for LLM providers (Gemini, OpenAI, Claude, Ollama).

Handles API requests, timeouts, and multi-turn message formatting.
"""
import logging
import time
import httpx
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Exception raised for LLM API failures."""
    pass


class LLMService:
    @staticmethod
    async def generate(
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: float = 30.0
    ) -> dict[str, Any]:
        """
        Send a conversation history to the configured LLM provider and get a response.
        
        Args:
            messages: List of dicts with 'role' ('system', 'user', 'assistant') and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            timeout: Request timeout in seconds.
            
        Returns:
            dict with 'content' (the text response), 'model' (model used), and 'latency_ms'.
        """
        provider = settings.LLM_PROVIDER
        start_time = time.perf_counter()
        
        req_char_count = sum(len(m.get("content", "")) for m in messages)
        est_tokens = req_char_count // 4
        
        logger.info(
            "[LLM TELEMETRY] provider=%s, history_len=%d, total_chars=%d, est_tokens=%d",
            provider, len(messages), req_char_count, est_tokens
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if provider == "openai":
                    result = await LLMService._call_openai(client, messages, temperature, max_tokens)
                    model = settings.OPENAI_MODEL
                elif provider == "gemini":
                    result = await LLMService._call_gemini(client, messages, temperature, max_tokens)
                    model = settings.GEMINI_MODEL
                elif provider == "ollama":
                    result = await LLMService._call_ollama(client, messages, temperature, max_tokens)
                    model = settings.OLLAMA_MODEL
                elif provider == "claude":
                    result = await LLMService._call_claude(client, messages, temperature, max_tokens)
                    model = settings.CLAUDE_MODEL
                else:
                    raise LLMError(f"Unsupported LLM provider: {provider}")
                    
        except httpx.HTTPStatusError as e:
            latency = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "[LLM TELEMETRY FAILURE] provider=%s, status=%d, latency_ms=%.2fms, error=%s",
                provider, e.response.status_code, latency, e
            )
            raise LLMError(f"LLM API returned {e.response.status_code}") from e
        except Exception as e:
            latency = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "[LLM TELEMETRY FAILURE] provider=%s, latency_ms=%.2fms, error=%s",
                provider, latency, e
            )
            raise LLMError(str(e)) from e

        latency = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "[LLM TELEMETRY SUCCESS] provider=%s, model=%s, latency_ms=%.2fms",
            provider, model, latency
        )
        
        return {
            "content": result.strip(),
            "model": model,
            "latency_ms": latency,
            "provider": provider
        }

    @staticmethod
    async def _call_openai(client: httpx.AsyncClient, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    @staticmethod
    async def _call_gemini(
        client: httpx.AsyncClient,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> str:
        eff_temperature = settings.GEMINI_TEMPERATURE if temperature is None else temperature
        eff_max_tokens = settings.GEMINI_MAX_TOKENS if max_tokens is None else max_tokens

        # Convert standard roles to Gemini format
        contents = []
        system_instruction = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction += msg["content"] + "\n"
            else:
                # Gemini uses 'user' and 'model'
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
                
        data = {
            "contents": contents,
            "generationConfig": {
                "temperature": eff_temperature,
                "maxOutputTokens": eff_max_tokens
            }
        }
        if system_instruction:
            data["system_instruction"] = {"parts": [{"text": system_instruction.strip()}]}
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        response = await client.post(url, json=data)
        response.raise_for_status()
        
        res_json = response.json()
        if "candidates" not in res_json or not res_json["candidates"]:
            raise LLMError(f"Gemini returned no candidates. Raw response: {res_json}")
            
        return res_json["candidates"][0]["content"]["parts"][0]["text"]

    @staticmethod
    async def _call_ollama(client: httpx.AsyncClient, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"
        data = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        response = await client.post(url, json=data)
        response.raise_for_status()
        return response.json()["message"]["content"]

    @staticmethod
    async def _call_claude(client: httpx.AsyncClient, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
        system_content = ""
        filtered_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_content += msg["content"] + "\n"
            else:
                filtered_messages.append(msg)
                
        headers = {
            "x-api-key": settings.CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        data = {
            "model": settings.CLAUDE_MODEL,
            "messages": filtered_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system_content:
            data["system"] = system_content.strip()
            
        response = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["content"][0]["text"]
