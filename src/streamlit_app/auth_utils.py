import streamlit as st


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


def check_is_authorized() -> bool:
    if "is_authorized" not in st.session_state or not st.session_state.is_authorized:
        st.session_state.is_authorized = False
        if "is_authorized_via_token" not in st.session_state:
            query_params = st.experimental_get_query_params()
            st.session_state.is_authorized_via_token = False
            if "auth_token" in query_params and "AUTH_TOKEN" in st.secrets:
                auth_token = query_params["auth_token"][0]
                if passwd_check(st.secrets["AUTH_TOKEN"], auth_token):
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
