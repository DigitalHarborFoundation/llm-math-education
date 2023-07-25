import numpy as np
import pandas as pd
import pytest

from llm_math_education import embedding_utils, retrieval


def mock_get_openai_embeddings(input_text_list, *args, **kwargs):
    return [np.random.random(size=embedding_utils.EMBEDDING_DIM) for _ in input_text_list]


def test_RetrievalDb(tmp_path, monkeypatch):
    monkeypatch.setattr("llm_math_education.embedding_utils.get_openai_embeddings", mock_get_openai_embeddings)

    df = pd.DataFrame(
        [
            {
                "categorical_var": "A",
                "text": "Test text.",
            },
            {
                "categorical_var": "B",
                "text": "Test\n\ntext.",
            },
        ],
    )
    db = retrieval.RetrievalDb(tmp_path, "testDb", "text", df)
    assert not db.embedding_filepath.exists()
    assert not db.df_filepath.exists()
    db.create_embeddings()
    assert db.embedding_filepath.exists()
    assert db.embedding_mat.shape == (len(df), embedding_utils.EMBEDDING_DIM)
    db.save_df()
    assert db.df_filepath.exists()

    db = retrieval.RetrievalDb(tmp_path, "testDb", "text")
    assert len(db.df) == len(df)

    distances = db.compute_string_distances("Test query.")
    assert len(distances) == len(df)
    top_df = db.get_top_df(distances, k=1)
    assert len(top_df) == 1

    # test non-existent db loading
    with pytest.raises(ValueError):
        retrieval.RetrievalDb(tmp_path, "testDb2", "text")
