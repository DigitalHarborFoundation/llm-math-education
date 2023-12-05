import openai
import streamlit as st

from llm_math_education import prompt_utils, retrieval_strategies
from llm_math_education.prompts import hints as hint_prompts
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
    create_new_hint(hint_type)


def process_hint_query(messages: list[dict]):
    # show the generated prompt if expert controls enabled
    if st.session_state.show_expert_controls:
        with st.expander("Prompt"):
            prompt = prompt_utils.PromptSelector.convert_conversation_to_string(
                st.session_state.hint_prompt_manager.stored_messages,
            )
            prompt = prompt.replace("\n", "\n\n")
            st.markdown(prompt)
    with st.chat_message("assistant", avatar=chat_utils.get_avatar("assistant")):
        message_placeholder = st.empty()
        with st.spinner(""):
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-0613",
                messages=messages,
            )
            assistant_message = completion["choices"][0]["message"]
            assert "role" in assistant_message and "content" in assistant_message
            st.session_state.hint_prompt_manager.add_stored_message(assistant_message)
        response = assistant_message["content"]
        for displayed_message in chat_utils.stream_text_response(response):
            message_placeholder.markdown(displayed_message)

        st.session_state.hint_chat_messages.append(assistant_message)


def create_new_hint(hint_type: str):
    st.session_state.hint_chat_messages = []
    st.session_state.hint_prompt_manager.clear_stored_messages()
    correct_answer = st.session_state.correct_answer_text_input.strip()
    incorrect_answer = st.session_state.incorrect_answer_text_input.strip()
    question = st.session_state.question_text_area.strip()
    lesson = st.session_state.lesson_text_area.strip()
    st.session_state.hint_prompt_manager.get_retrieval_strategy().update_map(
        {
            "question": question,
            "correct_answer": correct_answer,
            "incorrect_answer": incorrect_answer,
            "lesson": lesson,
        },
    )
    intro_messages = hint_prompts.intro_prompts[hint_type]["messages"]
    st.session_state.hint_prompt_manager.set_intro_messages(intro_messages)
    messages = st.session_state.hint_prompt_manager.build_query(None)
    st.session_state.new_hint_request_messages = messages


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
        "new_hint_request_messages": None,
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
        slot_map = data_utils.create_hint_default_retrieval_slot_map()
        retrieval_strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(slot_map)
        st.session_state.hint_prompt_manager.set_retrieval_strategy(retrieval_strategy)

    query_params = st.experimental_get_query_params()
    if "show_expert_controls" in query_params:
        if query_params["show_expert_controls"][0].lower() == "true":
            st.session_state.show_expert_controls = True

    if "is_openai_key_set" not in st.session_state or not st.session_state.is_openai_key_set:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        st.session_state.is_openai_key_set = True


def build_app():
    with st.sidebar:
        st.markdown(
            """
### About this demo

This demo was produced with the [Learning Engineering Virtual Institute](https://learning-engineering-virtual-institute.org/) (LEVI)
        in collaboration with [Digital Harbor Foundation](https://digitalharbor.org/),
        [Rising Academies](https://www.risingacademies.com/),
        and [The Learning Agency](https://the-learning-agency.com/).
The primary contributors are [Zachary Levonian](https://levon003.github.io/) and [Owen Henkel](https://www.linkedin.com/in/owenhenkel/).

This demo was made in [Streamlit](https://streamlit.io/). The code and data for this demo are available [on GitHub](https://github.com/DigitalHarborFoundation/llm-math-education).
        """,
        )
    st.markdown(
        """# Creating math hints with ChatGPT

Generate hints for practice problems given an incorrect answer.
Choose a practice problem from the bank below or insert your own lesson, worked example, and practice problem in the fields below.""",
    )
    question_df = data_utils.load_hint_problem_data()
    st.text_area(
        "Lesson and worked example:",
        key="lesson_text_area",
    )
    st.selectbox(
        "Choose a practice problem:",
        [QUESTION_SELECTBOX_DEFAULT_STRING] + question_df.display_name.to_list(),
        key="question_selectbox",
        on_change=question_selectbox_changed,
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
    # add the hint buttons
    for hint_type, button_label in HINT_TYPE_BUTTON_LABELS_MAP.items():
        st.button(
            button_label,
            key=f"{hint_type}_button",
            on_click=hint_type_button_clicked,
            args=(hint_type,),
            disabled=not are_buttons_enabled,
        )

    if "hint_chat_messages" not in st.session_state:
        st.session_state.hint_chat_messages = []

    # replay history, if there is any
    for message in st.session_state.hint_chat_messages:
        with st.chat_message(message["role"], avatar=chat_utils.get_avatar(message["role"])):
            st.markdown(message["content"])

    if st.session_state.new_hint_request_messages is not None:
        process_hint_query(st.session_state.new_hint_request_messages)
        st.session_state.new_hint_request_messages = None
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
    page_title="Hint generation with ChatGPT - for math educators",
    page_icon="💡",
)

if auth_utils.check_is_authorized(allow_openai_key=False):
    instantiate_session()
    build_app()
