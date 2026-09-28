from __future__ import annotations

import json
import logging
import os
import numpy as np

from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_INDEX_FILENAME = "index.faiss"
DEFAULT_METADATA_FILENAME = "metadata.json"

class VectorStore:
    def __init__(self, dimension: Optional[int] = None):
        self.dimension = dimension
        self._index = None
        self.metadata: List[Dict] = []

    def _ensure_index(self):
        import faiss

        if self._index is None:
            if self.dimension is None:
                raise ValueError("dimension must be set before building the index")
            self._index = faiss.IndexFlatIP(self.dimension)

    def build(self, embeddings: np.ndarray, metadata: List[Dict]) -> None:
        import faiss

        if len(embeddings) != len(metadata):
            raise ValueError("embeddings and metadat must be the same length")

        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        self.dimension = embeddings.shape[1]
        self._index = faiss.IndexFlatIP(self.dimension)
        if len(embeddings) > 0:
            self._index.add(embeddings)
        self.metadata = list(metadata)
        logger.info("Built FAISS index with %d vectors (dim=%d)", len(embeddings), self.dimension)

    def add(self, embeddings: np.ndarray, metadata: List[Dict]) -> None:
        if len(embeddings) != len(metadata):
            raise ValueError("embeddings and metadata must be the same length")

        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        if self.dimension is None:
            self.dimension = embeddings.shape[1]

        self._ensure_index()
        if len(embeddings) > 0:
            self._index.add(embeddings)
        self.metadata.extend(metadata)
        logger.info("Added %d vectors (total=%d)", len(embeddings), self._index.ntotal)

    def search(self, query_embedding, top_k=5):
        scores, indices = self._index.search(
            query_embedding.reshape(1, -1),
            top_k,
        )

        results = []

        for idx, score in zip(indices[0], scores[0]):

            # FAISS can return -1 when there are not enough results
            if idx < 0:
                continue

            entry = self.metadata[idx].copy()

            entry["score"] = float(score)

            results.append(entry)

        return results

    def save(self, directory: str) -> None:
        import faiss

        if self._index is None:
            raise ValueError("Cannot save an empty/unbuilt index")

        os.makedirs(directory, exist_ok=True)
        index_path = os.path.join(directory, DEFAULT_INDEX_FILENAME)
        metadata_path = os.path.join(directory, DEFAULT_METADATA_FILENAME)

        faiss.write_index(self._index, index_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(
                {"dimension": self.dimension, "chunks": self.metadata},
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info("Saved vector store to %s (%d vectors)", directory, self._index.ntotal)

    @classmethod
    def load(cls, directory: str) -> "VectorStore":
        import faiss

        index_path = os.path.join(directory, DEFAULT_INDEX_FILENAME)
        metadata_path = os.path.join(directory, DEFAULT_METADATA_FILENAME)

        if not os.path.exists(index_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"Vectore store files not found in {directory}. "
                f"Run the ingestion pipeline first."
            )

        index = faiss.read_index(index_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        store = cls(dimension=payload.get("dimension"))
        store._index = index
        store.metadata = payload.get("chunks", [])
        logger.info("Loaded vector store from %s (%d vectors)", directory, index.ntotal)
        return store

    def __len__(self) -> int:
        return 0 if self._index is None else self._index.ntotal