# understanding button callbacks
from datetime import datetime

import streamlit as st


def handle_button_click():
    st.session_state.click_log.append(f"Button clicked at {datetime.now().isoformat()}")


if "click_log" not in st.session_state:
    st.session_state["click_log"] = []

for click in st.session_state.click_log:
    st.write(click)

st.button("Click", key="button_key", on_click=handle_button_click)
