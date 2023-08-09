import logging
import re
from pathlib import Path

import pandas as pd
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


@st.cache_data
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


@st.cache_data
def create_hint_default_retrieval_slot_map() -> dict[str, retrieval.DbInfo]:
    retrieval_db_map = create_retrieval_db_map()
    rori_microlesson_db_info = retrieval.DbInfo(
        retrieval_db_map["rori_microlesson"],
        max_tokens=1000,
        prefix="Here is some lesson content that might be relevant:\n",
    )
    openstax_subsection_db_info = retrieval.DbInfo(
        retrieval_db_map["openstax_subsection"],
        max_tokens=1000,
        prefix="Here are some excerpts from a math textbook. If they are relevant to the question, feel free to use language or examples from these excerpts:\n",
    )
    slot_map = {
        "rori_microlesson_texts": rori_microlesson_db_info,
        "openstax_subsection_texts": openstax_subsection_db_info,
    }
    return slot_map


def cache_retrieval_data_in_session() -> bool:
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
            rori_microlesson_db_info = retrieval.DbInfo(
                st.session_state.retrieval_db_map["rori_microlesson"],
                max_tokens=2000,
                prefix="Here is some lesson content that might be relevant:\n",
            )
            openstax_subsection_db_info = retrieval.DbInfo(
                st.session_state.retrieval_db_map["openstax_subsection"],
                max_tokens=2000,
                prefix="Here are some excerpts from a math textbook. If they are relevant to the question, feel free to use language or examples from these excerpts:\n",
            )
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
            both_strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(
                {
                    "rori_microlesson_texts": rori_microlesson_db_info.copy(max_tokens=1000),
                    "openstax_subsection_texts": openstax_subsection_db_info.copy(max_tokens=1000),
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


def create_display_name(row, max_length: int | None = None):
    intro = re.sub("\\([^\\(]*\\)", "", row.topic).strip() + f" (grade {row.grade}): "
    question = row.question.replace("\n", " ").strip()
    display_name = intro + question
    if max_length and len(display_name) > max_length:
        display_name = display_name[: max_length - 3] + "..."
    return display_name


def trim_lesson(lesson: str) -> str:
    """Hacky function to strip some of the Rori chafe from the lesson and worked examples.

    Args:
        lesson (str): Rori micro-lesson description.

    Returns:
        str: Trimmed version of the given lesson.
    """
    lesson = lesson.strip()
    lines = lesson.split("\n")
    kept_lines = []
    for line in lines[:-3]:
        if (line.startswith("Write") or line.startswith("Type")) and "yes" in line.lower():
            continue
        elif line == "Would you like to try it for yourself?":
            continue
        kept_lines.append(line)
    for line in lines[-3:]:
        if (line.startswith("Write") or line.startswith("Type")) and "yes" in line.lower():
            continue
        elif "questions" in line:
            continue
        elif line == "Would you like to try it for yourself?":
            continue
        kept_lines.append(line)
    trimmed_lesson = "\n".join(kept_lines).strip()
    # strip some needless linebreaks
    trimmed_lesson = re.sub("\n\n\n+", "\n\n", trimmed_lesson)
    return trimmed_lesson


@st.cache_data
def load_hint_problem_data() -> pd.DataFrame:
    """Problem data has:
    - Problem
    - Correct answer
    - Incorrect answer
    - Lesson
    """
    question_df = pd.read_csv(DATA_DIR / "question_sample.csv").sort_values(by=["grade", "topic"])
    # .sort_values(by="question", key=lambda s: s.map(len))
    assert len(question_df) > 1
    question_df["display_name"] = [create_display_name(row) for row in question_df.itertuples()]
    question_df["lesson_trimmed"] = [trim_lesson(row.lesson) for row in question_df.itertuples()]
    return question_df
