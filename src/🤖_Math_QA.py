import locale
import time
from datetime import datetime

import notebook.auth.security
import openai
import streamlit as st

from llm_math_education import prompt_utils, retrieval_strategies
from llm_math_education.prompts import mathqa
from streamlit_app import custom_textarea

# from pathlib import Path
# from llm_math_education import chat_db

RETRIEVAL_OPTIONS_MAP = {
    "None": retrieval_strategies.NoRetrievalStrategy,
    "Rori micro-lessons only": retrieval_strategies.NoRetrievalStrategy,
    "Rori + Pre-algebra textbook": retrieval_strategies.NoRetrievalStrategy,
}
RETRIEVAL_OPTIONS_LIST = list(RETRIEVAL_OPTIONS_MAP.keys())


def get_header_message():
    return {
        "role": "assistant",
        "content": "header message",
        "timestamp": int(datetime.now().timestamp()),
    }


def get_avatar(role: str) -> str:
    if role == "user":
        return "🧑‍🎓"
    elif role == "assistant":
        return "🤖"
    return None


def update_temperature_setting():
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    temperature_str = st.session_state["temperature_text_input"]
    try:
        new_temperature = locale.atof(temperature_str)
        if new_temperature < 0 or new_temperature > 1:
            raise ValueError("Invalid temperature range.")
        st.session_state["temperature"] = new_temperature
        st.session_state["temperature_text_input_valid"] = True
    except ValueError:
        st.session_state["temperature_text_input_valid"] = False


def update_retrieval_setting():
    retrieval_str = st.session_state["retrieval_radio"]
    st.session_state["retrieval_strategy"] = RETRIEVAL_OPTIONS_MAP[retrieval_str]


if "is_authorized" not in st.session_state or not st.session_state.is_authorized:
    # attempt to authenticate from a URL parameter
    query_params = st.experimental_get_query_params()
    st.session_state.is_authorized = False
    st.session_state.auth_token_provided = False
    if "auth_token" in query_params and "AUTH_TOKEN" in st.secrets:
        st.session_state.auth_token_provided = True
        auth_token = query_params["auth_token"][0]
        if notebook.auth.security.passwd_check(st.secrets["AUTH_TOKEN"], auth_token):
            st.session_state.is_authorized = True
    if not st.session_state.is_authorized:
        # block the rest of the page!
        pass


openai.api_key = st.secrets["OPENAI_API_KEY"]

# settings
setting_defaults = {
    "temperature": 0.7,
    "temperature_text_input": "0.7",
    "temperature_text_input_valid": True,
    "retrieval_strategy": RETRIEVAL_OPTIONS_MAP[RETRIEVAL_OPTIONS_LIST[0]],
    "retrieval_radio": RETRIEVAL_OPTIONS_LIST[0],
}
for key_name, default_value in setting_defaults.items():
    if key_name not in st.session_state:
        st.session_state[key_name] = default_value

if "temperature" not in st.session_state:
    st.session_state["temperature"] = float(setting_defaults["temperature_text_input"])

st.set_page_config(page_title="ChatGPT for middle-school math education", page_icon="🤖")
st.markdown(
    """# Math Question-Answering

Ask math questions.
""",
)
st.write(f"Authorized: {st.session_state.is_authorized}")
# chat_log = chat_db.ChatLog(Path("data/chat_logs"))

with st.expander("System prompts"):
    st.markdown(
        """ChatGPT accepts a _prompt_, a text description of the expected behavior.

The prompt can be edited to adjust that behavior.

After each query, the associated prompt is included in a drop-down (including any retrieved information).""",
    )
    prompt_manager = prompt_utils.PromptSelector(mathqa.intro_prompts)
    text_options = [
        prompt_utils.PromptSelector.convert_conversation_to_string(messages)
        for messages in prompt_manager.get_intro_prompt_message_lists()
    ]
    _, system_textarea_key = custom_textarea.insert_textarea_with_selectbox(
        text_options,
        prompt_manager.get_intro_prompt_pretty_names(),
        "",
        "mathqa_system_prompt",
        custom_option_name="Custom prompt",
    )
    try:
        intro_prompt_messages = prompt_utils.PromptSelector.convert_string_to_conversation(
            st.session_state[system_textarea_key],
        )
    except Exception:
        st.warning("Syntax error in prompt.")
    # TODO set intro prompt messages in a PromptManager or similar

# initialize history
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [get_header_message()]

for message in st.session_state.chat_messages:
    with st.chat_message(message["role"], avatar=get_avatar(message["role"])):
        st.markdown(message["content"])

user_query = st.chat_input(
    "Ask a question about math" if len(st.session_state.chat_messages) <= 1 else "Ask a follow-up question",
)
if user_query:
    # st.write(f"User wrote: {user_query}")
    user_message = {
        "role": "user",
        "content": user_query,
        "timestamp": int(datetime.now().timestamp()),
    }
    st.session_state.chat_messages.append(user_message)

    # display user's new query
    with st.chat_message("user", avatar=get_avatar("user")):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar=get_avatar("assistant")):
        message_placeholder = st.empty()
        displayed_message = ""

        with st.spinner(""):
            time.sleep(1)  # imitate API delay
        assistant_message = {
            "role": "assistant",
            "content": "Not yet implemented\n\nThis response contains newlines.",
            "timestamp": int(datetime.now().timestamp()),
        }
        response = assistant_message["content"]
        for char in response:
            displayed_message += char
            if char == "\n":
                time.sleep(0.06)
            elif char == " ":
                time.sleep(0.04)
            else:
                time.sleep(0.005)
            message_placeholder.markdown(displayed_message + "▌")
        message_placeholder.markdown(displayed_message)

        st.session_state.chat_messages.append(assistant_message)

# Sidebar
with st.sidebar:
    st.markdown("Options")
    if st.button("Start a new session"):  # , disabled=len(st.session_state.chat_messages) <= 1):
        st.session_state.chat_messages = [get_header_message()]
    st.markdown(f"Conversation length: {len(st.session_state.chat_messages)}")
    # TODO compute token counts as well

    with st.expander("Advanced"):
        st.text_input("Temperature:", key="temperature_text_input", on_change=update_temperature_setting)
        if not st.session_state["temperature_text_input_valid"]:
            st.warning("Invalid temperature setting; should be a decimal between 0 and 1.")

        st.radio("Retrieval:", RETRIEVAL_OPTIONS_LIST, key="retrieval_radio", on_change=update_retrieval_setting)
