from llm_math_education import retrieval


class RetrievalStrategy:
    """General retrieval strategy implementation, mostly just an interface."""

    def do_retrieval(self, expected_slots: list[str], user_query: str, previous_messages: list[dict[str, str]] = []):
        raise ValueError("Not implemented.")


class NoRetrievalStrategy(RetrievalStrategy):
    def do_retrieval(self, expected_slots: list[str], user_query: str, previous_messages: list[dict[str, str]] = []):
        return {expected_slot: "" for expected_slot in expected_slots}


class StaticRetrievalStrategy(RetrievalStrategy):
    def __init__(self, fill_string: str) -> None:
        super().__init__()
        self.fill_string = fill_string

    def do_retrieval(self, expected_slots: list[str], user_query: str, previous_messages: list[dict[str, str]] = []):
        return {expected_slot: self.fill_string for expected_slot in expected_slots}


class EmbeddingRetrievalStrategy(RetrievalStrategy):
    def __init__(self, db: retrieval.RetrievalDb) -> None:
        super().__init__()
        self.db = db

    def do_retrieval(self, expected_slots: list[str], user_query: str, previous_messages: list[dict[str, str]] = []):
        # distances = self.db.compute_string_distances(user_query)
        # TODO do some text retrieval based on these distances
        return {}
