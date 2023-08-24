import locale
import logging
import time
from datetime import datetime

import openai
import pandas as pd
import streamlit as st

from llm_math_education import prompt_utils
from llm_math_education.prompts import mathqa
from streamlit_app import auth_utils, chat_utils, custom_textarea, data_utils

MAX_TOKENS = 4096
SAMPLE_QUERY_CATEGORIES = ["Algebra", "Geometry"]
STUDENT_QUERY_SELECTION_STRING = "(Choose a student question from MathNation)"


def get_header_message() -> dict[str, object]:
    """This is the header message that is shown to the user, which is not used as a system or assistant message."""
    return {
        "role": "assistant",
        "content": "Hi there! I'm here to help you with any math questions you have! What's your question?",
        "timestamp": int(datetime.now().timestamp()),
    }


def restart_chat_session():
    st.session_state.chat_messages = [get_header_message()]
    st.session_state.prompt_manager.clear_stored_messages()
    # note: can only do this state update in a callback / before the app is built!
    st.session_state.student_query_selectbox = STUDENT_QUERY_SELECTION_STRING


def session_restart_button_clicked():
    restart_chat_session()


def student_query_selectbox_changed():
    if st.session_state.student_query_selectbox != STUDENT_QUERY_SELECTION_STRING:
        st.session_state.student_query_selectbox_new_value = st.session_state.student_query_selectbox
        # TODO might want to restart the current session here...


def process_user_query(user_query: str):
    user_message = {
        "role": "user",
        "content": user_query,
        "timestamp": int(datetime.now().timestamp()),
    }
    st.session_state.chat_messages.append(user_message)

    # display user's new query
    with st.chat_message("user", avatar=chat_utils.get_avatar("user")):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar=chat_utils.get_avatar("assistant")):
        message_placeholder = st.empty()
        displayed_message = ""

        with st.spinner(""):
            messages = st.session_state.prompt_manager.build_query(user_query)
            if st.session_state.show_expert_controls:
                slot_fill_dict = st.session_state.prompt_manager.most_recent_slot_fill_dict
                # currently, we only show the retrieved texts until the next page reload
                with st.expander("Retrieved texts:"):
                    s = ""
                    for key, value in slot_fill_dict.items():
                        if value == "":
                            value = "(none)"
                        s += "#### " + key + ":\n\n" + value.replace("\n", "\n\n") + "\n\n\n"
                    st.markdown(s)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
                temperature=st.session_state.temperature,
                request_timeout=20,
            )
            assistant_message = completion["choices"][0]["message"]
            assert "role" in assistant_message and "content" in assistant_message
            st.session_state.prompt_manager.add_stored_message(assistant_message)
            # TODO add timestamp to message: int(datetime.now().timestamp())
        response = assistant_message["content"]
        for char in response:
            displayed_message += char
            if char == "\n":
                time.sleep(0.06)
            elif char == " ":
                time.sleep(0.03)
            else:
                time.sleep(0.004)
            message_placeholder.markdown(displayed_message + "▌")
        message_placeholder.markdown(displayed_message)

        st.session_state.chat_messages.append(assistant_message)


def update_temperature_setting():
    locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
    temperature_str = st.session_state["temperature_text_input"]
    try:
        new_temperature = locale.atof(temperature_str)
        if new_temperature < 0 or new_temperature > 2:
            raise ValueError("Invalid temperature range.")
        st.session_state["temperature"] = new_temperature
        st.session_state["temperature_text_input_valid"] = True
    except ValueError:
        st.session_state["temperature_text_input_valid"] = False


def update_retrieval_setting():
    retrieval_str = st.session_state["retrieval_radio"]
    logging.info(
        f"Updated retrieval strategy from {st.session_state.retrieval_strategy.__class__.__name__} to {st.session_state.retrieval_options_map[retrieval_str].__class__.__name__}.",
    )
    st.session_state["retrieval_strategy"] = st.session_state.retrieval_options_map[retrieval_str]
    st.session_state.prompt_manager.set_retrieval_strategy(st.session_state.retrieval_strategy)


def instantiate_session():
    # settings
    setting_defaults = {
        "temperature": 1.0,
        "temperature_text_input": "1.0",
        "temperature_text_input_valid": True,
        "retrieval_radio": data_utils.RETRIEVAL_OPTIONS_LIST[0],
        "student_query_selectbox_new_value": None,
        "show_expert_controls": False,
    }
    # initialize all values in the settings dict
    # (happens only on the first run each session)
    for key_name, default_value in setting_defaults.items():
        if key_name not in st.session_state:
            st.session_state[key_name] = default_value

    if "prompt_manager" not in st.session_state:
        st.session_state.prompt_manager = prompt_utils.PromptManager()

    query_params = st.experimental_get_query_params()
    if "show_expert_controls" in query_params:
        if query_params["show_expert_controls"][0].lower() == "true":
            st.session_state.show_expert_controls = True

    if "student_queries" not in st.session_state:
        # load the student question data
        if data_utils.DATA_DIR.exists():
            mn_general_student_queries_filepath = data_utils.DATA_DIR / "mn_general_student_queries.csv"
            query_df = pd.read_csv(mn_general_student_queries_filepath)
            st.session_state["student_queries"] = [
                {
                    "category": "Geometry" if row.subject_name == "Geometry" else "Algebra",
                    "query": row.post_content.strip().replace("[Continued:]", "\n"),
                }
                for row in query_df.sample(frac=1, random_state=87896).itertuples()
                if row.is_respondable_query == "general"
            ]
            st.session_state["student_queries"].insert(
                0,
                {
                    "category": None,
                    "query": STUDENT_QUERY_SELECTION_STRING,
                },
            )
        else:
            st.session_state["student_queries"] = [
                {
                    "category": None,
                    "query": "(Failed to load student questions.)",
                },
            ]
    # load dbs for retrieval
    was_data_loaded = data_utils.cache_retrieval_data_in_session()
    if was_data_loaded:
        st.session_state.retrieval_strategy = next(iter(st.session_state.retrieval_options_map.values()))
        st.session_state.prompt_manager.set_retrieval_strategy(st.session_state.retrieval_strategy)

    if "is_openai_key_set" not in st.session_state or not st.session_state.is_openai_key_set:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        st.session_state.is_openai_key_set = True


