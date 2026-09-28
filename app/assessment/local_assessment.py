"""
local_assessment.py
--------------------
Local, in-process replacement for the external `/assess` service that
backend/main.py used to call over ngrok.

It uses the RAG stack already in this repo (app/rag) to pull the most
relevant chunks from the FAISS knowledge base for the patient's symptoms,
then builds a patient_summary / possible_conditions / evidence dict in
the exact shape that AssessmentBuilder.build() expects.

No external API key or network call is required. If you later want an
LLM to write a nicer summary, you can slot a call to e.g. Claude/OpenAI
in `_build_patient_summary`, using the retrieved chunks as context.
"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, List

from app.rag.embeddings import EmbeddingModel
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore

DEFAULT_VECTOR_STORE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "knowledge_base",
        "vector_store",
    )
)

# Loaded once per process, not per-request.
_vector_store: VectorStore | None = None
_embedding_model: EmbeddingModel | None = None
_retriever: Retriever | None = None


def _get_retriever() -> Retriever:
    global _vector_store, _embedding_model, _retriever

    if _retriever is None:
        _vector_store = VectorStore.load(DEFAULT_VECTOR_STORE_DIR)
        _embedding_model = EmbeddingModel()
        _retriever = Retriever(_vector_store, _embedding_model)

    return _retriever


def _build_query(patient_data: dict) -> str:
    symptoms = ", ".join(patient_data.get("symptoms", []))
    return (
        f"{symptoms}. Severity: {patient_data.get('severity')}. "
        f"Duration: {patient_data.get('duration_days')} days. "
        f"Progression: {patient_data.get('progression')}."
    )


def _build_patient_summary(patient_data: dict) -> str:
    symptoms = ", ".join(patient_data.get("symptoms", []))
    return (
        f"{patient_data.get('age')}-year-old {patient_data.get('sex')} "
        f"reporting {symptoms} for {patient_data.get('duration_days')} day(s), "
        f"described as {str(patient_data.get('severity')).lower()} and "
        f"{str(patient_data.get('progression')).lower()}."
    )


def _build_possible_conditions(results: List[Dict]) -> List[Dict]:
    """Group retrieved chunks by their source/title and turn the best
    score per group into a rough 'confidence' bucket."""
    grouped: Dict[str, List[Dict]] = defaultdict(list)

    for r in results:
        title = r.get("metadata", {}).get("title") or r.get("source_id", "Unknown")
        grouped[title].append(r)

    conditions = []
    for title, chunks in grouped.items():
        best_score = max(c.get("score", 0.0) for c in chunks)

        if best_score >= 0.6:
            confidence = "High"
        elif best_score >= 0.4:
            confidence = "Moderate"
        else:
            confidence = "Low"

        conditions.append(
            {
                "condition": title,
                "confidence": confidence,
                "match_score": round(best_score, 3),
                "explanation": (
                    f"Confidence: {confidence} (similarity score {round(best_score, 3)}), "
                    f"based on {len(chunks)} matching reference passage(s)."
                ),
            }
        )

    conditions.sort(key=lambda c: c["match_score"], reverse=True)
    return conditions


def _build_evidence(results: List[Dict]) -> List[Dict]:
    evidence = []
    for r in results:
        text = r.get("text", "")
        title = r.get("metadata", {}).get("title") or r.get("source_id")
        source_file = r.get("metadata", {}).get("source_file")
        excerpt = text[:400] + ("..." if len(text) > 400 else "")

        evidence.append(
            {
                "source_id": r.get("source_id"),
                "title": title,
                "source_file": source_file,
                "score": round(r.get("score", 0.0), 3),
                "excerpt": excerpt,
                # Keys the Streamlit frontend reads directly:
                "source": f"{title} ({source_file})" if source_file else title,
                "explanation": excerpt,
            }
        )
    return evidence


def run_local_assessment(patient_data: dict, top_k: int = 5) -> dict:
    """
    Drop-in local replacement for the response that used to come back
    from the ngrok /assess endpoint.

    Returns:
        {
            "patient_summary": str,
            "possible_conditions": [{"condition", "confidence", "match_score"}],
            "evidence": [{"source_id", "title", "source_file", "score", "excerpt"}],
        }
    """
    retriever = _get_retriever()
    query = _build_query(patient_data)
    results = retriever.retrieve(query, top_k=top_k)

    return {
        "patient_summary": _build_patient_summary(patient_data),
        "possible_conditions": _build_possible_conditions(results),
        "evidence": _build_evidence(results),
    }