import re

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


def test_DbInfo(retrieval_db):
    db_info = retrieval.DbInfo(retrieval_db, max_tokens=1)
    assert db_info.max_tokens == 1
    db_info2 = db_info.copy()
    assert db_info2.max_tokens == 1
    db_info3 = db_info.copy(max_tokens=2)
    assert db_info3.max_tokens == 2


def test_DbInfo_get_fill_string_from_distances(retrieval_db):
    test_prefix = "test_prefix"
    test_suffix = "test_suffix"
    db_info = retrieval.DbInfo(retrieval_db, prefix=test_prefix, suffix=test_suffix, max_texts=1)
    distances = np.array([0] + [1] * (len(db_info.db.df) - 1))
    assert len(distances) == len(db_info.db.df)
    fill_string = db_info.get_fill_string_from_distances(distances)
    assert fill_string.startswith(test_prefix)
    assert fill_string.endswith(test_suffix)
    assert db_info.db.df[db_info.db.embed_col].iloc[0] in fill_string
    assert all(db_info.db.df[db_info.db.embed_col].iloc[1:].map(lambda t: t not in fill_string))


def test_DbInfo_get_single_text(retrieval_db):
    db_info = retrieval.DbInfo(retrieval_db)
    text, n_tokens = db_info.get_single_text(0)
    assert text == db_info.db.df[db_info.db.embed_col].iloc[0]
    assert n_tokens > 0


def test_DbInfo_get_parent_text(retrieval_db):
    db_info = retrieval.DbInfo(
        retrieval_db,
        max_texts=1,
        use_parent_text=True,
        parent_group_cols=["group_var"],
        parent_sort_cols=["categorical_var"],
    )
    # first, verify that with a budget of 0 no texts are returned
    assert db_info.get_parent_text(0, 0) is None

    # second, verify normal case
    text, n_tokens, used_inds = db_info.get_parent_text(0, 1000)
    assert used_inds == {0, 1}
    expected_parent_rows = db_info.db.df[db_info.db.df["group_var"] == 1]
    expected_text = "\n".join(expected_parent_rows[db_info.db.embed_col])
    assert text == expected_text, f"Parent text was {text}"
    assert n_tokens == expected_parent_rows[db_info.db.n_tokens_col].sum()

    # here, we retrieve the second entry in a parent text but we still get back the first and second together
    distances = np.array([1, 0, 1])
    fill_string = db_info.get_fill_string_from_distances(distances)
    assert fill_string == expected_text

    # check for non-duplicate retrieval
    db_info.max_texts = 2
    distances = np.array([0, 0, 1])
    fill_string = db_info.get_fill_string_from_distances(distances)
    assert len(re.findall(expected_text, fill_string)) == 1, f"Duplicate retrieval in {fill_string}"

    # third, we verify token budget backoff behavior
    # here, we give only enough budget to get the target text
    token_budget = db_info.db.df[db_info.db.n_tokens_col].iloc[0]
    text, n_tokens, used_inds = db_info.get_parent_text(0, token_budget)
    assert text == db_info.db.df[db_info.db.embed_col].iloc[0]
    assert n_tokens == token_budget
    assert used_inds == {0}

    # here, we give enough budget for two texts
    token_budget = db_info.db.df[db_info.db.n_tokens_col].iloc[0:1].sum()
    text, n_tokens, used_inds = db_info.get_parent_text(0, token_budget)
    assert len(used_inds - {0, 1}) == 0
