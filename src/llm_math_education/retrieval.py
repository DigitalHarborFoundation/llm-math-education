from __future__ import annotations

import collections.abc
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from llm_math_education import embedding_utils


class RetrievalDb:
    """In-memory retrieval helper class.

    When creating new embeddings:
        self.create_embeddings()
        self.save_df()

    When loading existing embeddings:
        self.load()

    """

    def __init__(
        self,
        embedding_dir: Path,
        db_name: str,
        embed_col: str,
        df: pd.DataFrame | None = None,
        n_tokens_col: str = "n_tokens",
    ):
        self.embedding_dir = embedding_dir
        self.db_name = db_name

        self.df_filepath = self.embedding_dir / f"{self.db_name}_df.parquet"
        self.embedding_filepath = self.embedding_dir / f"{self.db_name}_embed.npy"

        self.embed_col = embed_col
        if df is None:
            self.load()
        else:
            self.df = df
            self.normalize_strings()
        assert self.embed_col in self.df.columns

        self.n_tokens_col = n_tokens_col
        if n_tokens_col not in self.df.columns:
            self.compute_token_counts()

    def normalize_strings(self):
        self.df[self.embed_col] = self.df[self.embed_col].map(normalize_text)

    def compute_token_counts(self):
        token_counts = embedding_utils.get_token_counts(self.df[self.embed_col])
        self.df[self.n_tokens_col] = token_counts

    def create_embeddings(self):
        embedding_list = embedding_utils.batch_embed_texts(self.df[self.embed_col], self.df[self.n_tokens_col])
        self.embedding_mat = np.concatenate([e.reshape(1, -1) for e in embedding_list], axis=0)
        np.save(self.embedding_filepath, self.embedding_mat)

    def save_df(self):
        self.df.to_parquet(self.df_filepath)

    def load(self):
        if not self.df_filepath.exists():
            raise ValueError(f"Trying to load a dataframe from non-existent path: {self.df_filepath}")
        self.df = pd.read_parquet(self.df_filepath)
        self.embedding_mat = np.load(self.embedding_filepath)

    def compute_embedding_distances(self, query_embedding: np.array) -> np.array:
        if query_embedding.shape[0] != 1:
            query_embedding = query_embedding.reshape(1, -1)
        distances = scipy.spatial.distance.cdist(query_embedding, self.embedding_mat, metric="cosine")[0]
        return distances

    def compute_string_distances(self, query_str: str) -> np.array:
        embedding_list = embedding_utils.get_openai_embeddings([normalize_text(query_str)])
        query_embedding = embedding_list[0]
        return self.compute_embedding_distances(query_embedding)

    def iterate_query_embeddings(
        self,
        query_embedding_list: collections.abc.Iterable[np.array],
    ) -> collections.abc.Generator[np.array]:
        for query_embedding in query_embedding_list:
            yield self.compute_embedding_distances(query_embedding)

    def get_top_df(self, distances: np.array, k: int = 5) -> pd.DataFrame:
        sort_inds = np.argsort(distances)
        top_k_indices = sort_inds[:k]
        top_k_scores = distances[top_k_indices]
        assert top_k_indices.shape == top_k_scores.shape
        return self.df.iloc[top_k_indices]


def get_distance_sort_indices(distances: np.array) -> np.array:
    return np.argsort(distances)


def normalize_text(text: str) -> str:
    return text.replace("\n", " ").strip()


class DbInfo:
    def __init__(self, db: RetrievalDb, max_tokens: int = 1000, prefix: str = "", suffix: str = ""):
        self.db = db
        self.max_tokens = max_tokens
        self.prefix = prefix
        self.suffix = suffix

    def copy(self, **kwargs) -> DbInfo:
        """Create a copy of this DbInfo, overriding the keyword args with new values if provided.

        Returns:
            DbInfo: Newly instantiated copy.
        """
        for expected_key in ["max_tokens", "prefix", "suffix"]:
            if expected_key not in kwargs:
                kwargs[expected_key] = getattr(self, expected_key)
        return DbInfo(self.db, **kwargs)
