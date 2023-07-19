import streamlit as st

text_options = ["Text 1 contents", "Text 2 contents"]
text_option_names = ["Text 1", "Text 2"]


def checkbox_change():
    if st.session_state.radio_group != "Custom":
        index = text_option_names.index(st.session_state.radio_group)
        st.session_state.text_area = text_options[index]


def textarea_change():
    if st.session_state.text_area in text_options:
        index = text_options.index(st.session_state.text_area)
        st.session_state.radio_group = text_option_names[index]
    elif st.session_state.radio_group != "Custom":
        st.session_state.radio_group = "Custom"


if "text_area" not in st.session_state:
    st.session_state.text_area = text_options[0]
if "radio_group" not in st.session_state:
    st.session_state.radio_group = text_option_names[0]

st.radio("Default texts:", text_option_names + ["Custom"], key="radio_group", on_change=checkbox_change)
st.text_area("Text area:", key="text_area", on_change=textarea_change)
