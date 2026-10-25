import time

import openai

CHAT_MODEL = "gpt-6-luna"


def get_assistant_message(messages: list[dict], **kwargs) -> dict[str, str]:
    """Request a chat completion, returning the assistant message as a plain dict."""
    completion = openai.chat.completions.create(model=CHAT_MODEL, messages=messages, **kwargs)
    message = completion.choices[0].message
    return {"role": message.role, "content": message.content}


def get_avatar(role: str) -> str | None:
    if role == "user":
        return "🧑‍🎓"
    elif role == "assistant":
        return "🤖"
    return None


def stream_text_response(response: str):
    displayed_message = ""
    for char in response:
        displayed_message += char
        if char == "\n":
            time.sleep(0.06)
        elif char == " ":
            time.sleep(0.03)
        else:
            time.sleep(0.004)
        yield displayed_message + "▌"
    yield displayed_message
