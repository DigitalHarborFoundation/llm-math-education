from llm_math_education import retrieval_strategies


def test_NoRetrievalStrategy():
    retriever = retrieval_strategies.NoRetrievalStrategy()
    assert retriever.do_retrieval(["test"], "user") == {"test": ""}


def test_StaticRetrievalStrategy():
    retriever = retrieval_strategies.StaticRetrievalStrategy("TestVal")
    assert retriever.do_retrieval(["test"], "user") == {"test": "TestVal"}


def test_EmbeddingRetrievalStrategy():
    assert True
    db = None
    retriever = retrieval_strategies.EmbeddingRetrievalStrategy(db, max_tokens=10)
    assert retriever.do_retrieval(["test"], "user") == {"test": "TestVal"}
