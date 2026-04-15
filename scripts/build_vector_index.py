
"""
Build FAISS Vector Index from All AMU PDFs (Curriculum & Ordinances)
Indices:
1. Ordinances (Rules, Regulations)
2. Curriculum (Course Descriptions, Outcomes)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from backend.services.document_processor import document_processor
from backend.services.vector_store import vector_store
import pdfplumber
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

def process_pdf(pdf_path: Path, doc_type: str) -> list:
    """Process PDF and extract text chunks"""
    print(f"📄 Processing [{doc_type}]: {pdf_path.name}")
    
    chunks = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    # Clean up text (remove excessive whitespace)
                    text = " ".join(text.split())
                    full_text += text + "\n\n"
            
            if not full_text.strip():
                print(f"   ⚠️  No text found in {pdf_path.name}")
                return []
            
            # Chunk the document
            text_chunks = document_processor.chunk_document(
                full_text,
                chunk_size=1000,
                overlap=200
            )
            
            # Add metadata
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    "text": chunk,
                    "metadata": {
                        "source": pdf_path.name,
                        "chunk_id": i,
                        "document_type": doc_type,
                        "path": str(pdf_path)
                    }
                })
            
            print(f"   ✅ Created {len(chunks)} chunks")
    
    except Exception as e:
        print(f"   ❌ Error processing {pdf_path.name}: {e}")
    
    return chunks


def build_vector_index():
    print("=" * 60)
    print("Building Global Vector Index (Ordinances + Curriculum)")
    print("=" * 60)
    
    data_dir = Path(__file__).parent.parent / "data" / "raw"
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    all_chunks = []
    
    # 1. Scan Ordinances
    ordinance_dir = data_dir / "ordinances"
    if ordinance_dir.exists():
        for pdf_file in ordinance_dir.glob("*.pdf"):
            chunks = process_pdf(pdf_file, "ordinance")
            all_chunks.extend(chunks)
            
    # 2. Scan Curriculum
    curriculum_dir = data_dir / "curriculum"
    if curriculum_dir.exists():
        for pdf_file in curriculum_dir.glob("*.pdf"):
            chunks = process_pdf(pdf_file, "curriculum")
            all_chunks.extend(chunks)
            
    # 3. Check for root level PDFs (e.g., if organized flatly)
    for pdf_file in data_dir.glob("*.pdf"):
        chunks = process_pdf(pdf_file, "general")
        all_chunks.extend(chunks)

    if not all_chunks:
        print("❌ No documents found to index!")
        return
    
    print(f"\n📊 Total chunks collected: {len(all_chunks)}")
    print("🔨 Building FAISS index...")
    
    try:
        # Add to vector store
        texts = [chunk["text"] for chunk in all_chunks]
        metadatas = [chunk["metadata"] for chunk in all_chunks]
        
        vector_store.add_documents(texts, metadatas)
        
        # Save index
        print("💾 Saving vector store...")
        vector_store.save()
        
        # Show stats
        stats = vector_store.get_stats()
        print(f"\n✅ Vector store build COMPLETE!")
        print(f"   Docs: {stats['total_documents']}")
        print(f"   Size: {stats['index_size']}")
        
    except Exception as e:
        print(f"❌ Error building index: {e}")


if __name__ == "__main__":
    build_vector_index()