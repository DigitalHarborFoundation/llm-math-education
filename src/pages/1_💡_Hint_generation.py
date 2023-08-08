import time

import openai
import streamlit as st

from llm_math_education import prompt_utils
from streamlit_app import auth_utils, chat_utils, data_utils

QUESTION_SELECTBOX_DEFAULT_STRING = "(Choose a question from a Rori micro-lesson)"
HINT_TYPE_BUTTON_LABELS_MAP = {
    "hint_sequence": "Get a hint sequence",
    "slip_correction": "Correct a slip",
    "misconception": "Describe a misconception",
    "comparative_hint": "Compare this problem to a worked example",
}


def question_selectbox_changed():
    if st.session_state.question_selectbox != QUESTION_SELECTBOX_DEFAULT_STRING:
        display_name = st.session_state.question_selectbox
        question_df = data_utils.load_hint_problem_data()
        selected = question_df[question_df.display_name == display_name]
        assert len(selected) == 1
        selected = selected.iloc[0]
        st.session_state.question_text_area = selected.question
        st.session_state.incorrect_answer_text_input = selected.incorrect_answer
        st.session_state.correct_answer_text_input = selected.answer
        st.session_state.lesson_text_area = selected.lesson_trimmed


def hint_chat_input_changed():
    st.session_state.hint_chat_input_new_value = st.session_state.hint_chat_input


def hint_type_button_clicked(hint_type: str):
    st.session_state.hint_type_button_new_value = hint_type


def create_new_hint(hint_type: str):
    with st.chat_message("assistant", avatar=chat_utils.get_avatar("assistant")):
        message_placeholder = st.empty()

        with st.spinner(""):
            st.session_state.hint_prompt_manager.clear_stored_messages()
            correct_answer = st.session_state.correct_answer_text_input.strip()
            incorrect_answer = st.session_state.incorrect_answer_text_input.strip()
            question = st.session_state.question_text_area.strip()
            lesson = st.session_state.lesson_text_area.strip()
            # TODO build query correctly
            user_query = lesson + question + correct_answer + incorrect_answer + hint_type
            messages = st.session_state.hint_prompt_manager.build_query(user_query)
            # TODO show the generated prompt if expert controls enabled

            # completion = openai.ChatCompletion.create(
            #    model="gpt-3.5-turbo-0613",
            #    messages=messages,
            # )
            # assistant_message = completion["choices"][0]["message"]
            time.sleep(0.4)  # imitate API delay
            assistant_message = {
                "role": "assistant",
                "content": f"Generated a {hint_type} hint from {len(messages)} messages",
            }
            assert "role" in assistant_message and "content" in assistant_message
            st.session_state.hint_prompt_manager.add_stored_message(assistant_message)
        response = assistant_message["content"]
        for displayed_message in chat_utils.stream_text_response(response):
            message_placeholder.markdown(displayed_message)

        st.session_state.hint_chat_messages.append(assistant_message)


def process_followup_query(user_query: str):
    user_message = {
        "role": "user",
        "content": user_query,
    }
    st.session_state.hint_chat_messages.append(user_message)
    with st.chat_message("user", avatar=chat_utils.get_avatar("user")):
        st.markdown(user_query)

    with st.chat_message("assistant", avatar=chat_utils.get_avatar("assistant")):
        message_placeholder = st.empty()

        with st.spinner(""):
            messages = st.session_state.hint_prompt_manager.build_query(user_query)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
            )
            assistant_message = completion["choices"][0]["message"]
            assert "role" in assistant_message and "content" in assistant_message
        response = assistant_message["content"]
        for displayed_message in chat_utils.stream_text_response(response):
            message_placeholder.markdown(displayed_message)

        st.session_state.hint_chat_messages.append(assistant_message)
        st.session_state.hint_prompt_manager.add_stored_message(assistant_message)


