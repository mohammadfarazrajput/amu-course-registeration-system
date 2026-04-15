"""
RAG Retriever Service
Retrieves relevant ordinance context for agent reasoning
"""

from typing import List, Dict
from services.vector_store import vector_store


class Retriever:
    """RAG retrieval for AMU ordinances"""
    
    def __init__(self):
        self.vector_store = vector_store
    
    def retrieve_context(self, query: str, top_k: int = 3) -> Dict:
        """
        Retrieve relevant ordinance context for a query
        
        Args:
            query: User question or context need
            top_k: Number of relevant chunks to retrieve
        
        Returns:
            Dict with retrieved documents and formatted context
        """
        # Search vector store
        results = self.vector_store.similarity_search(query, k=top_k)
        
        if not results:
            return {
                "context": "No relevant ordinance information found.",
                "sources": [],
                "chunks": []
            }
        
        # Format context for LLM
        context_parts = []
        sources = []
        chunks = []
        
        for i, result in enumerate(results, 1):
            text = result['text']
            metadata = result.get('metadata', {})
            
            # Add to context
            context_parts.append(f"[Source {i}]\n{text}")
            
            # Track sources
            source_info = metadata.get('source', 'AMU Ordinances')
            if source_info not in sources:
                sources.append(source_info)
            
            # Store chunk info
            chunks.append({
                "text": text,
                "metadata": metadata,
                "score": result.get('score', 0)
            })
        
        formatted_context = "\n\n".join(context_parts)
        
        return {
            "context": formatted_context,
            "sources": sources,
            "chunks": chunks,
            "query": query
        }
    
    def retrieve_promotion_rules(self) -> str:
        """Retrieve promotion-specific rules"""
        query = "promotion requirements earned credits semester"
        result = self.retrieve_context(query, top_k=2)
        return result['context']
    
    def retrieve_advancement_rules(self) -> str:
        """Retrieve advancement eligibility rules"""
        query = "advancement eligibility CGPA third year final year"
        result = self.retrieve_context(query, top_k=2)
        return result['context']
    
    def retrieve_registration_modes(self) -> str:
        """Retrieve registration mode rules"""
        query = "registration mode A B C attendance evaluations"
        result = self.retrieve_context(query, top_k=2)
        return result['context']
    
    def retrieve_grading_rules(self) -> str:
        """Retrieve grading and passing criteria"""
        query = "grading grade points passing marks theory lab"
        result = self.retrieve_context(query, top_k=2)
        return result['context']


# Singleton instance
retriever = Retriever()