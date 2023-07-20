from llm_math_education import prompt_utils


def test_conversion():
    test_string = """SYSTEM:
System prompt.
Multiple lines.
USER:
User query."""
    messages = prompt_utils.PromptManager.convert_string_to_conversation(test_string)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System prompt.\nMultiple lines.", messages[0]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "User query.", messages[1]


def test_PromptManager():
    test_prompts = {
        "test_prompt_1": {
            "pretty_name": "Prompt 1",
            "expected_slots": [],
            "messages": [
                {
                    "role": "system",
                    "content": "System prompt 1.",
                },
            ],
        },
        "test_prompt_2": {
            "pretty_name": "Prompt 2",
            "expected_slots": [],
            "messages": [
                {
                    "role": "system",
                    "content": "System prompt 2.",
                },
            ],
        },
    }
    pm = prompt_utils.PromptManager(test_prompts)
    assert pm.get_intro_prompt_pretty_names() == ["Prompt 1", "Prompt 2"]
    message_lists = pm.get_intro_prompt_message_lists()
    assert message_lists[0] == test_prompts["test_prompt_1"]["messages"]
