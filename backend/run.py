"""
GrowthPilot — Quick Start
Run: python run.py
"""
import uvicorn
import subprocess
import sys
import os

def main():
    print("=" * 55)
    print("  🚀  GrowthPilot AI Business Mentor")
    print("=" * 55)

    # Ingest sample docs into ChromaDB on first run
    chroma_path = "./vector_store/chroma_db"
    if not os.path.exists(chroma_path):
        print("\n📚 First run — indexing knowledge base...")
        print("   (This may take a minute to download embedding models)")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ai_engine.ingest_docs"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            if result.returncode != 0:
                print(f"  ⚠️  Warning: Doc indexing had issues (continuing anyway)")
                if result.stderr:
                    print(f"  Details: {result.stderr[:200]}")
            else:
                print("  ✅ Knowledge base indexed successfully")
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Doc indexing timeout (continuing anyway)")
        except Exception as e:
            print(f"  ⚠️  Could not index docs: {e}")
            print("  The app will still run with sample knowledge")

    print("\n✅ Starting FastAPI server at http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("📊 Logs: growthpilot.log")
    print("🛑 Press Ctrl+C to stop\n")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
