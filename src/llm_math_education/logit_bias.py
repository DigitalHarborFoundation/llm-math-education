# Utilities associated with logit_bias
# docs: https://platform.openai.com/docs/api-reference/chat/create#logit_bias
# help doc: https://help.openai.com/en/articles/5247780-using-logit-bias-to-define-token-probability
# logit_bias takes at most 300 tokens: https://aidungeon.medium.com/controlling-gpt-3-with-logit-bias-55866d593292
import functools
import importlib.resources
import json
import re
import string as string_utils
from collections import Counter

import tiktoken

from llm_math_education import resources


@functools.cache
def get_tokenizer(model_name: str = "gpt-3.5-turbo") -> tiktoken.Encoding:
    """Get the tokenizer. Cached.

    Args:
        model_name (str, optional): The model tokenizer to load. Defaults to "gpt-3.5-turbo".

    Returns:
        tiktoken.Encoding: The tiktoken/OpenAI tokenizer.
    """
    tokenizer = tiktoken.encoding_for_model(model_name)
    return tokenizer


@functools.cache
def get_stopword_tokens():
    """Cached version of `load_stopword_tokens`."""
    return load_stopword_tokens()


def load_stopword_tokens() -> set[int]:
    resource_filepath = importlib.resources.files(resources) / "dolma_stopwords.json"
    with resource_filepath.open("r") as infile:
        stopwords_dict = json.load(infile)
    return set(stopwords_dict["stopword_tokens"])


def create_stopword_token_set_from_word_list(word_list: list[str]) -> set[int]:
    """Create a set of stopword tokens from the given list of stop words.
    Used to create the default stopword resource loaded by `load_stopword_tokens`.

    Args:
        word_list (list[str]): List of words to include in the stopword set.

    Returns:
        set[int]: Set of stopword tokens.
    """
    tokenizer = get_tokenizer()
    stopword_tokens = set()
    stopwords = (
        word_list
        + list(map(str.lower, word_list))
        + list(map(str.upper, word_list))
        + list(map(str.capitalize, word_list))
        + list(string_utils.whitespace)
        + list(string_utils.punctuation)
    )
    for word in stopwords:
        for char in string_utils.whitespace + string_utils.punctuation:
            for string in [word, char + word, word + char]:
                tokens = tokenizer.encode(string)
                if len(tokens) == 1:
                    stopword_tokens.add(tokens[0])
    return stopword_tokens


def get_nonstopword_tokens(text: str) -> list[int]:
    tokenizer = get_tokenizer()
    stopword_tokens = get_stopword_tokens()
    tokens = tokenizer.encode(text)
    tokens = [
        token
        for token in tokens
        if token not in stopword_tokens and re.fullmatch("[ A-Za-z]+", tokenizer.decode([token]))
    ]
    return tokens


def get_logit_bias(
    tokens: list[int],
    min_count: int = 2,
    n_tokens: int | None = None,
    max_tokens: int = 50,
    min_bias: float = 1.0,
    max_bias: float = 5.0,
) -> dict[int, float]:
    """Given a list of tokens, create a corresponding logit_bias dictionary.

    Roughly, identifies the most frequent max_tokens tokens, stopping at n_tokens if provided,
    that occur at least min_count times. Bias values are assigned based on frequency, in the range min_bias to max_bias.
    The most frequent token will always have a weight of max_bias in the resulting logit_bias.
    Bias defaults are generally inspired by this doc: https://help.openai.com/en/articles/5247780-using-logit-bias-to-define-token-probability

    Args:
        tokens (list[int]): The list of tokens, e.g. after having stopword tokens removed.
        min_count (int, optional): Defaults to 2.
        n_tokens (int | None, optional): Defaults to None.
        max_tokens (int, optional): Defaults to 50.
        min_bias (float, optional): Defaults to 1.0.
        max_bias (float, optional): Defaults to 5.0.

    Returns:
        dict[int, float]: The logit_bias dict that can be passed to the logit_bias parameter accepted by the OpenAI API.
    """
    if len(tokens) == 0:
        return {}
    logit_bias = {}
    c = Counter(tokens).most_common(max_tokens)
    max_count = c[0][1]  # count of most-frequently-occurring token
    if max_count >= min_count:
        for token, count in c:
            if count < min_count:
                continue
            bias = min_bias + (max_bias - min_bias) * (count / max_count)
            logit_bias[token] = bias
            if n_tokens is not None and len(logit_bias) >= n_tokens:
                break
    return logit_bias


def get_logit_bias_from_slot(
    recent_slot_fill_dict: list[dict[str, str]],
    include: list[str] | None = None,
    exclude: list[str] = [],
    **kwargs,
) -> dict[int, float]:
    """Given texts that fill one or more slots, create an appropriate logit_bias.
    This is probably not a very reasonable way to do to this.

    Args:
        recent_slot_fill_dict (list[dict[str, str]]): See `prompt_utils.PromptManager`.
        include (list[str] | None, optional): Slot texts to consider. Defaults to None, meaning all slots are included.
        exclude (list[str], optional): Slot texts to ignore. Defaults to [].

    Returns:
        dict[int, float]: logit_bias
    """
    texts = []
    for slot_fill_dict in recent_slot_fill_dict:
        for key, value in slot_fill_dict.items():
            if (include is None or key in include) and key not in exclude:
                texts.append(value)
    text = "\n".join(texts)
    tokens = get_nonstopword_tokens(text)
    return get_logit_bias(tokens, **kwargs)
