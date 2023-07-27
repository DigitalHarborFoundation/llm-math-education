import logging
from pathlib import Path

import streamlit as st

from llm_math_education import retrieval, retrieval_strategies

DATA_DIR = Path("./data") / "app_data"
RETRIEVAL_OPTIONS_LIST = [
    "Rori + Pre-algebra textbook",
    "Rori micro-lessons only",
    "Pre-algebra textbook only",
    "None",
]
DB_NAME_LIST = ["rori_microlesson", "openstax_subsection"]


def create_retrieval_db_map(
    db_name_list: list[str] = DB_NAME_LIST,
    except_on_error: bool = False,
) -> dict[str, retrieval.RetrievalDb]:
    retrieval_db_map = {}
    if DATA_DIR.exists():
        for db_name in db_name_list:
            try:
                db = retrieval.RetrievalDb(DATA_DIR, db_name, "db_string")
                retrieval_db_map[db_name] = db
            except Exception as ex:
                if except_on_error:
                    raise ValueError(f"Failed to load db {db_name}", ex)
                else:
                    logging.warning(f"Failed to load db {db_name}.")
                    continue
    return retrieval_db_map


def load_session_data() -> bool:
    if "retrieval_db_map" not in st.session_state:
        st.session_state.retrieval_db_map = create_retrieval_db_map()
    was_data_loaded = False
    if "retrieval_options_map" not in st.session_state:
        if any([db_name not in st.session_state.retrieval_db_map for db_name in DB_NAME_LIST]):
            # missing needed db data
            st.warning("Error loading retrieval data; performance may be degraded.")
            st.session_state.retrieval_options_map = {
                key: retrieval_strategies.NoRetrievalStrategy() for key in RETRIEVAL_OPTIONS_LIST
            }
        else:
            rori_microlesson_db_info = {
                "db": st.session_state.retrieval_db_map["rori_microlesson"],
                "max_tokens": 2000,
                "prefix": "Here is some lesson content that might be relevant:\n",
            }
            openstax_subsection_db_info = {
                "db": st.session_state.retrieval_db_map["openstax_subsection"],
                "max_tokens": 2000,
                "prefix": "Here are some excerpts from a math textbook. If they are relevant to the question, feel free to use language or examples from these excerpts:\n",
            }
            rori_only_strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(
                {
                    "rori_microlesson_texts": rori_microlesson_db_info,
                },
            )
            openstax_only_strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(
                {
                    "openstax_subsection_texts": openstax_subsection_db_info,
                },
            )
            rori_microlesson_db_info = rori_microlesson_db_info.copy()
            openstax_subsection_db_info = openstax_subsection_db_info.copy()
            rori_microlesson_db_info["max_tokens"] /= 2
            openstax_subsection_db_info["max_tokens"] /= 2
            both_strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(
                {
                    "rori_microlesson_texts": rori_microlesson_db_info,
                    "openstax_subsection_texts": openstax_subsection_db_info,
                },
            )
            retrieval_options_map = {
                RETRIEVAL_OPTIONS_LIST[0]: both_strategy,
                RETRIEVAL_OPTIONS_LIST[1]: rori_only_strategy,
                RETRIEVAL_OPTIONS_LIST[2]: openstax_only_strategy,
                RETRIEVAL_OPTIONS_LIST[3]: retrieval_strategies.NoRetrievalStrategy(),
            }
            st.session_state.retrieval_options_map = retrieval_options_map
        was_data_loaded = True
    return was_data_loaded
