
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path.cwd() / "backend"))

print("Testing Backend Startup...")

try:
    from main import app
    print("✅ FastAPI app initialized successfully")
except Exception as e:
    print(f"❌ Backend startup failed: {e}")
    import traceback
    traceback.print_exc()
