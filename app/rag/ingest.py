"""
ingest.py
---------

End-to-end ingestion pipeline:

raw source .txt files
        ↓
clean
        ↓
chunk
        ↓
embed
        ↓
FAISS vector store

Expected raw folder structure:

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

Usage:

    python -m app.rag.ingest

Specific source:

    python -m app.rag.ingest --source Diabetes

    python -m app.rag.ingest --source Heart_Disease

Both:

    python -m app.rag.ingest \
        --source Diabetes \
        --source Heart_Disease
"""

from __future__ import annotations

import argparse
import logging
import os
from typing import List, Optional

from .clean import clean_text
from .chunker import (
    chunk_document,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)
from .embeddings import (
    EmbeddingModel,
    DEFAULT_MODEL_NAME,
)
from .vector_store import VectorStore

from app.rag.metadata.sources import (
    SOURCE_REGISTRY,
    get_source,
    validate_raw_files_present,
)


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Vector store output directory
# ----------------------------------------------------------------------

DEFAULT_VECTOR_STORE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "knowledge_base",
        "vector_store",
    )
)


# ----------------------------------------------------------------------
# Main ingestion pipeline
# ----------------------------------------------------------------------

def run_ingestion_pipeline(
    source_ids: Optional[List[str]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    model_name: str = DEFAULT_MODEL_NAME,
    output_dir: str = DEFAULT_VECTOR_STORE_DIR,
    skip_license_check: bool = False,
) -> VectorStore:

    """
    Run the complete RAG ingestion pipeline.

    Pipeline:

        raw TXT files
            ↓
        cleaning
            ↓
        chunking
            ↓
        embeddings
            ↓
        FAISS
            ↓
        disk
    """

    # --------------------------------------------------------------
    # Select sources
    # --------------------------------------------------------------

    source_ids = source_ids or list(SOURCE_REGISTRY.keys())

    if not source_ids:
        raise ValueError(
            "No sources registered in "
            "knowledge_base/metadata/sources.py"
        )

    logger.info(
        "Sources selected for ingestion: %s",
        ", ".join(source_ids),
    )

    # --------------------------------------------------------------
    # Validate raw files
    # --------------------------------------------------------------

    presence = validate_raw_files_present()

    all_chunks = []

    # --------------------------------------------------------------
    # Process each source folder
    # --------------------------------------------------------------

    for source_id in source_ids:

        source = get_source(source_id)

        # ----------------------------------------------------------
        # License check
        # ----------------------------------------------------------

        if not skip_license_check:

            if not source.is_license_approved():

                logger.warning(
                    "Skipping source '%s': license '%s' "
                    "is not approved for ingestion.",
                    source_id,
                    source.license,
                )

                continue

        # ----------------------------------------------------------
        # Check raw files
        # ----------------------------------------------------------

        if not presence.get(source_id, False):

            logger.warning(
                "Skipping source '%s': "
                "no .txt files found in %s",
                source_id,
                source.raw_dir,
            )

            continue

        # ----------------------------------------------------------
        # Get all TXT files
        # ----------------------------------------------------------

        raw_files = source.raw_files

        logger.info(
            "Processing source '%s'",
            source_id,
        )

        logger.info(
            "Found %d raw files in %s",
            len(raw_files),
            source.raw_dir,
        )

        # ----------------------------------------------------------
        # Process every TXT file
        # ----------------------------------------------------------

        for raw_file in raw_files:

            logger.info(
                "Reading: %s",
                raw_file,
            )

            raw_text = _read_raw(raw_file)

            # ------------------------------------------------------
            # Clean
            # ------------------------------------------------------

            cleaned = clean_text(raw_text)

            if not cleaned:

                logger.warning(
                    "File '%s' produced no content "
                    "after cleaning; skipping.",
                    raw_file,
                )

                continue

            # ------------------------------------------------------
            # Chunk
            # ------------------------------------------------------

            chunks = chunk_document(
                cleaned,
                source_id=source_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                extra_metadata={
                    "title": source.title,
                    "publisher": source.publisher,
                    "url": source.url,
                    "license": source.license,
                    "specialty": source.specialty,
                    "source_file": os.path.basename(raw_file),
                },
            )

            logger.info(
                "  -> %d chunks from %s",
                len(chunks),
                os.path.basename(raw_file),
            )

            all_chunks.extend(chunks)

    # --------------------------------------------------------------
    # Check chunks
    # --------------------------------------------------------------

    if not all_chunks:

        raise RuntimeError(
            "Ingestion produced zero chunks. "
            "Check the knowledge_base/raw folders, "
            "TXT files, source registry, and license approvals."
        )

    logger.info(
        "Total chunks created: %d",
        len(all_chunks),
    )

    # --------------------------------------------------------------
    # Generate embeddings
    # --------------------------------------------------------------

    logger.info(
        "Embedding %d total chunks with model '%s'...",
        len(all_chunks),
        model_name,
    )

    embedder = EmbeddingModel(
        model_name=model_name
    )

    texts = [
        chunk.text
        for chunk in all_chunks
    ]

    embeddings = embedder.embed_texts(
        texts,
        show_progress_bar=True,
    )

    logger.info(
        "Embedding shape: %s",
        embeddings.shape,
    )

    # --------------------------------------------------------------
    # Build FAISS vector store
    # --------------------------------------------------------------

    store = VectorStore(
        dimension=embeddings.shape[1]
    )

    store.build(
        embeddings,
        [
            chunk.to_dict()
            for chunk in all_chunks
        ],
    )

    # --------------------------------------------------------------
    # Save vector store
    # --------------------------------------------------------------

    store.save(output_dir)

    logger.info(
        "Ingestion complete."
    )

    logger.info(
        "Vector store saved to: %s",
        output_dir,
    )

    return store


# ----------------------------------------------------------------------
# Read raw text
# ----------------------------------------------------------------------

def _read_raw(path: str) -> str:

    with open(
        path,
        "r",
        encoding="utf-8",
        errors="replace",
    ) as file:

        return file.read()


# ----------------------------------------------------------------------
# CLI argument parser
# ----------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description="MedAgentX RAG ingestion pipeline"
    )

    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help=(
            "Source folder to ingest. "
            "Examples: Diabetes, Heart_Disease. "
            "Repeat this argument for multiple sources."
        ),
    )

    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
    )

    parser.add_argument(
        "--model-name",
        type=str,
        default=DEFAULT_MODEL_NAME,
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_VECTOR_STORE_DIR,
    )

    parser.add_argument(
        "--skip-license-check",
        action="store_true",
        help=(
            "Bypass license approval checks "
            "(testing only)."
        ),
    )

    return parser


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():

    parser = _build_arg_parser()

    args = parser.parse_args()

    run_ingestion_pipeline(
        source_ids=args.sources,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        model_name=args.model_name,
        output_dir=args.output_dir,
        skip_license_check=args.skip_license_check,
    )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()