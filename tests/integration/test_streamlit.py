from llm_math_education import retrieval_strategies
from streamlit_app import data_utils


def test_data_utils():
    retrieval_db_map = data_utils.create_retrieval_db_map()
    assert len(retrieval_db_map) > 1

    slot_map = data_utils.create_hint_default_retrieval_slot_map()
    assert len(slot_map) > 1

    retrieval_options_map = data_utils.create_mathqa_retrieval_options_map(retrieval_db_map)
    assert len(retrieval_options_map) > 0
    assert any(
        type(retrieval_strategy) is not retrieval_strategies.NoRetrievalStrategy
        for retrieval_strategy in retrieval_options_map.values()
    )
