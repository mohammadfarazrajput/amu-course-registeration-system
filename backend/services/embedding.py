"""
Embedding Service using Google Gemini
Handles text embeddings for vector store
"""

import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings



class DummyEmbeddings:
    """Dummy embeddings for fallback"""
    def embed_query(self, text: str) -> List[float]:
        return [0.0] * 768
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.0] * 768 for _ in texts]


class EmbeddingService:
    """Singleton embedding service"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Gemini embeddings"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("⚠️ GEMINI_API_KEY not found in environment")
                raise ValueError("API Key missing")
            
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=api_key
            )
            print("✅ Gemini Embeddings initialized")
            
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini Embeddings: {e}")
            print("Using DummyEmbeddings (RAG features will not work)")
            self.embeddings = DummyEmbeddings()
    
    def embed_text(self, text: str) -> List[float]:
        """Embed a single text"""
        return self.embeddings.embed_query(text)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts"""
        return self.embeddings.embed_documents(texts)


# Singleton instance
embedding_service = EmbeddingService()