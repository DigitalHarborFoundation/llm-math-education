import notebook.auth.security
import streamlit as st


def password_submitted():
    entered_password = st.session_state.password_text_input
    # TODO should probably check against a separate password hash, rather than reusing the auth_token hash
    if notebook.auth.security.passwd_check(st.secrets["AUTH_TOKEN"], entered_password):
        st.session_state.is_authorized = True
    else:
        st.error("😕 Password incorrect")


def check_is_authorized() -> bool:
    if "is_authorized" not in st.session_state or not st.session_state.is_authorized:
        st.session_state.is_authorized = False
        if "is_authorized_via_token" not in st.session_state:
            query_params = st.experimental_get_query_params()
            st.session_state.is_authorized_via_token = False
            if "auth_token" in query_params and "AUTH_TOKEN" in st.secrets:
                auth_token = query_params["auth_token"][0]
                if notebook.auth.security.passwd_check(st.secrets["AUTH_TOKEN"], auth_token):
                    st.session_state.is_authorized_via_token = True
            if st.session_state.is_authorized_via_token:
                st.session_state.is_authorized = True
        if not st.session_state.is_authorized:
            st.text_input(
                "Password:",
                type="password",
                on_change=password_submitted,
                key="password_text_input",
            )
    return st.session_state.is_authorized
