import streamlit as st

if "word" not in st.session_state:
    st.session_state["word"] = ""

new_word = st.text_input(
    "Enter:",
    placeholder="Enter word" if st.session_state.word == "" else "Update word",
    key="text_input_key",
)
if new_word:
    st.session_state.word = new_word
    print(new_word)
st.write(f"Word: {st.session_state.word}")
