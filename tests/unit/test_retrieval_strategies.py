from llm_math_education import retrieval, retrieval_strategies


def test_NoRetrievalStrategy():
    retriever = retrieval_strategies.NoRetrievalStrategy()
    assert retriever.do_retrieval(["test"], "user") == {"test": ""}


def test_StaticRetrievalStrategy():
    retriever = retrieval_strategies.StaticRetrievalStrategy("TestVal")
    assert retriever.do_retrieval(["test"], "user") == {"test": "TestVal"}


def test_EmbeddingRetrievalStrategy(retrieval_db_path):
    # TODO is monkeypatch needed here? this might be making an actual API call...
    db = retrieval.RetrievalDb(retrieval_db_path, "conftestDb", "text")
    retriever = retrieval_strategies.EmbeddingRetrievalStrategy(db, max_tokens=5)
    filled_slots = retriever.do_retrieval(["testSlot"], "testQuery")
    assert "testSlot" in filled_slots
    # note that the actual text retrieved here is random due to the way the retrieval embeddings are generated
    assert filled_slots["testSlot"].startswith("Test text"), "No retrieved text."

    # test max_tokens
    retriever = retrieval_strategies.EmbeddingRetrievalStrategy(db, max_tokens=0)
    filled_slots = retriever.do_retrieval(["testSlot"], "testQuery")
    assert filled_slots["testSlot"] == ""
