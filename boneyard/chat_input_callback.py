import streamlit as st


def chat_input_submit():
    st.write(st.session_state.chat_input_key)


# This throws an exception! Can't set value from session state
# if "chat_input_key" not in st.session_state:
#    st.session_state["chat_input_key"] = "test"

st.chat_input("Enter query", key="chat_input_key", on_submit=chat_input_submit)
