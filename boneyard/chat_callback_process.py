import time

import streamlit as st


def chat_input_submit():
    build_app()
    with st.chat_message("user"):
        st.markdown(st.session_state.chat_input_key)
    with st.chat_message("assistant"):
        with st.spinner("loading..."):
            time.sleep(1)
            st.markdown("System reply")
    st.session_state.messages.append({"role": "user", "content": st.session_state.chat_input_key})
    st.session_state.messages.append({"role": "assistant", "content": "System reply"})


def button_clicked():
    if len(st.session_state.messages) > 0:
        st.session_state.messages.pop()
    st.session_state.is_app_built = False


def build_app():
    time.sleep(0.2)  # imitate loading delay
    st.button(
        "Delete message",
        key="button_key",
        on_click=button_clicked,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.chat_input(
        "Enter query",
        key="chat_input_key",
        on_submit=chat_input_submit,
    )

    st.session_state.is_app_built = True


if "is_app_built" not in st.session_state or not st.session_state.is_app_built:
    build_app()
