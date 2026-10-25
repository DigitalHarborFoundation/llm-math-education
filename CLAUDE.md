# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`llm-math-education` is a Python package (published to PyPI) implementing simple retrieval-augmented generation (RAG) for middle-school math QA and hint generation, plus a Streamlit demo app. It uses the OpenAI Python SDK v1+ via the module-level client (`openai.api_key = ...`, `openai.chat.completions.create`, `openai.embeddings.create`). The project is in maintenance mode (see README FAQ).

## Environment and commands

uv manages Python and all dependencies (`uv.lock` is committed; `.python-version` sets the dev interpreter).

```bash
make install          # uv sync + pre-commit hooks + Jupyter kernel
make test             # uv run pytest --cov=src --cov-report term-missing
uv run pytest tests/unit/test_retrieval.py::test_name   # single test
make run-streamlit                    # main Math QA app (src/🤖_Math_QA.py)
make run-hint-generation-streamlit    # standalone hint app (src/hint_generation/app.py)
```

Run commands from the repo root: the Streamlit app loads data via paths relative to it (`data/app_data`). pytest is configured in `pyproject.toml` with `pythonpath = ["src"]`, which is what makes `streamlit_app` importable in tests.

Lint/format runs via pre-commit (black at line length 120, isort profile black, flake8, pyupgrade, add-trailing-comma, plus nbQA equivalents for notebooks). Run manually with `uv run pre-commit run --all-files`. CI (`.github/workflows/tests.yaml`) runs both tests and pre-commit; dependabot (`.github/dependabot.yml`) opens monthly update PRs for uv, pre-commit, GitHub Actions, and Docker.

Secrets: `OPENAI_API_KEY` in `.env` at the repo root for library/notebook use; the Streamlit app reads `.streamlit/secrets.toml` (`OPENAI_API_KEY`, optional argon2-hashed `AUTH_TOKEN`; see DEVELOPMENT.md for generating it).

## Architecture

Library code lives in `src/llm_math_education/`. The RAG flow is composed from three pieces:

1. **`retrieval.RetrievalDb`**: an in-memory embedding store over a pandas DataFrame. Persisted as `{db_name}_df.parquet` + `{db_name}_embed.npy` in a directory; passing a `df` creates a new DB (then `create_embeddings()` + `save_df()`), omitting it loads an existing one. Token counts are stored in an `n_tokens` column. Embeddings come from `embedding_utils` (`text-embedding-ada-002`, dim 1536).
2. **`retrieval_strategies.RetrievalStrategy`**: `do_retrieval(expected_slots, user_query, previous_messages)` returns a dict mapping prompt slot names to fill strings. `MappedEmbeddingRetrievalStrategy` maps each slot to either a static string or a `retrieval.DbInfo` (a `RetrievalDb` plus settings like `max_texts` / token budget that control how retrieved rows become text).
3. **`prompt_utils.PromptManager`**: holds intro messages (prompt templates using Python `str.format` `{slot}` syntax), a retrieval strategy, and stored conversation messages. `build_query()` identifies slots in each message, asks the strategy to fill them, and formats them. `{user_query}` is a special slot: when present, the user's query is substituted into the template instead of being appended as a separate user message.

Prompt templates live in `prompts/mathqa.py` and `prompts/hints.py` (`intro_prompts` dicts). Other modules: `logit_bias` (builds OpenAI `logit_bias` from frequent tokens in retrieved text, using `resources/dolma_stopwords.json`), `openstax` (scrapes OpenStax textbooks; needs the `openstax` extra), `misconceptions`, `chat_db` (ndjson chat logging).

Streamlit app code is outside the published package: `src/🤖_Math_QA.py` (entry point) and `src/pages/` form a multipage app, with helpers in `src/streamlit_app/` (`data_utils` builds the RetrievalDbs from the prebuilt `data/app_data` files for `rori_microlesson` and `openstax_subsection`; these embeddings were made with `text-embedding-ada-002`, so changing `EMBEDDING_MODEL` requires regenerating them). The apps' chat model is `chat_utils.CHAT_MODEL`, and `chat_utils.get_assistant_message` converts responses to plain `{"role", "content"}` dicts, which is what `PromptManager` stores. `Dockerfile.streamlit` packages the app, and the GitHub Action pushes the image to GCP Artifact Registry on every push to `main`.

`notebook/` holds exploratory/data-prep notebooks and `boneyard/` holds discarded Streamlit experiments. Neither is used by the package.

## Testing notes

Tests must never hit OpenAI. `tests/unit/conftest.py` has an autouse fixture that deletes `openai.resources.Embeddings.create` and `openai.resources.chat.Completions.create`. Tests that need embeddings monkeypatch `llm_math_education.embedding_utils.get_openai_embeddings` with `mock_get_openai_embeddings` (random vectors) from `conftest`. Use the `retrieval_db` / `retrieval_db_path` fixtures for a small throwaway DB. Integration tests in `tests/integration/` load the real `data/app_data` DBs.
