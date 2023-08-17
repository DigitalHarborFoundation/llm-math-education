import pytest

from llm_math_education import openstax


@pytest.mark.skip(reason="Long test (15s, even with caching), not on the core functionality path")
def test_openstax(pytestconfig):
    cache_dir = pytestconfig.rootpath / "tests" / "resources" / "openstax_prealgebra"
    cache_dir.mkdir(exist_ok=True)
    prealgebra_textbook_url = "https://openstax.org/books/prealgebra-2e/pages/1-introduction"
    textbook_data = openstax.cache_openstax_textbook_contents(prealgebra_textbook_url, cache_dir)
    df = openstax.get_subsection_dataframe(textbook_data)
    assert len(df) > 0
    assert "content" in df.columns
