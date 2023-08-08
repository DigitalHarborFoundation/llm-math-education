# understanding button callbacks
from datetime import datetime

import streamlit as st


def handle_button_click():
    st.session_state.button_click_time = datetime.now()
    st.write("Recorded new button click state for later handling during this app refresh")


if "click_log" not in st.session_state:
    st.session_state["click_log"] = []
if "button_click_time" not in st.session_state:
    st.session_state.button_click_time = None

# note that this counter will be out-of-order, because the click isn't in the click log until the button_click_time-handling code below is executed
# this is expected behavior
st.write(f"{len(st.session_state.click_log)} clicks")

for click in st.session_state.click_log:
    st.write(click)

if st.session_state.button_click_time is not None:
    st.session_state.click_log.append(f"Button clicked at {st.session_state.button_click_time.isoformat()}")
    st.write("NEW! " + st.session_state.click_log[-1])
    st.session_state.button_click_time = None

st.button("Click", key="button_key", on_click=handle_button_click)
st.button("Rerun app")  # does nothing, but will force a rerun on click
