import json
import logging
import uuid
from datetime import datetime
from pathlib import Path


class ChatLog:
    def __init__(self, log_dir: Path, filename: str = ""):
        if filename == "":
            # use today's date
            curr_date_str = datetime.now().strftime("%Y%m%d")
            filename = f"chat_log_{curr_date_str}.ndjson"
        self.log_dir = log_dir
        self.filename = filename
        self.log_file = self.log_dir / self.filename
        self.logger = logging.getLogger("llm_math_education.chat_db.ChatLog")
        self.chat_id_dict = None

    def log_chat_completion(self, chat_id: str, messages_list: list[dict], completion_dict: dict):
        combined = {
            "chat_id": chat_id,
            "messages": messages_list,
            "completion": completion_dict,
            "logged_timestamp": datetime.now().timestamp(),
        }
        self.log_dict(combined)

    def log_dict(self, dict_to_log: dict):
        with open(self.log_file, "a") as outfile:
            outfile.write(json.dumps(dict_to_log) + "\n")

    def list_previous_logs(self, pattern: str = "*.ndjson"):
        previous_log_filepaths = []
        for filepath in self.log_dir.glob(pattern):
            previous_log_filepaths.append(self.log_dir / filepath)
        return previous_log_filepaths

    def load_previous_chats(self, use_cached: bool = True) -> dict:
        """Loads previous chats.

        Args:
            use_cached (bool, optional): If previously-loaded chats should be used. Defaults to True.

        Returns:
            dict: Map of chat_id -> saved contents dict
        """
        if self.chat_id_dict is not None and use_cached:
            return self.chat_id_dict
        previous_log_filepaths = self.list_previous_logs()
        self.logger.info(f"Identified {len(previous_log_filepaths)} log files.")
        chat_id_dict = {}
        for log_filepath in previous_log_filepaths:
            with open(log_filepath) as infile:
                for line in infile:
                    d = json.loads(line)
                    if "chat_id" not in d:
                        continue
                    chat_id = d["chat_id"]
                    if chat_id not in chat_id_dict or d["logged_timestamp"] > chat_id_dict[chat_id]["logged_timestamp"]:
                        # take the most recent chat_id info
                        chat_id_dict[chat_id] = d
        self.chat_id_dict = chat_id_dict
        return self.chat_id_dict

    def get_matching_chat_ids(self, messages: list[dict]):
        assert len(messages) > 0, "Continuation expects at least one initial message."
        matching_chat_ids = []
        for saved_chat in self.chat_id_dict.values():
            if saved_chat["messages"][: len(messages)] == messages:
                matching_chat_ids.append(saved_chat["chat_id"])
        return matching_chat_ids


def generate_chat_id():
    curr_date = datetime.now().strftime("%Y%m%d")
    curr_timestamp = datetime.now().timestamp()
    return f"{uuid.uuid4()}_{curr_date}_{curr_timestamp}"
