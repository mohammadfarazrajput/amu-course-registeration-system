"""
Master Setup Script
Runs all setup steps in correct order
"""

import sys
from pathlib import Path
import subprocess

def run_script(script_name, description):
    """Run a Python script"""
    print("\n" + "=" * 60)
    print(f"🚀 {description}")
    print("=" * 60)
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            capture_output=False
        )
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("AMU Registration System - Complete Setup")
    print("=" * 60)
    
    steps = [
        ("parse_curriculum.py", "Step 1: Parse Curriculum PDFs"),
        ("seed_database.py", "Step 2: Seed Database"),
        ("build_vector_index.py", "Step 3: Build Vector Index"),
    ]
    
    success = True
    for script, description in steps:
        if not run_script(script, description):
            success = False
            print(f"\n⚠️  Setup stopped at: {description}")
            break
    
    if success:
        print("\n" + "=" * 60)
        print("✅ SETUP COMPLETE!")
        print("=" * 60)
        print("\n🚀 You can now run:")
        print("   cd backend")
        print("   python main.py")
        print("\n📖 Visit: http://localhost:8000/docs")
    else:
        print("\n❌ Setup incomplete. Please fix errors and try again.")


if __name__ == "__main__":
    main()