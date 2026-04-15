
try:
    from sentence_transformers import SentenceTransformer
    print("✅ sentence-transformers is installed")
except ImportError:
    print("❌ sentence-transformers NOT installed")
