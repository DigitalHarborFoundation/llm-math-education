import conftest

from llm_math_education import embedding_utils


def test_get_token_counts():
    n_tokens_list = embedding_utils.get_token_counts(["test", "test "])
    assert n_tokens_list == [1, 2]


def test_get_openai_embeddings(monkeypatch):
    monkeypatch.setattr("llm_math_education.embedding_utils.get_openai_embeddings", conftest.mock_get_openai_embeddings)
    result = embedding_utils.get_openai_embeddings(["test"])
    assert len(result) == 1
    assert result[0].shape[0] == embedding_utils.EMBEDDING_DIM


def test_batch_embed_texts(monkeypatch):
    monkeypatch.setattr("llm_math_education.embedding_utils.get_openai_embeddings", conftest.mock_get_openai_embeddings)

    max_tokens = embedding_utils.MAX_TOKENS_PER_REQUEST
    input_text_list = ["test"] * (max_tokens + 1)
    embedding_list = embedding_utils.batch_embed_texts(
        input_text_list,
        embedding_utils.get_token_counts(input_text_list),
    )
    assert len(embedding_list) == len(input_text_list)
    assert all(emb.shape[0] == embedding_utils.EMBEDDING_DIM for emb in embedding_list)
