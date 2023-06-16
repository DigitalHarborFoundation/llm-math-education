from llm_math_education import chat_db


def test_generate_chat_id():
    chat_id = chat_db.generate_chat_id()
    assert chat_id is not None and len(chat_id) > 0
    assert chat_id != chat_db.generate_chat_id()


def test_ChatLog(tmp_path):
    chat_log = chat_db.ChatLog(tmp_path)
    assert chat_log.load_previous_chats() == {}

    chat_id = chat_db.generate_chat_id()
    messages_list = [
        {"role": "user", "content": "Initial user test message"},
    ]
    completion_dict = {
        "id": "chatcmpl-AAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "object": "chat.completion",
        "created": 1686870764,
        "model": "gpt-3.5-turbo",
        "choices": {},
        "usage": {},
    }
    chat_log.log_chat_completion(chat_id, messages_list, completion_dict)
    assert chat_log.log_file.exists()

    previous_logs = chat_log.list_previous_logs()
    assert len(previous_logs) == 1
    assert previous_logs[0] == chat_log.log_file

    assert chat_log.load_previous_chats() == {}
    assert chat_log.load_previous_chats(use_cached=False) is not None
    assert len(chat_log.chat_id_dict) == 1

    assert chat_log.get_matching_chat_ids(messages_list) == [chat_id]
    assert chat_log.get_matching_chat_ids([{"role": "user", "content": "Non-existent test message"}]) == []
