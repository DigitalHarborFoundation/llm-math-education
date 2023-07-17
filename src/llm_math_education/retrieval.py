import collections.abc
from pathlib import Path
from typing import Optional

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
        df: Optional[pd.DataFrame],
        embed_col: str,
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


def normalize_text(text: str) -> str:
    return text.replace("\n", " ").strip()