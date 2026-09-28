"""
retriever.py
------------
Top-k retrieval over the FAISS vector store, with optional metadata
filtering (e.g. restrict to a given source_id or license-approved sources)
and score-threshold cutoffs for safety (avoid surfacing weakly-relevant
medical content).
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List, Optional

from .embeddings import EmbeddingModel
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.0  # cosine similarity floor; raise to be more strict


class Retriever:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        default_top_k: int = DEFAULT_TOP_K,
        min_score: float = DEFAULT_MIN_SCORE,
    ):
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.default_top_k = default_top_k
        self.min_score = min_score

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        source_filter: Optional[List[str]] = None,
        metadata_filter: Optional[Callable[[Dict], bool]] = None,
        overfetch_factor: int = 4,
    ) -> List[Dict]:
        """
        Retrieve the top-k most relevant chunks for a query.

        Parameters
        ----------
        query : str
            Natural language query.
        top_k : int, optional
            Number of results to return (defaults to self.default_top_k).
        min_score : float, optional
            Minimum cosine similarity required to keep a result.
        source_filter : List[str], optional
            If provided, only keep chunks whose 'source_id' is in this list.
        metadata_filter : Callable[[dict], bool], optional
            Arbitrary predicate over a chunk's metadata dict for custom
            filtering (e.g. specialty, license, publication year).
        overfetch_factor : int
            When filters are active, fetch top_k * overfetch_factor raw
            candidates from FAISS before filtering, so filtering doesn't
            starve the result set.

        Returns
        -------
        List[Dict]
            Each dict contains chunk_id, source_id, text, position,
            metadata, and score -- sorted by score descending.
        """
        top_k = top_k if top_k is not None else self.default_top_k
        min_score = min_score if min_score is not None else self.min_score

        if not query or not query.strip():
            return []

        query_embedding = self.embedding_model.embed_query(query)

        has_filters = bool(source_filter) or metadata_filter is not None
        fetch_k = top_k * overfetch_factor if has_filters else top_k

        raw_results = self.vector_store.search(query_embedding, top_k=fetch_k)

        filtered = []
        for result in raw_results:
            if result.get("score", 0.0) < min_score:
                continue
            if source_filter and result.get("source_id") not in source_filter:
                continue
            if metadata_filter and not metadata_filter(result.get("metadata", {})):
                continue
            filtered.append(result)
            if len(filtered) >= top_k:
                break

        logger.debug(
            "Query %r -> %d results (from %d candidates)",
            query, len(filtered), len(raw_results),
        )
        return filtered

    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Convenience helper: retrieve chunks and join them into a single
        context string suitable for prompting an LLM, with citations."""
        results = self.retrieve(query, top_k=top_k, **kwargs)
        if not results:
            return ""

        parts = []
        for r in results:
            citation = r.get("source_id", "unknown")
            parts.append(f"[{citation}] {r['text']}")
        return "\n\n".join(parts)