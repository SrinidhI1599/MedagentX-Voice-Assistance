from __future__ import annotations

import logging
from typing import List, Sequence

import numpy as np


logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = 32


# ------------------------------------------------------------
# Embedding Model
# ------------------------------------------------------------

class EmbeddingModel:

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        device: str | None = None,
        normalize_embeddings: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.normalize_embeddings = normalize_embeddings

        self._model = None

    # --------------------------------------------------------
    # Load model lazily
    # --------------------------------------------------------

    @property
    def model(self):

        if self._model is None:

            from sentence_transformers import SentenceTransformer

            logger.info(
                "Loading embedding model: %s",
                self.model_name,
            )

            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
            )

        return self._model

    # --------------------------------------------------------
    # Embedding dimension
    # --------------------------------------------------------

    @property
    def dimension(self) -> int:

        return self.model.get_sentence_embedding_dimension()

    # --------------------------------------------------------
    # Embed multiple texts
    # --------------------------------------------------------

    def embed_texts(
        self,
        texts: Sequence[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
        show_progress_bar: bool = False,
    ) -> np.ndarray:

        if not texts:

            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        embeddings = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )

        return embeddings.astype(np.float32)

    # --------------------------------------------------------
    # Embed a single query
    # --------------------------------------------------------

    def embed_query(
        self,
        query: str,
    ) -> np.ndarray:

        return self.embed_texts(
            [query]
        )[0]