from llm_math_education import logit_bias

THE_TOKEN = 1820  # token for string "the"


def test_get_tokenizer():
    tokenizer = logit_bias.get_tokenizer()
    assert tokenizer.encode("the") == [1820]
    assert tokenizer.decode([THE_TOKEN]) == "the"


def test_load_stopwords():
    stopword_tokens = logit_bias.load_stopword_tokens()
    assert len(stopword_tokens) >= 11000
    assert THE_TOKEN in stopword_tokens, "The 'the' token (1820) should be in the stopwords."
    assert stopword_tokens == logit_bias.get_stopword_tokens()
    # test caching
    assert logit_bias.get_stopword_tokens() == logit_bias.get_stopword_tokens()


def test_get_nonstopword_tokens():
    # stopwords
    tokens = logit_bias.get_nonstopword_tokens("the was and were thus")
    assert len(tokens) == 0
    # non-stopwords
    tokens = logit_bias.get_nonstopword_tokens("verily osmogorp")
    assert len(tokens) >= 5


def test_get_logit_bias():
    tokens = logit_bias.get_nonstopword_tokens("verily verily verily")
    assert len(tokens) == 6
    logit_bias_dict = logit_bias.get_logit_bias(tokens, min_count=4)
    assert len(logit_bias_dict) == 0
    logit_bias_dict = logit_bias.get_logit_bias(tokens, min_count=3)
    assert len(logit_bias_dict) == 1
    assert any([token in logit_bias_dict for token in tokens])


def test_get_logit_bias_from_slot():
    recent_slot_fill_dict = [
        {
            "slot1": "verily verily verily",
            "slot2": "the",
        },
    ]
    logit_bias_dict = logit_bias.get_logit_bias_from_slot(recent_slot_fill_dict)
    assert 1570 in logit_bias_dict
    # TODO make this test cover more cases and be more explanatory


def test_create_stopword_token_set_from_word_list():
    word_list = ["the"]
    stopword_tokens = logit_bias.create_stopword_token_set_from_word_list(word_list)
    assert len(stopword_tokens) > 1
    assert THE_TOKEN in stopword_tokens
