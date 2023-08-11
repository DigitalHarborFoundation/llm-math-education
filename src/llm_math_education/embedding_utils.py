import functools

import numpy as np
import openai
import tiktoken

EMBEDDING_DIM = 1536
MAX_TOKENS_PER_REQUEST = 8191
EMBEDDING_MODEL = "text-embedding-ada-002"


def get_token_counts(text_list: list[str]) -> list[int]:
    tokenizer = tiktoken.encoding_for_model(EMBEDDING_MODEL)
    token_counts = []
    for string in text_list:
        token_counts.append(len(tokenizer.encode(string)))
    return token_counts


def get_openai_embeddings(texts: list[str], embedding_model: str = EMBEDDING_MODEL) -> list[np.array]:
    return get_openai_embeddings_cached(tuple(texts), embedding_model=embedding_model)


@functools.lru_cache(maxsize=512, typed=True)
def get_openai_embeddings_cached(texts: tuple[str], embedding_model: str = EMBEDDING_MODEL) -> list[np.array]:
    result = openai.Embedding.create(input=texts, engine=embedding_model)
    embedding_list = [np.array(d["embedding"]) for d in result.data]
    return embedding_list


def batch_embed_texts(input_text_list: list[str], n_tokens_list: list[int]) -> list[np.array]:
    curr_batch_token_count = 0
    texts = []
    embedding_list = []
    for text, n_tokens in zip(input_text_list, n_tokens_list):
        if curr_batch_token_count + n_tokens > MAX_TOKENS_PER_REQUEST:
            embedding_list.extend(get_openai_embeddings(texts, EMBEDDING_MODEL))
            texts = [text]
            curr_batch_token_count = 0
        else:
            texts.append(text)
            curr_batch_token_count += n_tokens
    if len(texts) > 0:
        embedding_list.extend(get_openai_embeddings(texts, EMBEDDING_MODEL))
    return embedding_list
