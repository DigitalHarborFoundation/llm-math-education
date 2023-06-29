from pathlib import Path

import streamlit as st

from llm_math_education import chat_db

st.set_page_config(page_title="ChatGPT for middle-school math ed", page_icon=":robot_face:")
chat_log = chat_db.ChatLog(Path("data/chat_logs"))
