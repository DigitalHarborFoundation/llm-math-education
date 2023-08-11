from llm_math_education import prompt_utils, retrieval_strategies


def test_conversion():
    test_string = """SYSTEM:
System prompt.
Multiple lines.
USER:
User query."""
    messages = prompt_utils.PromptSelector.convert_string_to_conversation(test_string)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System prompt.\nMultiple lines.", messages[0]
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "User query.", messages[1]


def test_PromptSelector():
    test_prompts = {
        "test_prompt_1": {
            "pretty_name": "Prompt 1",
            "messages": [
                {
                    "role": "system",
                    "content": "System prompt 1.",
                },
            ],
        },
        "test_prompt_2": {
            "pretty_name": "Prompt 2",
            "messages": [
                {
                    "role": "system",
                    "content": "System prompt 2.",
                },
            ],
        },
    }
    pm = prompt_utils.PromptSelector(test_prompts)
    assert pm.get_intro_prompt_pretty_names() == ["Prompt 1", "Prompt 2"]
    message_lists = pm.get_intro_prompt_message_lists()
    assert message_lists[0] == test_prompts["test_prompt_1"]["messages"]

    assert pm.get_default_intro_prompt()["pretty_name"] == "Prompt 1"


def test_PromptManager():
    pm = prompt_utils.PromptManager()

    # test basic query
    messages = pm.build_query("Test")
    assert len(messages) == 1
    assert messages[0]["content"] == "Test"
    assert len(pm.stored_messages) == 1
    assert pm.stored_messages[0]["content"] == "Test"
    pm.clear_stored_messages()

    # test conversation start with system message
    test_intro_messages = [
        {
            "role": "system",
            "content": "System",
        },
    ]
    messages = pm.set_intro_messages(test_intro_messages).build_query("User")
    assert len(messages) == 2
    assert messages[0]["role"] == "system", messages
    assert messages[0]["content"] == "System"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "User"
    pm.clear_stored_messages()

    # test conversation continuation
    previous_messages = messages
    previous_messages.append(
        {
            "role": "assistant",
            "content": "Assistant",
        },
    )
    messages = pm.set_intro_messages(test_intro_messages).build_query("User2", previous_messages=previous_messages)
    assert len(messages) == 4
    assert messages[2]["content"] == "Assistant"
    assert messages[3]["content"] == "User2"


def test_PromptManager_retrieval():
    test_intro_messages = [
        {
            "role": "system",
            "content": "Test {slot1} {slot2}",
        },
    ]
    retrieval_strategy = retrieval_strategies.StaticRetrievalStrategy("Fill")
    pm = prompt_utils.PromptManager().set_intro_messages(test_intro_messages).set_retrieval_strategy(retrieval_strategy)
    messages = pm.build_query("User")
    assert len(messages) == 2
    assert messages[0]["content"] == "Test Fill Fill", messages[0]
    assert pm.intro_messages[0]["content"] == "Test {slot1} {slot2}"


def test_identify_slots():
    slots = prompt_utils.PromptManager.identify_slots("test {test1} {test2} {test3 }")
    assert slots == ["test1", "test2"]

    slots = prompt_utils.PromptManager.identify_slots("test {test1} {test1}")
    assert slots == ["test1"]


def test_user_query_replacement():
    test_intro_messages = [
        {
            "role": "user",
            "content": "Question: {user_query}",
        },
    ]
    messages = prompt_utils.PromptManager().set_intro_messages(test_intro_messages).build_query("Test")
    assert len(messages) == 1
    assert messages[0]["content"] == "Question: Test"

    # this behavior requires exactly the slot name "user_query"
    # compare to the below behavior, which produces 2 messages
    test_intro_messages = [
        {
            "role": "user",
            "content": "Question: {other_slot}",
        },
    ]
    messages = prompt_utils.PromptManager().set_intro_messages(test_intro_messages).build_query("Test")
    assert len(messages) == 2
    assert messages[0]["content"] == "Question: "
    assert messages[1]["content"] == "Test"
