from llm_math_education import retrieval, retrieval_strategies


def test_NoRetrievalStrategy():
    retriever = retrieval_strategies.NoRetrievalStrategy()
    assert retriever.do_retrieval(["test"], "user") == {"test": ""}


def test_StaticRetrievalStrategy():
    retriever = retrieval_strategies.StaticRetrievalStrategy("TestVal")
    assert retriever.do_retrieval(["test"], "user") == {"test": "TestVal"}


def test_EmbeddingRetrievalStrategy(retrieval_db_path):
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


def test_MappedEmbeddingRetrievalStrategy(retrieval_db):
    slot_map = {
        "slot1": "fill1",
        "slot2": "fill2",
    }
    retriever = retrieval_strategies.MappedEmbeddingRetrievalStrategy(slot_map, nonmatching_fill="nomatch")
    filled_slots = retriever.do_retrieval(["slot1", "slot2"], "")
    assert slot_map == filled_slots
    filled_slots = retriever.do_retrieval(["slot1", "slot2", "slot3"], "")
    assert filled_slots["slot3"] == "nomatch"
    for slot, slot_fill in slot_map.items():
        assert filled_slots[slot] == slot_fill

    slot_map = {
        "slot1": "fill1",
        "slot2": retrieval.DbInfo(retrieval_db),
    }
    retriever = retrieval_strategies.MappedEmbeddingRetrievalStrategy(slot_map)
    filled_slots = retriever.do_retrieval(["slot1", "slot2"], "")
    assert filled_slots["slot1"] == "fill1"
    assert filled_slots["slot2"].startswith("Test text")

    retriever.update_map({"slot2": "fill2"})
    filled_slots = retriever.do_retrieval(["slot1", "slot2"], "")
    assert filled_slots["slot2"] == "fill2"
