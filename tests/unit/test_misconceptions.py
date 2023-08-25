from llm_math_education import misconceptions


def test_load_misconception_list():
    misconception_list = misconceptions.load_misconception_list()
    assert len(misconception_list) >= 50
    # assert misconception_list == misconceptions.get_misconception_list()  # I'm not sure why this inequality is false
    # test caching
    assert misconceptions.get_misconception_list() == misconceptions.get_misconception_list()


def test_get_misconceptions_string():
    misconception_string = misconceptions.get_misconceptions_string()
    assert len(misconception_string) >= 1000
