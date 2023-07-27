import streamlit as st

from streamlit_app import auth_utils


def build_app():
    st.markdown(
        """# Hint generation

Coming soon.""",
    )


st.set_page_config(
    page_title="ChatGPT for middle-school math education - Hint generation",
    page_icon="💡",
)

if auth_utils.check_is_authorized():
    build_app()
