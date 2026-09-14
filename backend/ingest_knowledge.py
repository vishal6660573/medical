"""
Convenience CLI script to ingest medical knowledge documents into the RAG vector store.
Run:
    python ingest_knowledge.py
"""
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.rag.ingest import ingest_medical_documents

if __name__ == "__main__":
    result = ingest_medical_documents()
    print("Ingestion Result:", result)
