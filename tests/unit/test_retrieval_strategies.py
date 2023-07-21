from llm_math_education import retrieval_strategies


def test_NoRetrievalStrategy():
    retriever = retrieval_strategies.NoRetrievalStrategy()
    assert retriever.do_retrieval(["test"], "user") == {"test": ""}
