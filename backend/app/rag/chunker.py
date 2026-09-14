import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.logs import logger


@dataclass
class DocumentChunk:
    document_title: str
    source_file: str
    section: str
    chunk_index: int
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MedicalDocumentChunker:
    """
    Semantic Markdown/Text chunker designed for clinical documents and medical guidelines.
    Preserves headings, bullet lists, and paragraphs.
    """

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_file(self, file_path: Path) -> List[DocumentChunk]:
        """Load and split a medical document into structured chunks."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        text = file_path.read_text(encoding="utf-8", errors="replace")
        return self.chunk_text(text, source_file=file_path.name)

    def chunk_text(self, text: str, source_file: str = "document.md") -> List[DocumentChunk]:
        """Parse markdown structure and produce overlapping semantic chunks."""
        lines = text.split("\n")

        # Extract top-level title
        document_title = source_file.replace(".md", "").replace("_", " ").title()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                document_title = stripped.lstrip("# ").strip()
                break

        # Parse document into sections by markdown headers (##, ###)
        sections = []
        current_section = "General Overview"
        current_lines = []

        for line in lines:
            header_match = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
            if header_match:
                if current_lines:
                    sections.append((current_section, "\n".join(current_lines).strip()))
                    current_lines = []
                current_section = header_match.group(2).strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_section, "\n".join(current_lines).strip()))

        # Now chunk each section
        chunks: List[DocumentChunk] = []
        chunk_idx = 0

        for section_title, section_text in sections:
            if not section_text:
                continue

            paragraphs = re.split(r"\n\s*\n", section_text)
            current_chunk_paragraphs = []
            current_len = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                para_len = len(para)
                if current_len + para_len > self.chunk_size and current_chunk_paragraphs:
                    # Flush current chunk
                    chunk_body = "\n\n".join(current_chunk_paragraphs).strip()
                    if chunk_body:
                        chunks.append(DocumentChunk(
                            document_title=document_title,
                            source_file=source_file,
                            section=section_title,
                            chunk_index=chunk_idx,
                            content=chunk_body,
                            metadata={
                                "char_count": len(chunk_body),
                                "source_file": source_file,
                                "section": section_title
                            }
                        ))
                        chunk_idx += 1

                    # Retain last paragraph for overlap if within overlap size
                    if len(current_chunk_paragraphs[-1]) <= self.chunk_overlap:
                        current_chunk_paragraphs = [current_chunk_paragraphs[-1], para]
                        current_len = sum(len(p) for p in current_chunk_paragraphs)
                    else:
                        current_chunk_paragraphs = [para]
                        current_len = para_len
                else:
                    current_chunk_paragraphs.append(para)
                    current_len += para_len

            if current_chunk_paragraphs:
                chunk_body = "\n\n".join(current_chunk_paragraphs).strip()
                if chunk_body:
                    chunks.append(DocumentChunk(
                        document_title=document_title,
                        source_file=source_file,
                        section=section_title,
                        chunk_index=chunk_idx,
                        content=chunk_body,
                        metadata={
                            "char_count": len(chunk_body),
                            "source_file": source_file,
                            "section": section_title
                        }
                    ))
                    chunk_idx += 1

        logger.info(f"Chunked '{source_file}' into {len(chunks)} chunks")
        return chunks

    def chunk_directory(self, dir_path: Path) -> List[DocumentChunk]:
        """Scan directory and chunk all .md and .txt files."""
        dir_path = Path(dir_path)
        if not dir_path.exists():
            logger.warning(f"Knowledge directory does not exist: {dir_path}")
            return []

        all_chunks: List[DocumentChunk] = []
        for ext in ("*.md", "*.txt"):
            for f in sorted(dir_path.glob(ext)):
                try:
                    file_chunks = self.chunk_file(f)
                    all_chunks.extend(file_chunks)
                except Exception as e:
                    logger.error(f"Failed to chunk file {f.name}: {e}")

        logger.info(f"Loaded {len(all_chunks)} total chunks from {dir_path}")
        return all_chunks
