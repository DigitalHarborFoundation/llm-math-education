# Demo script, used to verify the usage examples shown in the README
# flake8: noqa
from pathlib import Path

import dotenv

dotenv.load_dotenv(".env")

demo_dir = Path("data") / "demo"
demo_dir.mkdir(exist_ok=True)
student_question = "How do I identify common factors?"

df_filepath = demo_dir / "raw_demo_df.json"
if not df_filepath.exists():
    cache_dir = Path("tests") / "resources" / "openstax_prealgebra"
    from llm_math_education import openstax

    prealgebra_textbook_url = "https://openstax.org/books/prealgebra-2e/pages/1-introduction"
    textbook_data = openstax.cache_openstax_textbook_contents(prealgebra_textbook_url, cache_dir)
    df = openstax.get_subsection_dataframe(textbook_data)
    df = df.sample(n=10)
    df.to_json(df_filepath)
else:
    import pandas as pd

    df = pd.read_json(df_filepath)
print(df.columns)

from llm_math_education import retrieval

openstax_db = retrieval.RetrievalDb(demo_dir, "openstax_prealgebra", "content", df)
openstax_db.create_embeddings()
openstax_db.save_df()

# load existing embedding database
openstax_db = retrieval.RetrievalDb(demo_dir, "openstax_prealgebra", "content")
distances = openstax_db.compute_string_distances(student_question)
print(distances)

from llm_math_education import retrieval_strategies

db_info = retrieval.DbInfo(
    openstax_db,
    max_texts=1,
)
strategy = retrieval_strategies.MappedEmbeddingRetrievalStrategy(
    {
        "openstax_section": db_info,
    },
)

from llm_math_education import prompt_utils

pm = prompt_utils.PromptManager()
pm.set_retrieval_strategy(strategy)
pm.set_intro_messages(
    [
        {
            "role": "user",
            "content": """Answer this question: {user_query}

Reference this text in your answer:
{openstax_section}""",
        },
    ],
)
messages = pm.build_query(student_question)
print(messages)

# pass these messages to the OpenAI API
import openai

completion = openai.ChatCompletion.create(
    model="gpt-4o-mini",
    messages=messages,
)
assistant_message = completion["choices"][0]["message"]
print(assistant_message)

# add stored messages to continue the conversation
pm.add_stored_message(assistant_message)
pm.build_query("I have a follow-up question...")

# you can alternately use the built-in prompts
from llm_math_education.prompts import mathqa as mathqa_prompts

pm.clear_stored_messages()
pm.set_intro_messages(mathqa_prompts.intro_prompts["general_math_qa_intro"])
