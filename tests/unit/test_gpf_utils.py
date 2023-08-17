from llm_math_education import gpf_utils


def test_get_gpd_codes():
    grade, domain, construct, subconstruct, skill, index = gpf_utils.get_gpd_codes("G9.N5.1.3.1")
    assert grade == 9
    assert domain == "N"
    assert construct == "N5"
    assert subconstruct == "N5.1"
    assert skill == "N5.1.3"
    assert index == 1
