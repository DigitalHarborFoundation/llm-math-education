import os

from llm_math_education import env_utils


def test_load_dotfile(tmp_path):
    expected_key = "TEST_LOAD_DOTFILE_KEY"
    expected_value = "test_load_dotfile_value"
    with open(tmp_path / ".env", "w") as outfile:
        outfile.write(f"{expected_key}={expected_value}")

    assert expected_key not in os.environ
    env_utils.load_dotfile(tmp_path)
    assert expected_key in os.environ
    assert os.environ[expected_key] == expected_value
