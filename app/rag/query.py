from __future__ import annotations

import argparse
import json
import os

from .embeddings import EmbeddingModel
from .vector_store import VectorStore


DEFAULT_VECTOR_STORE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "knowledge_base",
        "vector_store",
    )
)


def load_metadata(vector_store_dir: str):
    metadata_path = os.path.join(
        vector_store_dir,
        "metadata.json",
    )

    with open(
        metadata_path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def search(
    query: str,
    top_k: int = 5,
    vector_store_dir: str = DEFAULT_VECTOR_STORE_DIR,
):
    """
    Search the FAISS vector store and return the
    most relevant medical chunks.
    """

    # ---------------------------------------------------------
    # Load vector store
    # ---------------------------------------------------------

    store = VectorStore.load(vector_store_dir)

    # ---------------------------------------------------------
    # Create embedding model
    # ---------------------------------------------------------

    embedder = EmbeddingModel()

    query_embedding = embedder.embed_query(query)

    # ---------------------------------------------------------
    # Search FAISS
    # ---------------------------------------------------------

    results = store.search(
        query_embedding,
        top_k=top_k,
    )

    return results


def main():

    parser = argparse.ArgumentParser(
        description="Query MedAgentX FAISS vector store"
    )

    parser.add_argument(
        "query",
        type=str,
        help="Medical question to search",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of chunks to retrieve",
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("MEDAGENT RAG RETRIEVAL")
    print("=" * 70)

    print(f"\nQuestion:\n{args.query}")

    results = search(
        query=args.query,
        top_k=args.top_k,
    )

    print("\n" + "=" * 70)
    print(f"TOP {len(results)} RETRIEVED CHUNKS")
    print("=" * 70)

    for i, result in enumerate(results, start=1):

        print(f"\n{'=' * 70}")
        print(f"RESULT {i}")
        print(f"{'=' * 70}")

        print(f"Score: {result.get('score')}")

        print(
            f"Source: "
            f"{result.get('source_id')}"
        )

        print(
            f"File: "
            f"{result.get('source_file')}"
        )

        print(
            f"Title: "
            f"{result.get('title')}"
        )

        print("\nText:")

        print(
            result.get("text", "")
        )


if __name__ == "__main__":
    main()