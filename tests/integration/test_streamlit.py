# Integration tests for the streamlit app,
# including testing some of the associated utilities in `streamlit_app`

from llm_math_education import prompt_utils, retrieval_strategies
from llm_math_education.prompts import hints as hint_prompts
from streamlit_app import auth_utils, data_utils


def test_hint_generation():
    hint_prompt_manager = prompt_utils.PromptManager()
    slot_map = data_utils.create_hint_default_retrieval_slot_map()
    retrieval_strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(slot_map)
    hint_prompt_manager.set_retrieval_strategy(retrieval_strategy)

    hint_prompt_manager.get_retrieval_strategy().update_map(
        {
            "question": "Which true? A) True B) False",
            "correct_answer": "A",
            "incorrect_answer": "B",
            "lesson": "Booleans are fun",
        },
    )
    for hint_type in hint_prompts.intro_prompts.keys():
        hint_prompt_manager.clear_stored_messages()
        intro_messages = hint_prompts.intro_prompts[hint_type]["messages"]
        hint_prompt_manager.set_intro_messages(intro_messages)
        messages = hint_prompt_manager.build_query(None)
        assert len(messages) >= 1

        for expected_fill in ["rori_microlesson_texts", "openstax_subsection_texts", "question"]:
            assert any(
                expected_fill in slot_fill_dict and len(slot_fill_dict[expected_fill].strip()) > 0
                for slot_fill_dict in hint_prompt_manager.recent_slot_fill_dict
            ), f"{expected_fill} should have non-empty fill in {hint_prompt_manager.recent_slot_fill_dict}"

        followup_messages = hint_prompt_manager.build_query("Follow-up question")
        assert len(followup_messages) == len(messages) + 1


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
