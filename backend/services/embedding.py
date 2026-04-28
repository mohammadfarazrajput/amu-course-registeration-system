"""
Embedding Service
Uses sentence-transformers (local, free, no API needed).
Gemini embeddings removed — was causing failures when rate-limited.
"""

import os
from typing import List


class DummyEmbeddings:
    """Fallback if sentence-transformers not installed"""
    DIM = 384

    def embed_query(self, text: str) -> List[float]:
        return [0.0] * self.DIM

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * self.DIM for _ in texts]


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.model = SentenceTransformer(model_name)
            self._use_st = True
            print(f"✅ Embeddings: sentence-transformers ({model_name})")
        except Exception as e:
            print(f"⚠️ sentence-transformers unavailable: {e} — using DummyEmbeddings")
            self.model = DummyEmbeddings()
            self._use_st = False

    def embed_text(self, text: str) -> List[float]:
        if self._use_st:
            return self.model.encode(text, convert_to_numpy=True).tolist()
        return self.model.embed_query(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self._use_st:
            return self.model.encode(texts, convert_to_numpy=True).tolist()
        return self.model.embed_documents(texts)


embedding_service = EmbeddingService()
