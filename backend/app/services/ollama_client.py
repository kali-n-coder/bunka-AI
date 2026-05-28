import json
import logging
from typing import AsyncGenerator, Dict, List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _ollama_timeout():
    return httpx.Timeout(
        settings.OLLAMA_TIMEOUT_SECONDS,
        connect=10.0,
        read=settings.OLLAMA_TIMEOUT_SECONDS,
        write=30.0,
    )


class OllamaClient:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL

    async def chat(self, messages: List[Dict[str, str]], stream: bool = False):
        chat_url = f"{self.base_url}/api/chat"
        chat_payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream
        }

        if not stream:
            async with httpx.AsyncClient(timeout=_ollama_timeout()) as client:
                try:
                    response = await client.post(chat_url, json=chat_payload)
                    if response.status_code == 404:
                        return await self._generate(client, messages)
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    logger.error("Ollama API error: %r", e)
                    raise
        else:
            return self._chat_stream(chat_url, chat_payload, messages)

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        labels = {
            "system": "System",
            "user": "User",
            "assistant": "Assistant",
        }
        lines = []
        for message in messages:
            role = labels.get(message.get("role", "user"), "User")
            lines.append(f"{role}: {message.get('content', '')}")
        lines.append("Assistant:")
        return "\n\n".join(lines)

    async def _generate(self, client: httpx.AsyncClient, messages: List[Dict[str, str]]):
        response = await client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": self._messages_to_prompt(messages),
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return {"message": {"content": data.get("response", "")}, "done": data.get("done", True)}

    async def _chat_stream(
        self,
        url: str,
        payload: Dict,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=_ollama_timeout()) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code == 404:
                    async for chunk in self._generate_stream(client, messages):
                        yield chunk
                    return
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue

    async def _generate_stream(
        self,
        client: httpx.AsyncClient,
        messages: List[Dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        async with client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": self._messages_to_prompt(messages),
                "stream": True,
            },
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

ollama_client = OllamaClient()
