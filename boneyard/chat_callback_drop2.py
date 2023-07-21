import time

import streamlit as st

if "word" not in st.session_state:
    st.session_state["word"] = ""

new_word = st.chat_input("Enter word" if st.session_state.word == "" else "Update word", key="chat_input_key")
if new_word:
    with st.spinner(""):
        time.sleep(1)
        st.session_state.word = new_word
st.write(f"Word: {st.session_state.word}")
