import logging
from typing import List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_EMBEDDING_MODEL

    async def embed(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model, "prompt": text}

        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["embedding"]
            except Exception as exc:
                logger.error("Ollama embedding API error: %s", exc)
                raise


embedding_client = EmbeddingClient()
