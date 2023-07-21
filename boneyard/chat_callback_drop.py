import time

import streamlit as st


def chat_input_submit():
    with st.spinner(""):
        time.sleep(1)
        st.session_state.word = st.session_state.chat_input_key


if "word" not in st.session_state:
    st.session_state["word"] = ""

st.write(f"Word: {st.session_state.word}")
st.chat_input(
    "Enter word" if st.session_state.word == "" else "Update word",
    key="chat_input_key",
    on_submit=chat_input_submit,
)
