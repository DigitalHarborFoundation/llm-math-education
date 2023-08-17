# llm-math-education: LLMs for Middle-School Math Question-Answering

How can we incorporate external math knowledge from trusted sources in generated answers to student questions?

The `llm-math-education` package implements basic retrieval augmented generation (RAG) and contains prompts for two primary use cases: general math question-answering (QA) and hint generation. It is currently designed to work only with the OpenAI generative chat API.

This project is [hosted on GitHub](https://github.com/levon003/llm-math-education).
Feel free to open an [issue](https://github.com/levon003/llm-math-education/issues) with questions, comments, or requests.


## Installation

The `llm-math-education` package is [available on PyPI](https://pypi.org/project/llm-math-education/).

```bash
pip install llm-math-education
```

## Basic usage

Assuming that `OPENAI_API_KEY` is provided as an environment variable or set via `openai.api_key = your_api_key`.

### Create an embedding lookup database from a dataframe

```python
# create a dataframe from an OpenStax textbook
```

## Development

See the [developer's guide](/DEVELOPMENT.md).
