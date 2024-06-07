from streamlit.testing.v1 import AppTest

from streamlit_app import auth_utils


def test_hint_generation_app():
    # generate a new password for this test
    password = "test"
    hashed_password = auth_utils.passwd_hash(password)

    # create and run the app
    at = AppTest.from_file("src/hint_generation/app.py")
    at.secrets["PASSWORD"] = hashed_password
    at.secrets["OPENAI_API_KEY"] = "test-key"
    at.run()
    assert not at.exception
    assert "is_authorized" not in at.session_state or not at.session_state.is_authorized

    # attempt to log in
    # note: this is deprecated, because we turend off passwords for this demo
    # at.text_input(key=auth_utils.PASSWORD_TEXT_INPUT_KEY).input(password).run()
    # assert not at.exception
    # assert at.session_state.is_authorized
