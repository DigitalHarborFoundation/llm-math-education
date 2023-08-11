import numpy as np
import pandas as pd
import pytest

from llm_math_education import embedding_utils, retrieval


def mock_get_openai_embeddings(input_text_list, *args, **kwargs):
    return [np.random.random(size=embedding_utils.EMBEDDING_DIM) for _ in input_text_list]


@pytest.fixture
def retrieval_db_path(tmp_path, monkeypatch):
    # Creates a retrieval database that can be used by multiple tests
    monkeypatch.setattr("llm_math_education.embedding_utils.get_openai_embeddings", mock_get_openai_embeddings)

    df = pd.DataFrame(
        [
            {
                "categorical_var": "A",
                "group_var": 1,
                "text": "Test text 1.",
            },
            {
                "categorical_var": "B",
                "group_var": 1,
                "text": "Test text 2.",
            },
            {
                "categorical_var": "C",
                "group_var": 2,
                "text": "Test text 3.",
            },
        ],
    )
    db = retrieval.RetrievalDb(tmp_path, "conftestDb", "text", df)
    db.create_embeddings()
    db.save_df()
    return tmp_path


@pytest.fixture
def retrieval_db(retrieval_db_path) -> retrieval.RetrievalDb:
    db = retrieval.RetrievalDb(retrieval_db_path, "conftestDb", "text")
    return db


@pytest.fixture(autouse=True)
def no_openai(monkeypatch):
    """Remove Embedding and ChatCompletion creations during all tests.

    This is probably not necessary given the dotenv configuration."""
    monkeypatch.delattr("openai.Embedding.create")
    monkeypatch.delattr("openai.ChatCompletion.create")
