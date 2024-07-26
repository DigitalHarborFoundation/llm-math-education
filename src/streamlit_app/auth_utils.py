import openai
import openai.error
import streamlit as st

PASSWORD_TEXT_INPUT_KEY = "password_text_input"


def generate_auth_token() -> str:
    import binascii
    import os

    auth_token = binascii.b2a_hex(os.urandom(16)).decode("ascii")
    return auth_token


def cast_unicode(s: bytes | str, encoding: str) -> str:
    if isinstance(s, bytes):
        return s.decode(encoding, "replace")
    return s


def passwd_hash(passphrase: str) -> str:
    from argon2 import PasswordHasher

    ph = PasswordHasher(
        memory_cost=10240,
        time_cost=10,
        parallelism=8,
    )
    h = ph.hash(passphrase)

    return ":".join(("argon2", cast_unicode(h, "ascii")))


def passwd_check(hashed_passphrase: str, passphrase: str) -> bool:
    # modification of source provided with a BSD 3-Clause License, Copyright (c) 2015-, Jupyter Development Team
    # from notebook.auth.security
    assert hashed_passphrase.startswith("argon2:")
    import argon2
    import argon2.exceptions

    ph = argon2.PasswordHasher()
    try:
        return ph.verify(hashed_passphrase[7:], passphrase)
    except argon2.exceptions.VerificationError:
        return False


def password_submitted():
    entered_password = st.session_state.password_text_input
    if passwd_check(st.secrets["PASSWORD"], entered_password):
        st.session_state.is_authorized = True
    else:
        st.error("😕 Password incorrect")


def openai_api_key_submitted():
    entered_openai_api_key = st.session_state.openai_api_key_text_input
    if validate_openai_api_key(entered_openai_api_key):
        st.session_state.is_authorized = True
        openai.api_key = entered_openai_api_key
        st.session_state.is_openai_key_set = True
    else:
        st.error("😕 Couldn't validate OpenAI API key")


def validate_openai_api_key(openai_api_key: str) -> bool:
    previous_api_key = openai.api_key
    try:
        # temporarily override api key used
        openai.api_key = openai_api_key
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": "Hi"}],
            request_timeout=10,
            max_tokens=1,
        )
        completion["choices"][0]["message"]
        return True
    except openai.error.RateLimitError as ex:
        st.warning(f"Valid API key, but got a RateLimitError: {ex}")
    except Exception as ex:
        st.warning(f"API returned an error: {ex}")
    finally:
        openai.api_key = previous_api_key
    return False


def check_is_authorized(allow_openai_key: bool = False, markdown_header: str = "") -> bool:
    if "is_authorized" not in st.session_state or not st.session_state.is_authorized:
        st.session_state.is_authorized = False
        if "is_authorized_via_token" not in st.session_state:
            st.session_state.is_authorized_via_token = False
            if "auth_token" in st.query_params and "AUTH_TOKEN" in st.secrets:
                auth_token = st.query_params["auth_token"]
                if passwd_check(st.secrets["AUTH_TOKEN"], auth_token):
                    st.session_state.is_authorized_via_token = True
            if st.session_state.is_authorized_via_token:
                st.session_state.is_authorized = True
        if not st.session_state.is_authorized:
            if markdown_header != "":
                st.markdown(markdown_header)
            st.text_input(
                "Password:",
                type="password",
                on_change=password_submitted,
                key=PASSWORD_TEXT_INPUT_KEY,
            )
            if allow_openai_key:
                st.markdown(
                    'Or, provide your own OpenAI API key. (See: ["Where do I find my Secret API Key?"](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key))',
                )
                st.text_input(
                    "OpenAI API key:",
                    type="password",
                    on_change=openai_api_key_submitted,
                    key="openai_api_key_text_input",
                )
    return st.session_state.is_authorized
