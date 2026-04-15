
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Importing fastapi...")
    import fastapi
    print("Importing sqlalchemy...")
    import sqlalchemy
    print("Importing langchain...")
    import langchain
    # print("Importing faiss...")
    # import faiss
    print("Importing sentence_transformers...")
    import sentence_transformers
    
    print("Importing local modules...")
    from database import init_db
    from models import Student
    
    print("All imports successful!")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