def build_app():
    # build the actual app
    st.markdown(
        """# Math Question-Answering with ChatGPT

Ask math questions, receive curriculum-based answers.

This demo explores the feasibility of providing a math-related dialogues to answer middle-school student questions.

Start with a question, and then ask follow-up questions.""",
    )
    st.selectbox(
        "If you need some ideas, try a real student question:",
        [q["query"] for q in st.session_state["student_queries"]],
        key="student_query_selectbox",
        on_change=student_query_selectbox_changed,
    )

    if st.session_state.show_expert_controls:
        st.write("You can also customize the prompt that the dialogue system uses.")

        with st.expander("System prompts"):
            st.markdown(
                """ChatGPT accepts a _prompt_, a text description of the expected behavior.

The prompt can be edited to adjust that behavior.

After each query, the associated prompt is included in a drop-down (including any retrieved information).""",
            )
            prompt_selector = prompt_utils.PromptSelector(mathqa.intro_prompts)
            text_options = [
                prompt_utils.PromptSelector.convert_conversation_to_string(messages)
                for messages in prompt_selector.get_intro_prompt_message_lists()
            ]
            custom_textarea.insert_textarea_with_selectbox(
                text_options,
                prompt_selector.get_intro_prompt_pretty_names(),
                "System prompt",
                "mathqa_system_prompt_selectbox",
                "mathqa_system_prompt_textarea",
                custom_option_name="Custom prompt",
            )
            # set the intro prompt
            try:
                intro_prompt_messages = prompt_utils.PromptSelector.convert_string_to_conversation(
                    st.session_state["mathqa_system_prompt_textarea"],
                )
            except Exception:
                st.warning("Syntax error in prompt.")
            st.session_state.prompt_manager.set_intro_messages(intro_prompt_messages)
    else:
        # use the default prompt
        prompt_selector = prompt_utils.PromptSelector(mathqa.intro_prompts)
        intro_prompt_messages = prompt_selector.get_default_intro_prompt()["messages"]
        st.session_state.prompt_manager.set_intro_messages(intro_prompt_messages)

    # initialize history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [get_header_message()]

    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"], avatar=chat_utils.get_avatar(message["role"])):
            st.markdown(message["content"])

    new_chat_input_value = st.chat_input(
        "Ask a question about math",  # we would prefer to update this conditionally, but: https://github.com/streamlit/streamlit/issues/7054
        key="chat_input_key",
    )

    # first check to see if this is from the checkbox
    user_query = None
    if st.session_state.student_query_selectbox_new_value is not None:
        user_query = st.session_state.student_query_selectbox_new_value
        st.session_state.student_query_selectbox_new_value = None
    elif new_chat_input_value:
        assert new_chat_input_value == st.session_state.chat_input_key
        user_query = new_chat_input_value
    if user_query is not None and user_query.strip() != "":
        # note: we can't do this in a callback, unfortunately,
        # as we need the app to be already built when we create the new elements
        process_user_query(user_query.strip())

    # Build sidebar
    with st.sidebar:
        st.markdown("### Options")
        st.button(
            "Start new chat",
            disabled=len(st.session_state.chat_messages) <= 1,
            on_click=session_restart_button_clicked,
        )

        if st.session_state.show_expert_controls:
            with st.expander("Advanced"):
                st.markdown(f"Conversation length: {len(st.session_state.chat_messages)}")
                st.markdown(
                    f"Used tokens: {st.session_state.prompt_manager.compute_stored_token_counts()} / {MAX_TOKENS}",
                )
                st.text_input("Temperature:", key="temperature_text_input", on_change=update_temperature_setting)
                if not st.session_state["temperature_text_input_valid"]:
                    st.warning("Invalid temperature setting; should be a decimal between 0 and 2.")

                st.radio(
                    "Retrieval:",
                    data_utils.RETRIEVAL_OPTIONS_LIST,
                    key="retrieval_radio",
                    on_change=update_retrieval_setting,
                )


st.set_page_config(page_title="ChatGPT for middle-school math education", page_icon="🤖")
if auth_utils.check_is_authorized(allow_openai_key=True):
    instantiate_session()
    build_app()
