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


class MappedEmbeddingRetrievalStrategy(RetrievalStrategy):
    def __init__(self, slot_map: dict[str, str | dict], nonmatching_fill: str = "") -> None:
        super().__init__()
        self.slot_map = slot_map
        self.nonmatching_fill = nonmatching_fill
        self._validate_slot_map()

    def _validate_slot_map(self):
        for key, value in self.slot_map.items():
            if type(key) is not str:
                raise ValueError("Slot map keys must be strings.")
            if type(value) not in [dict, str]:
                raise ValueError("Unexpected type in slot map.")
            if type(value) is dict:
                if "db" not in value or not hasattr(value["db"], "compute_string_distances"):
                    raise ValueError("Expected a db with a compute_string_distances() method.")

    def update_map(self, slot_updates: dict):
        self.slot_map.update(slot_updates)
        self._validate_slot_map()

    def do_retrieval(self, expected_slots: list[str], user_query: str, previous_messages: list[dict[str, str]] = []):
        fill_string_map = {}
        for expected_slot in expected_slots:
            if expected_slot in self.slot_map:
                db_info = self.slot_map[expected_slot]
                if type(db_info) is str:
                    fill_string = db_info
                else:
                    db = db_info["db"]
                    max_tokens = db_info["max_tokens"] if "max_tokens" in db_info else 1500
                    distances = db.compute_string_distances(user_query)
                    sort_inds = retrieval.get_distance_sort_indices(distances)
                    texts = []
                    total_tokens = 0
                    for ind in sort_inds:
                        row = db.df.iloc[ind]
                        n_tokens = row[db.n_tokens_col]
                        if total_tokens + n_tokens > max_tokens:
                            break
                        total_tokens += n_tokens
                        text = row[db.embed_col]
                        texts.append(text)
                    prefix = db_info["prefix"] if "prefix" in db_info else ""
                    suffix = db_info["suffix"] if "suffix" in db_info else ""
                    fill_string = prefix + "\n".join(texts) + suffix
            else:
                fill_string = self.nonmatching_fill
            fill_string_map[expected_slot] = fill_string
        return fill_string_map
