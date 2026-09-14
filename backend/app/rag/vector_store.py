import json
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.models import MedicalDocumentChunk
from app.rag.chunker import DocumentChunk
from app.core.logs import logger
from app.core.config import settings


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorStore:
    """
    PostgreSQL + pgvector Vector Store with seamless SQLite / generic DB fallback.
    """

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def add_chunks(
        self,
        db: Session,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> int:
        """Insert document chunks and their embeddings into the database."""
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks count must match embeddings count")

        records = []
        for chunk, emb in zip(chunks, embeddings):
            emb_json = json.dumps(emb)
            meta_json = json.dumps(chunk.metadata)

            rec = MedicalDocumentChunk(
                document_title=chunk.document_title,
                source_file=chunk.source_file,
                section=chunk.section,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding_json=emb_json,
                meta_info=meta_json
            )
            records.append(rec)

        db.add_all(records)
        db.commit()
        logger.info(f"Inserted {len(records)} medical document chunks into vector store")
        return len(records)

    def search_similar(
        self,
        db: Session,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        min_score: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        Search nearest matching chunks using cosine similarity.
        """
        k = top_k or self.top_k

        # Fetch candidate chunks from database
        chunks = db.query(MedicalDocumentChunk).all()
        if not chunks:
            logger.info("No medical document chunks found in vector store")
            return []

        scored_results = []
        for chunk in chunks:
            if not chunk.embedding_json:
                continue
            try:
                emb = json.loads(chunk.embedding_json)
                score = cosine_similarity(query_embedding, emb)
                if score >= min_score:
                    scored_results.append({
                        "id": chunk.id,
                        "document_title": chunk.document_title,
                        "source_file": chunk.source_file,
                        "section": chunk.section,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "score": round(float(score), 4),
                        "snippet": chunk.content[:200] + ("..." if len(chunk.content) > 200 else "")
                    })
            except Exception as e:
                logger.debug(f"Error parsing chunk embedding {chunk.id}: {e}")

        # Sort by similarity descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_results[:k]
        logger.info(f"Retrieved {len(top_results)} relevant RAG chunks (top score: {top_results[0]['score'] if top_results else 'N/A'})")
        return top_results

    def clear_documents(self, db: Session, source_file: Optional[str] = None):
        """Clear chunks for a specific file or all chunks."""
        if source_file:
            db.query(MedicalDocumentChunk).filter(MedicalDocumentChunk.source_file == source_file).delete()
        else:
            db.query(MedicalDocumentChunk).delete()
        db.commit()
        logger.info(f"Cleared chunks from vector store (filter: {source_file or 'ALL'})")

    def get_stats(self, db: Session) -> Dict[str, Any]:
        """Return knowledge base statistics."""
        total_chunks = db.query(MedicalDocumentChunk).count()
        files = db.query(MedicalDocumentChunk.source_file).distinct().all()
        file_list = [f[0] for f in files if f[0]]
        return {
            "total_chunks": total_chunks,
            "document_count": len(file_list),
            "documents": file_list
        }


_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(top_k=getattr(settings, "RAG_TOP_K", 3))
    return _vector_store_instance
