import numpy as np

from llm_math_education import embedding_utils


def mock_get_openai_embeddings(input_text_list, *args, **kwargs):
    return [np.random.random(size=embedding_utils.EMBEDDING_DIM) for _ in input_text_list]
