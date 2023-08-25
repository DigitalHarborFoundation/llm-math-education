from __future__ import annotations

import re

from llm_math_education import embedding_utils, retrieval_strategies

VALID_ROLES: list[str] = ["user", "assistant", "system"]


class PromptSelector:
    """PromptSelector provides utilities to enumerate and choose prompts.

    Prompts are stored in dictionaries in the `prompts` modules.
    """

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

    def get_intro_prompt_message_lists(self) -> list[dict[str, str]]:
        message_lists = []
        for prompt_info in self.intro_prompt_dict.values():
            message_lists.append(prompt_info["messages"])
        return message_lists

    def get_default_intro_prompt(self) -> dict[str]:
        return self.intro_prompt_dict[next(iter(self.intro_prompt_dict.keys()))]

    def convert_conversation_to_string(messages):
        conversation_string = ""
        for message in messages:
            conversation_string += message["role"].upper() + ":\n"
            conversation_string += message["content"] + "\n"
        return conversation_string

    def convert_string_to_conversation(conversation_string: str) -> list[dict[str, str]]:
        """Given a string representing a conversation, convert into the expected messages list format.

        Follows a pretty basic convention, defined in this implementation.

        Args:
            conversation_string (str): String representing a conversation.

        Returns:
            list[dict[str, str]]: List of messages, each with a "role" and "content".
        """
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
        self.most_recent_slot_fill_dict: dict[str, str] = {}
        self.recent_slot_fill_dict: list[dict[str, str]] = []

    def set_intro_messages(self, intro_messages: list[dict[str, str]]) -> PromptManager:
        self.intro_messages = intro_messages
        return self

    def set_retrieval_strategy(self, retrieval_strategy: retrieval_strategies.RetrievalStrategy) -> PromptManager:
        self.retrieval_strategy = retrieval_strategy
        return self

    def get_retrieval_strategy(self) -> retrieval_strategies.RetrievalStrategy:
        return self.retrieval_strategy

    def add_stored_message(self, message: dict[str, str]) -> PromptManager:
        self.stored_messages.append(message)
        return self

    def clear_stored_messages(self) -> PromptManager:
        self.stored_messages.clear()
        return self

    def build_query(
        self,
        user_query: str | None = None,
        previous_messages: list[dict[str, str]] | None = None,
        query_for_retrieval_context: str | None = None,
    ) -> list[dict[str, str]]:
        """Given a user_query (or the `intro_messages` set on this PromptManager), build a set of messages to pass to the OpenAI API.

        Args:
            user_query (str | None, optional): If provided, will construct a new user message from this user. Defaults to None.
            previous_messages (list[dict[str, str]] | None, optional): If provided, will continue a conversation. Defaults to None.
            query_for_retrieval_context (str | None, optional): If provided, this is used for any RetrievalStrategies that require querying. Defaults to None, meaning the user_query or the most recent user message will be used.

        Raises:
            KeyError: If the given RetrievalStrategy doesn't fill all the identified slots in the prompts.

        Returns:
            list[dict[str, str]]: List of messages, to pass to the OpenAI API.
        """
        if previous_messages is None:
            previous_messages = self.stored_messages
        if len(previous_messages) == 0:
            # this is a new query
            messages = [message.copy() for message in self.intro_messages]
            self.stored_messages.extend(messages)
        else:
            # not a new query,
            # so include the previous messages as context
            messages = [message.copy() for message in previous_messages]
        if user_query is not None:
            user_message = {
                "role": "user",
                "content": user_query,
            }
            messages.append(user_message)
            self.stored_messages.append(user_message)

        should_remove_user_query_message = False
        if query_for_retrieval_context is None:
            query_for_retrieval_context = ""
        for message in messages[::-1]:
            expected_slots = PromptManager.identify_slots(message["content"])
            if len(expected_slots) > 0:
                slot_fill_dict = self.retrieval_strategy.do_retrieval(
                    expected_slots,
                    query_for_retrieval_context,
                    messages,
                )
                self.most_recent_slot_fill_dict = slot_fill_dict
                self.recent_slot_fill_dict.append(slot_fill_dict)
                assert len(slot_fill_dict) == len(expected_slots), "Unexpected fill provided."
                if "user_query" in slot_fill_dict and user_query is not None:
                    # special case: fill user_query slots with the current user_query
                    slot_fill_dict["user_query"] = user_query
                    should_remove_user_query_message = True
                try:
                    message["content"] = message["content"].format(**slot_fill_dict)
                except KeyError:
                    raise KeyError(f"Failed to fill {expected_slots} with {slot_fill_dict}.")
            else:
                self.recent_slot_fill_dict.append({})
            if query_for_retrieval_context == "" and message["role"] == "user":
                # use as retrieval context the most recent user message
                # TODO rethink this, providing a more flexible way to specify the retrieval context
                query_for_retrieval_context = message["content"]
        self.recent_slot_fill_dict = self.recent_slot_fill_dict[::-1]
        if should_remove_user_query_message:
            self.stored_messages.pop()
            assert messages[-1]["content"] == user_query
            messages = messages[:-1]
        return messages

    def compute_stored_token_counts(self) -> int:
        token_counts = embedding_utils.get_token_counts([message["content"] for message in self.stored_messages])
        total_token_count = sum(token_counts)
        return total_token_count

    def identify_slots(prompt_string: str) -> list[str]:
        """Uses a regex to identify missing slots in a prompt_string.

        More advanced slot formatting is not supported.

        Args:
            prompt_string (str): The prompt itself, with format-style slots to fill e.g. "This is a prompt with a slot: {slot_to_fill}"

        Returns:
            list[str]: List of identified slots.
        """
        expected_slots = re.findall(r"{[^{} ]+}", prompt_string)
        return sorted({slot[1:-1] for slot in expected_slots})
