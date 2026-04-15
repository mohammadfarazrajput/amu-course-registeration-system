"""
Vector Store Service using FAISS
Handles ordinance storage and retrieval
"""

import os
from pathlib import Path
from typing import List, Dict
import pickle
import faiss
import numpy as np

from services.embedding import embedding_service


class VectorStore:
    """FAISS vector store for AMU ordinances"""
    
    def __init__(self, store_path: str = "../data/vector_store"):
        self.store_path = Path(store_path)
        self.store_path.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.store_path / "faiss.index"
        self.metadata_file = self.store_path / "metadata.pkl"
        
        self.index = None
        self.documents = []
        self.metadatas = []
        
        # Load if exists
        if self.index_file.exists():
            self.load()
        else:
            print("⚠️ Vector store not found. Run build_vector_index.py first.")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict] = None):
        """Add documents to vector store"""
        if not texts:
            return
        
        # Generate embeddings
        embeddings = embedding_service.embed_texts(texts)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Create index if doesn't exist
        if self.index is None:
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self.documents.extend(texts)
        if metadatas:
            self.metadatas.extend(metadatas)
        else:
            self.metadatas.extend([{} for _ in texts])
        
        print(f"✅ Added {len(texts)} documents to vector store")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        if self.index is None or self.index.ntotal == 0:
            # Attempt a lazy load in case the index was built after startup
            if self.index_file.exists() and self.index is None:
                try:
                    self.load()
                except Exception as e:
                    print(f"⚠️ Lazy load failed: {e}")
            if self.index is None or self.index.ntotal == 0:
                print("⚠️ Vector store is empty — RAG features disabled")
                return []
        
        # Embed query
        query_embedding = embedding_service.embed_text(query)
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_array, k)
        
        # Format results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append({
                    "text": self.documents[idx],
                    "metadata": self.metadatas[idx],
                    "score": float(dist)
                })
        
        return results
    
    def save(self):
        """Save index and metadata to disk"""
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))
        
        with open(self.metadata_file, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadatas': self.metadatas
            }, f)
        
        print(f"✅ Vector store saved to {self.store_path}")
    
    def load(self):
        """Load index and metadata from disk"""
        if self.index_file.exists():
            self.index = faiss.read_index(str(self.index_file))
            print(f"✅ Loaded FAISS index with {self.index.ntotal} vectors")
        
        if self.metadata_file.exists():
            with open(self.metadata_file, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.metadatas = data['metadatas']
            print(f"✅ Loaded {len(self.documents)} documents")
    
    def get_stats(self) -> Dict:
        """Get vector store statistics"""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.index.d if self.index else 0
        }


# Singleton instance
vector_store = VectorStore()