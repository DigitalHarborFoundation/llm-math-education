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
    def __init__(self, db: retrieval.RetrievalDb, max_tokens: int = 2000) -> None:
        super().__init__()
        self.db: retrieval.RetrievalDb = db
        self.max_tokens: int = max_tokens

    def do_retrieval(self, expected_slots: list[str], user_query: str, previous_messages: list[dict[str, str]] = []):
        distances = self.db.compute_string_distances(user_query)
        sort_inds = retrieval.get_distance_sort_indices(distances)
        texts = []
        total_tokens = 0
        for ind in sort_inds:
            row = self.db.df.iloc[ind]
            n_tokens = row[self.db.n_tokens_col]
            if total_tokens + n_tokens > self.max_tokens:
                break
            total_tokens += n_tokens
            text = row[self.db.embed_col]
            texts.append(text)
        fill_string = "\n".join(texts)
        return {expected_slot: fill_string for expected_slot in expected_slots}
