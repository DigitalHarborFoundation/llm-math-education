# Integration tests for the streamlit app,
# including testing some of the associated utilities in `streamlit_app`

from llm_math_education import retrieval_strategies
from streamlit_app import auth_utils, data_utils


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


def test_auth_utils():
    auth_token = auth_utils.generate_auth_token()
    hashed_auth_token = auth_utils.passwd_hash(auth_token)
    assert auth_utils.passwd_check(hashed_auth_token, auth_token)
