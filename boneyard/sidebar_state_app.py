import streamlit as st

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message("user"):
        st.write(message)

new_message = st.chat_input("Enter message")
if new_message:
    st.chat_message("user").write(new_message)
    st.session_state.messages.append(new_message)

# note: perhaps obvious, but this sidebar must come below the above in order to read the length of the messages correctly
with st.sidebar:
    st.write(f"Messages: {len(st.session_state.messages)}")
