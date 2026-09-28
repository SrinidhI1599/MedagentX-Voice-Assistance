from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n")

DEFAULT_CHUNK_SIZE = 800
DEFAULT_CHUNK_OVERLAP = 150
MIN_CHUNK_SIZE = 50

@dataclass
class Chunk:
    chunk_id: str
    source_id: str 
    text: str 
    position: int
    char_start: int 
    char_end: int 
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return{
            "chunk_id": self.chunk_id,
            "source_id": self.source_id,
            "text": self.text,
            "position": self.position,
            "char_start": self.char_start,
            "metadata": self.metadata
        }

def _split_sentences(paragraph: str) -> List[str]:
    sentences = _SENTENCE_SPLIT_RE.split(paragraph.strip())
    return [s for s in sentences if s.strip()]

def _split_paragraph(text: str) -> List[str]:
    paragraphs = _PARAGRAPH_SPLIT_RE.split(text.strip())
    return [p.strip() for p in paragraphs if p.strip()]

def _pack_units(units: List[str], chunk_size: int, overlap: int) -> List[str]:
    chunks: List[str] = []
    current = ""

    for unit in units:
        candidate = f"{current} {unit}".strip() if current else unit

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail}{unit}".strip() if tail else unit
        else:
            current = unit

        while len(current) > chunk_size * 1.5:
            chunks.append(current[:chunk_size])
            current = current[chunk_size - overlap:]

    if current.strip():
        chunks.append(current.strip())

    return chunks

def chunk_document(
    text: str,
    source_id: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    extra_metadata: Optional[dict] = None,
) -> List[Chunk]:

    if not text or not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    paragraphs = _split_paragraph(text)

    units: List[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            units.append(para)
        else:
            units.extend(_split_sentences(para))

    raw_chunks = _pack_units(units, chunk_size, chunk_overlap)

    merged: List[str] = []
    for c in raw_chunks:
        if merged and len(c) < MIN_CHUNK_SIZE:
            merged[-1] = f"{merged[-1]} {c}".strip()
        else:
            merged.append(c)

    chunks: List[Chunk] = []
    cursor = 0
    for i, chunk_text in enumerate(merged):
        start = text.find(chunk_text[:30], cursor) if chunk_text else cursor
        start = max(start, 0)
        end = start + len(chunk_text)
        cursor = max(end - chunk_overlap, cursor)

        chunks.append(
            Chunk(
                chunk_id=f"{source_id}::chunk_{i:04d}",
                source_id=source_id,
                text=chunk_text,
                position=i,
                char_start=start,
                char_end=end,
                metadata=dict(extra_metadata or {})
            )
        )

    return chunks