def instantiate_session():
    # settings
    setting_defaults = {
        "hint_type_button_new_value": None,
        "hint_chat_input_new_value": None,
        "show_expert_controls": False,
    }
    # initialize all values in the settings dict
    # (happens only on the first run each session)
    for key_name, default_value in setting_defaults.items():
        if key_name not in st.session_state:
            st.session_state[key_name] = default_value

    if "hint_prompt_manager" not in st.session_state:
        st.session_state.hint_prompt_manager = prompt_utils.PromptManager()
        data_utils.load_session_data()
        default_retrieval_strategy = next(iter(st.session_state.retrieval_options_map.values()))
        st.session_state.hint_prompt_manager.set_retrieval_strategy(default_retrieval_strategy)

    query_params = st.experimental_get_query_params()
    if "show_expert_controls" in query_params:
        if query_params["show_expert_controls"][0].lower() == "true":
            st.session_state.show_expert_controls = True

    if "is_openai_key_set" not in st.session_state or not st.session_state.is_openai_key_set:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        st.session_state.is_openai_key_set = True


def build_app():
    st.markdown(
        """# Hint generation

Generate hints for practice problems given an incorrect answer.""",
    )
    question_df = data_utils.load_hint_problem_data()
    st.selectbox(
        "Choose a practice problem:",
        [QUESTION_SELECTBOX_DEFAULT_STRING] + question_df.display_name.to_list(),
        key="question_selectbox",
        on_change=question_selectbox_changed,
    )
    with st.expander("Lesson and worked example"):
        st.text_area(
            "Lesson and worked example text:",
            key="lesson_text_area",
            label_visibility="collapsed",
        )
    st.text_area(
        "Practice problem:",
        key="question_text_area",
    )
    c1, c2 = st.columns(2)
    with c1:
        st.text_input(
            "Student's incorrect answer:",
            key="incorrect_answer_text_input",
        )
    with c2:
        st.text_input(
            "Correct answer:",
            key="correct_answer_text_input",
        )
    are_buttons_enabled = (
        st.session_state.correct_answer_text_input.strip() != ""
        and st.session_state.incorrect_answer_text_input.strip() != ""
        and st.session_state.question_text_area.strip() != ""
    )
    if not are_buttons_enabled:
        st.warning(
            f"Select a practice problem above, then choose one of {len(HINT_TYPE_BUTTON_LABELS_MAP)} hint types.",
        )
    elif st.session_state.correct_answer_text_input.strip() == st.session_state.incorrect_answer_text_input.strip():
        st.warning("To generate a hint, the student's answer can't match the correct answer.")
        are_buttons_enabled = False
    with st.container():
        for hint_type, button_label in HINT_TYPE_BUTTON_LABELS_MAP.items():
            st.button(
                button_label,
                key=f"{hint_type}_button",
                on_click=hint_type_button_clicked,
                args=(hint_type,),
                disabled=not are_buttons_enabled,
            )

    # initialize history
    if "hint_chat_messages" not in st.session_state:
        st.session_state.hint_chat_messages = []

    for message in st.session_state.hint_chat_messages:
        with st.chat_message(message["role"], avatar=chat_utils.get_avatar(message["role"])):
            st.markdown(message["content"])

    if st.session_state.hint_type_button_new_value is not None:
        hint_type = st.session_state.hint_type_button_new_value
        st.session_state.hint_type_button_new_value = None
        create_new_hint(hint_type)
    elif st.session_state.hint_chat_input_new_value is not None:
        user_query = st.session_state.hint_chat_input_new_value
        st.session_state.hint_chat_input_new_value = None
        process_followup_query(user_query)

    if len(st.session_state.hint_chat_messages) > 0:
        # only display chat input once an initial hint has been generated
        st.chat_input(
            "Ask a follow-up question about the problem",
            key="hint_chat_input",
            on_submit=hint_chat_input_changed,
        )


st.set_page_config(
    page_title="ChatGPT for middle-school math education - Hint generation",
    page_icon="💡",
)

if auth_utils.check_is_authorized():
    instantiate_session()
    build_app()
