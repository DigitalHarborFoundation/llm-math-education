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
    """Wrapper class with info about how retrieved texts should be incorporated in a prompt.

    See `prompt_utils.PromptManager`.
    """

    def __init__(
        self,
        db: RetrievalDb,
        max_tokens: int = 1000,
        max_texts: int = 1000,
        prefix: str = "",
        suffix: str = "",
        join_string: str = "\n",
        use_parent_text: bool = False,
        parent_group_cols: list[str] = [],
        parent_sort_cols: list[str] = [],
    ):
        self.db = db
        self.max_tokens = max_tokens
        self.max_texts = max_texts
        self.prefix = prefix
        self.suffix = suffix
        self.join_string = join_string

        # configure parent retrieval
        self.use_parent_text = use_parent_text
        self.parent_join_string = "\n"
        self.parent_group_cols = parent_group_cols
        self.parent_sort_cols = parent_sort_cols

    def copy(self, **kwargs) -> DbInfo:
        """Create a copy of this DbInfo, overriding the keyword args with new values if provided.

        Returns:
            DbInfo: Newly instantiated copy.
        """
        for expected_key in ["max_tokens", "prefix", "suffix"]:
            if expected_key not in kwargs:
                kwargs[expected_key] = getattr(self, expected_key)
        return DbInfo(self.db, **kwargs)

    def get_fill_string_from_distances(self, distances: np.array):
        sort_inds = get_distance_sort_indices(distances)
        used_inds = set()
        texts = []
        total_tokens = 0
        for ind in sort_inds:
            if ind in used_inds:
                continue
            if self.use_parent_text:
                token_budget = self.max_tokens - total_tokens
                text, n_tokens, new_used_inds = self.get_parent_text(ind, token_budget)
                used_inds.update(new_used_inds)
            else:
                text, n_tokens = self.get_single_text(ind)
                used_inds.add(ind)
            if total_tokens + n_tokens > self.max_tokens:
                break
            total_tokens += n_tokens
            texts.append(text)
            if len(texts) >= self.max_texts:
                break
        fill_string = self.prefix + self.join_string.join(texts) + self.suffix
        return fill_string

    def get_single_text(self, ind: int):
        row = self.db.df.iloc[ind]
        text = row[self.db.embed_col]
        n_tokens = row[self.db.n_tokens_col]
        return text, n_tokens

    def get_parent_text(self, ind: int, token_budget: int):
        """
        Intuition of "parent document" retriever is to retrieve for inclusion in a prompt the "parent" document,
        similar to including docs on either "side" as additional context.

        Read more: https://python.langchain.com/docs/modules/data_connection/retrievers/parent_document_retriever

        Args:
            ind (int): Most semantically relevant index to retrieve parents of.
        """
        df = self.db.df
        row = df.iloc[ind]
        and_cond = np.ones(len(df), dtype=bool)
        for col in self.parent_group_cols:
            cond = df[col] == row[col]
            and_cond = np.logical_and(and_cond, cond)
        parent = df[and_cond]
        if self.parent_sort_cols is not None and len(self.parent_sort_cols) > 1:
            parent = parent.sort_values(by=self.parent_sort_cols)
        # include a variable amount of context based on the given token_budget
        # preference ranking implemented here:
        #  - all docs
        #  - up to token_budget docs from target_ind - 0
        total_tokens = parent[self.db.n_tokens_col].sum()
        if row[self.db.n_tokens_col] > token_budget:
            # simple case: NOTHING will fit in the token budget!
            return None
        elif total_tokens <= token_budget:
            # simple case: if all tokens in budget, no extra work
            rows = parent
        else:
            target_ind_val = df.index[ind]
            before = parent.loc[:target_ind_val]
            # see: https://stackoverflow.com/a/37872823
            cumulative_token_counts = before.loc[::-1, self.db.n_tokens_col].cumsum()[::-1]
            rows = before[cumulative_token_counts <= token_budget]
        assert len(rows) >= 1
        new_used_inds = {df.index.get_loc(new_ind) for new_ind in rows.index}
        assert ind in new_used_inds
        texts = rows[self.db.embed_col]
        n_tokens_rows = rows[self.db.n_tokens_col]
        text = self.parent_join_string.join(texts)
        # note this will underestimate the true number of tokens, due to whatever parent_join_string is
        n_tokens = n_tokens_rows.sum()
        return text, n_tokens, new_used_inds
