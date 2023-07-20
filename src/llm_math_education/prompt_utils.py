VALID_ROLES = ["user", "assistant", "system"]


class PromptManager:
    def __init__(self, intro_prompt_dict: dict):
        self.intro_prompt_dict = intro_prompt_dict

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
