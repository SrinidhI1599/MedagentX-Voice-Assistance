"""
sources.py
----------
Registry of knowledge-base source folders used by MedAgentX's RAG pipeline.

Expected structure:

knowledge_base/
└── raw/
    ├── Diabetes/
    │   ├── article1.txt
    │   ├── article2.txt
    │   └── ...
    │
    └── Heart_Disease/
        ├── article1.txt
        ├── article2.txt
        └── ...

Each registered source_id corresponds to a folder under knowledge_base/raw/.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ----------------------------------------------------------------------
# Approved licenses
# ----------------------------------------------------------------------

APPROVED_LICENSES = {
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "CC0-1.0",
    "PUBLIC-DOMAIN",
    "US-GOV-PUBLIC-DOMAIN",
    "INTERNAL-LICENSED",
}


# ----------------------------------------------------------------------
# Raw knowledge-base directory
# ----------------------------------------------------------------------

RAW_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "knowledge_base",
        "raw",
    )
)


# ----------------------------------------------------------------------
# Source definition
# ----------------------------------------------------------------------

@dataclass
class Source:
    source_id: str
    title: str
    publisher: str
    url: Optional[str] = None
    license: str = "UNKNOWN"
    specialty: List[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    notes: str = ""

    @property
    def raw_dir(self) -> str:
        """
        Return the directory containing raw files for this source.
        """
        return os.path.join(RAW_DIR, self.source_id)

    @property
    def raw_files(self) -> List[str]:
        """
        Return all .txt files inside the source directory.
        """
        if not os.path.isdir(self.raw_dir):
            return []

        files = []

        for root, _, filenames in os.walk(self.raw_dir):
            for filename in filenames:
                if filename.lower().endswith(".txt"):
                    files.append(
                        os.path.join(root, filename)
                    )

        return sorted(files)

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
# Source registry
#
# IMPORTANT:
# source_id must match the folder name under:
#
# knowledge_base/raw/
# ----------------------------------------------------------------------

SOURCE_REGISTRY: Dict[str, Source] = {

    "Diabetes": Source(
        source_id="Diabetes",
        title="Diabetes",
        publisher="Medical Knowledge Base",
        url=None,
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=[
            "diabetes",
            "endocrinology",
            "internal_medicine",
        ],
        notes="Medical reference documents stored in the Diabetes knowledge-base folder.",
    ),

    "Heart_Disease": Source(
        source_id="Heart_Disease",
        title="Heart Disease",
        publisher="Medical Knowledge Base",
        url=None,
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=[
            "cardiology",
            "heart_disease",
            "internal_medicine",
        ],
        notes="Medical reference documents stored in the Heart_Disease knowledge-base folder.",
    ),

    "CKD": Source(
        source_id="CKD",
        title="Chronic Kidney Disease",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["nephrology", "internal_medicine"],
        notes="Medical reference documents stored in the CKD knowledge-base folder.",
    ),

    "COPD": Source(
        source_id="COPD",
        title="Chronic Obstructive Pulmonary Disease",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["pulmonology", "internal_medicine"],
        notes="Medical reference documents stored in the COPD knowledge-base folder.",
    ),

    "Cancer": Source(
        source_id="Cancer",
        title="Cancer",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["oncology", "internal_medicine"],
        notes="Medical reference documents stored in the Cancer knowledge-base folder.",
    ),

    "Chikungunya": Source(
        source_id="Chikungunya",
        title="Chikungunya",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the Chikungunya knowledge-base folder.",
    ),

    "Dengue": Source(
        source_id="Dengue",
        title="Dengue",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the Dengue knowledge-base folder.",
    ),

    "GERD": Source(
        source_id="GERD",
        title="Gastroesophageal Reflux Disease",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["gastroenterology", "internal_medicine"],
        notes="Medical reference documents stored in the GERD knowledge-base folder.",
    ),

    "HyperTension": Source(
        source_id="HyperTension",
        title="Hypertension",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["cardiology", "internal_medicine"],
        notes="Medical reference documents stored in the HyperTension knowledge-base folder.",
    ),

    "Malaria": Source(
        source_id="Malaria",
        title="Malaria",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the Malaria knowledge-base folder.",
    ),

    "Pneumonia": Source(
        source_id="Pneumonia",
        title="Pneumonia",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["pulmonology", "infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the Pneumonia knowledge-base folder.",
    ),

    "Stroke": Source(
        source_id="Stroke",
        title="Stroke",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["neurology", "internal_medicine"],
        notes="Medical reference documents stored in the Stroke knowledge-base folder.",
    ),

    "TB": Source(
        source_id="TB",
        title="Tuberculosis",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["pulmonology", "infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the TB knowledge-base folder.",
    ),

    "UTI": Source(
        source_id="UTI",
        title="Urinary Tract Infection",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["urology", "infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the UTI knowledge-base folder.",
    ),

    "asthma": Source(
        source_id="asthma",
        title="Asthma",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["pulmonology", "internal_medicine"],
        notes="Medical reference documents stored in the asthma knowledge-base folder.",
    ),

    "fatty liver": Source(
        source_id="fatty liver",
        title="Fatty Liver Disease",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["hepatology", "gastroenterology", "internal_medicine"],
        notes="Medical reference documents stored in the fatty liver knowledge-base folder.",
    ),

    "gastroenteritis": Source(
        source_id="gastroenteritis",
        title="Gastroenteritis",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["gastroenterology", "infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the gastroenteritis knowledge-base folder.",
    ),

    "hepatitis": Source(
        source_id="hepatitis",
        title="Hepatitis",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["hepatology", "infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the hepatitis knowledge-base folder.",
    ),

    "migraine": Source(
        source_id="migraine",
        title="Migraine",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["neurology", "internal_medicine"],
        notes="Medical reference documents stored in the migraine knowledge-base folder.",
    ),

    "obesity": Source(
        source_id="obesity",
        title="Obesity",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["endocrinology", "internal_medicine"],
        notes="Medical reference documents stored in the obesity knowledge-base folder.",
    ),

    "typhoid": Source(
        source_id="typhoid",
        title="Typhoid Fever",
        publisher="Medical Knowledge Base",
        license="US-GOV-PUBLIC-DOMAIN",
        specialty=["infectious_disease", "internal_medicine"],
        notes="Medical reference documents stored in the typhoid knowledge-base folder.",
    ),
}


# ----------------------------------------------------------------------
# Source helper functions
# ----------------------------------------------------------------------

def get_source(source_id: str) -> Source:
    if source_id not in SOURCE_REGISTRY:
        raise KeyError(
            f"Unknown source_id '{source_id}'. "
            f"Register it in knowledge_base/metadata/sources.py "
            f"before ingesting."
        )

    return SOURCE_REGISTRY[source_id]


def list_sources(
    specialty: Optional[str] = None,
) -> List[Source]:

    sources = list(SOURCE_REGISTRY.values())

    if specialty:
        sources = [
            source
            for source in sources
            if specialty in source.specialty
        ]

    return sources


def is_license_approved(source_id: str) -> bool:
    return get_source(source_id).is_license_approved()


def validate_raw_files_present() -> Dict[str, bool]:
    """
    Check whether each registered source folder contains
    at least one .txt file.

    Returns:
        {
            "Diabetes": True,
            "Heart_Disease": True
        }
    """

    return {
        source_id: len(source.raw_files) > 0
        for source_id, source in SOURCE_REGISTRY.items()
    }