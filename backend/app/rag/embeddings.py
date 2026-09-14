import math
import hashlib
import httpx
from typing import List, Optional
from app.core.config import settings
from app.core.logs import logger


class EmbeddingService:
    """
    Embedding service interfacing with Ollama embedding API with fast local fallback.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        dimension: int = 768
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.dimension = dimension or getattr(settings, "EMBEDDING_DIM", 768)
        self._checked_ollama = False
        self._ollama_available = False
        self._endpoint_type = "embeddings"  # "embeddings" or "embed"

    def _probe_ollama(self):
        """Check once whether Ollama embedding model is available."""
        if self._checked_ollama:
            return
        self._checked_ollama = True
        try:
            # Check /api/embeddings
            url = f"{self.base_url}/api/embeddings"
            payload = {"model": self.model, "prompt": "health test"}
            with httpx.Client(timeout=2.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200 and "embedding" in resp.json():
                    self._ollama_available = True
                    self._endpoint_type = "embeddings"
                    logger.info(f"Ollama embedding active using model '{self.model}' (/api/embeddings)")
                    return

            # Check /api/embed
            url = f"{self.base_url}/api/embed"
            payload = {"model": self.model, "input": "health test"}
            with httpx.Client(timeout=2.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200 and "embeddings" in resp.json():
                    self._ollama_available = True
                    self._endpoint_type = "embed"
                    logger.info(f"Ollama embedding active using model '{self.model}' (/api/embed)")
                    return
        except Exception as e:
            logger.debug(f"Ollama embedding probe error: {e}")

        logger.info(f"Ollama embedding model '{self.model}' not found or unreachable. Using dense semantic vector fallback.")
        self._ollama_available = False

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Deterministic, hash-based bag-of-words / n-gram dense embedding.
        Ensures unit L2 norm and semantic overlap for token matches when Ollama is offline.
        """
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            val = ((h >> 8) % 1000) / 1000.0 - 0.5
            vec[idx] += val

            # Character 3-grams
            for i in range(len(word) - 2):
                gram = word[i:i+3]
                gh = int(hashlib.md5(gram.encode("utf-8")).hexdigest(), 16)
                g_idx = gh % self.dimension
                vec[g_idx] += 0.35

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_text(self, text: str) -> List[float]:
        """Synchronously generate embedding for a single text string."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        self._probe_ollama()

        if self._ollama_available:
            try:
                if self._endpoint_type == "embeddings":
                    url = f"{self.base_url}/api/embeddings"
                    payload = {"model": self.model, "prompt": text}
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            emb = resp.json().get("embedding")
                            if emb:
                                return self._normalize_vec(emb)
                else:
                    url = f"{self.base_url}/api/embed"
                    payload = {"model": self.model, "input": text}
                    with httpx.Client(timeout=10.0) as client:
                        resp = client.post(url, json=payload)
                        if resp.status_code == 200:
                            embs = resp.json().get("embeddings")
                            if embs and len(embs) > 0:
                                return self._normalize_vec(embs[0])
            except Exception as e:
                logger.debug(f"Ollama embedding request failed: {e}")

        return self._fallback_embed(text)

    async def aembed_text(self, text: str) -> List[float]:
        """Asynchronously generate embedding for a single text string."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        self._probe_ollama()

        if self._ollama_available:
            try:
                if self._endpoint_type == "embeddings":
                    url = f"{self.base_url}/api/embeddings"
                    payload = {"model": self.model, "prompt": text}
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            emb = resp.json().get("embedding")
                            if emb:
                                return self._normalize_vec(emb)
                else:
                    url = f"{self.base_url}/api/embed"
                    payload = {"model": self.model, "input": text}
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            embs = resp.json().get("embeddings")
                            if embs and len(embs) > 0:
                                return self._normalize_vec(embs[0])
            except Exception as e:
                logger.debug(f"Async Ollama embedding request failed: {e}")

        return self._fallback_embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch embed list of texts."""
        return [self.embed_text(t) for t in texts]

    def _normalize_vec(self, vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [x / norm for x in vec]
        return vec


_service_instance: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _service_instance
    if _service_instance is None:
        _service_instance = EmbeddingService()
    return _service_instance
