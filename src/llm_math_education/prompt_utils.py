from __future__ import annotations

import re

from llm_math_education import retrieval_strategies

VALID_ROLES = ["user", "assistant", "system"]


class PromptSelector:
    """PromptSelector provides utilities to enumerate and choose prompts."""

    def __init__(self, intro_prompt_dict: dict):
        self.intro_prompt_dict = intro_prompt_dict
        self.pretty_name_to_id_map = {
            t[1]["pretty_name"] if "pretty_name" in t[1] else f"Prompt {i}": t[0]
            for i, t in enumerate(self.intro_prompt_dict)
        }

    def get_intro_prompt_pretty_names(self):
        pretty_name_list = []
        for i, prompt_info in enumerate(self.intro_prompt_dict.values()):
            pretty_name = prompt_info["pretty_name"] if "pretty_name" in prompt_info else f"Prompt {i}"
            pretty_name_list.append(pretty_name)
        return pretty_name_list

    def get_intro_prompt_message_lists(self):
        message_lists = []
        for prompt_info in self.intro_prompt_dict.values():
            message_lists.append(prompt_info["messages"])
        return message_lists

    def convert_conversation_to_string(messages):
        conversation_string = ""
        for message in messages:
            conversation_string += message["role"].upper() + ":\n"
            conversation_string += message["content"] + "\n"
        return conversation_string

    def convert_string_to_conversation(conversation_string: str) -> list[dict[str, str]]:
        messages = []
        message = {
            "content": "",
        }
        for line in conversation_string.split("\n"):
            possible_role = line[:-1].lower()
            if possible_role in VALID_ROLES:
                if "role" in message:
                    message["content"] = message["content"].strip()
                    messages.append(message)
                    message = {
                        "content": "",
                    }
                message["role"] = possible_role
            else:
                message["content"] += line + "\n"
        if "role" in message:
            message["content"] = message["content"].strip()
            messages.append(message)
        return messages


class PromptManager:
    """Stores prompts and generates message lists for passing to the OpenAI API."""

    def __init__(self):
        self.intro_messages: list[dict[str, str]] = []
        self.retrieval_strategy: retrieval_strategies.RetrievalStrategy = retrieval_strategies.NoRetrievalStrategy()
        self.stored_messages: list[dict[str, str]] = []

    def set_intro_messages(self, intro_messages: list[dict[str, str]]) -> PromptManager:
        self.intro_messages = intro_messages
        return self

    def set_retrieval_strategy(self, retrieval_strategy: retrieval_strategies.RetrievalStrategy) -> PromptManager:
        self.retrieval_strategy = retrieval_strategy
        return self

    def add_stored_message(self, message: dict[str, str]) -> PromptManager:
        self.stored_messages.append(message)
        return self

    def clear_stored_messages(self) -> PromptManager:
        self.stored_messages.clear()
        return self

    def build_query(self, user_query: str, previous_messages: list[dict[str, str]] | None = None):
        if previous_messages is None:
            previous_messages = self.stored_messages
        messages = []
        if len(previous_messages) == 0:
            # this is a new query
            messages = [message.copy() for message in self.intro_messages]
            for message in messages:
                expected_slots = PromptManager.identify_slots(message["content"])
                if len(expected_slots) > 0:
                    slot_fill_dict = self.retrieval_strategy.do_retrieval(
                        expected_slots,
                        user_query,
                        messages,
                    )
                    assert len(slot_fill_dict) == len(expected_slots), "Unexpected fill provided."
                    try:
                        message["content"] = message["content"].format(**slot_fill_dict)
                    except KeyError:
                        raise KeyError(f"Failed to fill {expected_slots} with {slot_fill_dict}.")
            # store the intro messages
            self.stored_messages.extend(messages)
        else:
            # not a new query,
            # so include the previous messages as context
            messages += previous_messages
        # TODO identify if the user query has slots to fill
        user_message = {
            "role": "user",
            "content": user_query,
        }
        self.stored_messages.append(user_message)
        messages.append(user_message)
        return messages

    def compute_stored_token_counts(self) -> int:
        total_token_count = 0
        for message in self.stored_messages:
            content = message["content"]
            token_count = len(content.split())
            total_token_count += token_count
        return total_token_count

    def identify_slots(prompt_string):
        expected_slots = re.findall(r"{[^{} ]+}", prompt_string)
        return [slot[1:-1] for slot in expected_slots]
