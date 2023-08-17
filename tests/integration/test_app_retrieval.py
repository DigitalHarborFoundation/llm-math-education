# Test retrieval with the actual app data
import conftest

from llm_math_education import prompt_utils, retrieval, retrieval_strategies


def test_parent_retrieval(monkeypatch, pytestconfig):
    monkeypatch.setattr("llm_math_education.embedding_utils.get_openai_embeddings", conftest.mock_get_openai_embeddings)

    app_data_dir = pytestconfig.rootpath / "data" / "app_data"
    assert app_data_dir.exists()

    openstax_db = retrieval.RetrievalDb(app_data_dir, "openstax_subsection", "db_string")
    openstax_subsection_db_info = retrieval.DbInfo(
        openstax_db,
        max_tokens=3000,
        max_texts=1,
        prefix="",
        use_parent_text=True,
        parent_group_cols=["chapter", "section"],
        parent_sort_cols=["index"],
    )
    strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(
        {
            "openstax_subsection_texts": openstax_subsection_db_info,
        },
    )

    pm = prompt_utils.PromptManager()
    pm.set_retrieval_strategy(strategy)
    messages = pm.build_query("{openstax_subsection_texts}")

    assert len(pm.recent_slot_fill_dict) == 1
    slot_fill_dict = pm.recent_slot_fill_dict[0]
    assert "openstax_subsection_texts" in slot_fill_dict

    fill = slot_fill_dict["openstax_subsection_texts"].strip()
    assert len(fill) > 0

    assert fill == messages[0]["content"]
