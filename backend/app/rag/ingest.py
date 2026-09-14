import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure backend directory is in python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.core.logs import logger
from app.database.database import SessionLocal, create_tables
from app.rag.chunker import MedicalDocumentChunker
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import get_vector_store


def find_docs_dir() -> Path:
    """Resolve medical knowledge documents directory path."""
    candidates = [
        BASE_DIR / settings.DOCS_DIR,
        BASE_DIR.parent / settings.DOCS_DIR,
        BASE_DIR / "data" / "medical_knowledge",
        BASE_DIR.parent / "data" / "medical_knowledge",
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    # Default to data/medical_knowledge relative to repo root
    return BASE_DIR.parent / "data" / "medical_knowledge"


def ingest_medical_documents(
    docs_dir: Optional[Path] = None,
    clear_existing: bool = True
) -> Dict[str, Any]:
    """
    Ingest all medical documents into the vector store:
    1. Scan and parse .md/.txt files
    2. Split into structured semantic chunks
    3. Generate dense embeddings via Ollama / embedding service
    4. Store chunks and embeddings into PostgreSQL/SQLite
    """
    target_dir = docs_dir or find_docs_dir()
    logger.info(f"Starting medical document ingestion from: {target_dir}")

    if not target_dir.exists():
        msg = f"Knowledge base directory does not exist: {target_dir}"
        logger.error(msg)
        return {"success": False, "error": msg, "chunks_ingested": 0}

    # Ensure database tables exist
    create_tables()

    # 1. Chunk documents
    chunker = MedicalDocumentChunker(chunk_size=700, chunk_overlap=120)
    chunks = chunker.chunk_directory(target_dir)

    if not chunks:
        logger.warning("No document chunks created. Check directory content.")
        return {"success": True, "chunks_ingested": 0, "message": "No documents found"}

    # 2. Generate embeddings
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    embedding_service = get_embedding_service()
    chunk_texts = [f"{c.document_title} - {c.section}\n{c.content}" for c in chunks]
    embeddings = embedding_service.embed_documents(chunk_texts)

    # 3. Store into Vector Store
    db = SessionLocal()
    try:
        vector_store = get_vector_store()
        if clear_existing:
            vector_store.clear_documents(db)

        inserted_count = vector_store.add_chunks(db, chunks, embeddings)
        stats = vector_store.get_stats(db)
        logger.info(f"RAG ingestion completed successfully! Total chunks in DB: {stats['total_chunks']}")
        return {
            "success": True,
            "chunks_ingested": inserted_count,
            "total_chunks": stats["total_chunks"],
            "documents": stats["documents"],
            "docs_dir": str(target_dir)
        }
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        db.rollback()
        return {"success": False, "error": str(e), "chunks_ingested": 0}
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Smart Health Platform - RAG Medical Knowledge Ingestion")
    print("=" * 60)
    res = ingest_medical_documents()
    print(f"Result: {res}")
