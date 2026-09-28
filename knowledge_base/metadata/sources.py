"""
sources.py
----------
Registry of knowledge base source documents used by MedAgentX's RAG
pipeline, plus license verification so we never ingest content whose
license doesn't permit the intended use (retrieval-augmented generation
for a medical assistant, potentially redistributed to end users).

Each source's raw text is expected to live at:
    knowledge_base/raw/<source_id>.txt
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Licenses considered safe for ingestion + redistribution of excerpts
# in a RAG context. Extend this set only after legal/compliance review.
APPROVED_LICENSES = {
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "CC0-1.0",
    "PUBLIC-DOMAIN",
    "US-GOV-PUBLIC-DOMAIN",   # e.g. NIH/CDC/MedlinePlus works
    "INTERNAL-LICENSED",       # explicitly licensed for internal use, tracked separately
}

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")


@dataclass
class Source:
    source_id: str            # matches raw/<source_id>.txt, used as chunk prefix
    title: str
    publisher: str
    url: Optional[str] = None
    license: str = "UNKNOWN"
    specialty: List[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    notes: str = ""

    @property
    def raw_path(self) -> str:
        return os.path.join(RAW_DIR, f"{self.source_id}.txt")

    def is_license_approved(self) -> bool:
        return self.license in APPROVED_LICENSES

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "publisher": self.publisher,
            "url": self.url,
            "license": self.license,
            "specialty": self.specialty,
            "publication_year": self.publication_year,
            "notes": self.notes,
        }


# ----------------------------------------------------------------------
# Registry. Add new sources here -- ingestion refuses to run on any
# source_id not registered, and refuses any source with a non-approved
# license (see is_license_approved below).
# ----------------------------------------------------------------------
SOURCE_REGISTRY: Dict[str, Source] = {
    "medlineplus_hypertension": Source(
        source_id="medlineplus_hypertension",
        title="High Blood Pressure",
        publisher="MedlinePlus (NIH/NLM)",
        url="https://medlineplus.gov/highbloodpressure.html",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["cardiology", "internal_medicine"],
        notes="Public-domain patient education content from the NLM.",
    ),
    "medlineplus_type2_diabetes": Source(
        source_id="medlineplus_type2_diabetes",
        title="Type 2 Diabetes",
        publisher="MedlinePlus (NIH/NLM)",
        url="https://medlineplus.gov/type2diabetes.html",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["endocrinology", "internal_medicine"],
        notes="Public-domain patient education content from the NLM.",
    ),
    # Add additional sources here. Example template:
    # "source_id": Source(
    #     source_id="source_id",
    #     title="...",
    #     publisher="...",
    #     url="...",
    #     license="CC-BY-4.0",
    #     specialty=["..."],
    #     publication_year=2024,
    # ),
}


def get_source(source_id: str) -> Source:
    if source_id not in SOURCE_REGISTRY:
        raise KeyError(
            f"Unknown source_id '{source_id}'. Register it in "
            f"knowledge_base/metadata/sources.py before ingesting."
        )
    return SOURCE_REGISTRY[source_id]


def list_sources(specialty: Optional[str] = None) -> List[Source]:
    sources = list(SOURCE_REGISTRY.values())
    if specialty:
        sources = [s for s in sources if specialty in s.specialty]
    return sources


def is_license_approved(source_id: str) -> bool:
    return get_source(source_id).is_license_approved()


def validate_raw_files_present() -> Dict[str, bool]:
    """Check that every registered source has a corresponding raw .txt
    file on disk. Returns a dict of source_id -> exists (bool)."""
    return {sid: os.path.exists(src.raw_path) for sid, src in SOURCE_REGISTRY.items()}