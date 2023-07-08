import collections.abc
from pathlib import Path

import numpy as np
import openai
import pandas as pd
import scipy
import tiktoken


class EmbeddingDb:
    """In-memory embedding retrieval helper class.

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
        df: pd.DataFrame,
        embed_col: str,
        n_tokens_col: str = "n_tokens",
        embedding_model: str = "text-embedding-ada-002",
        max_tokens_per_request: int = 8191,
    ):
        self.embedding_dir = embedding_dir
        self.db_name = db_name

        self.df = df
        self.embed_col = embed_col
        assert embed_col in df.columns
        self.normalize_strings()
        self.n_tokens_col = n_tokens_col
        if n_tokens_col not in df.columns:
            self.compute_token_counts()

        # config
        self.embedding_model = embedding_model
        self.max_tokens_per_request = max_tokens_per_request

        self.df_filepath = self.embedding_dir / f"{self.db_name}_df.parquet"
        self.embedding_filepath = self.embedding_dir / f"{self.db_name}_embed.npy"

    def normalize_strings(self):
        self.df[self.embed_col] = self.df[self.embed_col].map(normalize_text)

    def compute_token_counts(self):
        tokenizer = tiktoken.encoding_for_model(self.embedding_model)
        token_counts = []
        for string in self.df[self.embed_col]:
            token_counts.append(tokenizer.encode(string))
        self.df[self.n_tokens_col] = token_counts

    def _get_embeddings(texts: list[str], embedding_model: str) -> list[np.array]:
        result = openai.Embedding.create(input=texts, engine=embedding_model)
        embedding_list = [np.array(d["embedding"]) for d in result.data]
        return embedding_list

    def create_embeddings(self):
        """_summary_

        Args:
            embedding_model (str, optional): OpenAI embedding model to use. Defaults to "text-embedding-ada-002".
            max_tokens_per_request (int, optional): How to chunk inputs. Defaults to 8191, per OpenAI docs for Ada.
        """
        # TODO
        # texts = [row.db_string.replace("\n", " ") for row in embed_df.itertuples()]
        curr_batch_token_count = 0
        texts = []
        embedding_list = []
        for text, n_tokens in zip(self.db[self.embed_col], self.db[self.n_tokens_col]):
            if curr_batch_token_count + n_tokens > self.max_tokens_per_request:
                embedding_list.extend(EmbeddingDb._get_embeddings(texts, self.embedding_model))
                texts = [text]
                curr_batch_token_count = 0
            else:
                texts.append(text)
                curr_batch_token_count += n_tokens
        if len(texts) > 0:
            embedding_list.extend(EmbeddingDb._get_embeddings(texts, self.embedding_model))
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

    def compute_string_distances(self, query_str: str) -> np.array():
        result = openai.Embedding.create(input=[query_str], engine=self.embedding_model)
        embedding_list = [np.array(d["embedding"]) for d in result.data]
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
