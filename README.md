# llm-math-education: Retrieval augmented generation for middle-school math question answering and hint generation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.8284412.svg)](https://doi.org/10.5281/zenodo.8284412)
[![License](https://img.shields.io/github/license/DigitalHarborFoundation/llm-math-education)](https://github.com/DigitalHarborFoundation/llm-math-education/blob/main/LICENSE)

How can we incorporate trusted, external math knowledge in generated answers to student questions?

`llm-math-education` is a Python package that implements basic retrieval augmented generation (RAG) and contains prompts for two primary use cases: general math question-answering (QA) and hint generation. It is currently designed to work only with the OpenAI generative chat API.

This project is [hosted on GitHub](https://github.com/DigitalHarborFoundation/llm-math-education).
Feel free to open an [issue](https://github.com/DigitalHarborFoundation/llm-math-education/issues) with questions, comments, or requests.

A [fork of this repository at `DigitalHarborFoundation/rag-for-math-qa`](https://github.com/DigitalHarborFoundation/rag-for-math-qa) contains research code and data used to publish [our workshop paper](https://arxiv.org/abs/2310.03184).

## Demo

You can explore the effects of the retrieval-augmented generation approach by using our [Streamlit app](https://llm-math-education-levon003.streamlit.app/About_this_app). You'll need to provide your own OpenAI API key.

Demo link: <https://llm-math-education.streamlit.app>

## Installation

The `llm-math-education` package is [available on PyPI](https://pypi.org/project/llm-math-education/).

```bash
pip install llm-math-education
```

## Usage

We assume that `OPENAI_API_KEY` is provided as an environment variable or set via `openai.api_key = your_api_key`.

Preliminary setup: specify a directory in which to save the embedding database.
```python
from pathlib import Path
demo_dir = Path("data") / "demo"
demo_dir.mkdir(exist_ok=True)
```

We'll use `llm-math-education` to answer a student question.
```python
student_question = "How do I identify common factors?"
```

These usage examples can be seen together in [src/usage_demo.py](/src/usage_demo.py).

### Acquiring textbook data for retrieval augmented generation

To do retrieval augmented generation, we need data.
We'll use an OpenStax Pre-algebra textbook as our retrieval data.

Note: the `llm_math_education.openstax` module relies on `requests` and `beautifulsoup4`, which are not listed as dependencies. Install them yourself with `pip` if you want to download and parse OpenStax textbooks.

```python
from llm_math_education import openstax
prealgebra_textbook_url = "https://openstax.org/books/prealgebra-2e/pages/1-introduction"
textbook_data = openstax.cache_openstax_textbook_contents(prealgebra_textbook_url, demo_dir / "openstax")
df = openstax.get_subsection_dataframe(textbook_data)

>>> df.columns
Index(['title', 'content', 'index', 'chapter', 'section'], dtype='object')
```

The parsing code is probably very brittle; it has only been tested with the Pre-algebra textbook.

### Creating an embedding lookup database from a dataframe

```python
from llm_math_education import retrieval
db_name = "openstax_prealgebra"
text_column_to_embed = "content"
openstax_db = retrieval.RetrievalDb(demo_dir, db_name, text_column_to_embed, df)
openstax_db.create_embeddings()
openstax_db.save_df()
```

### Loading an existing embedding database

Here, we compute the "distance" in embedding space between the student question and the documents in the database.

```python
openstax_db = retrieval.RetrievalDb(demo_dir, "openstax_prealgebra", "content")
distances = openstax_db.compute_string_distances(student_question)

>>> distances
[0.21348877 0.24298186 0.25825211 ... 0.25500673 0.24491884 0.22458498]
```

### Using the database to do retrieval augmented generation

#### Defining a retrieval strategy

```python
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
```

The key in the dictionary passed to the `MappedEmbedding` retrieval strategy identifies the key to be replaced in the prompt, in Python string formatting notation.

#### Starting a chat conversation with RAG

We'll use a `PromptManager` to build chat messages from a prompt, a retrieval strategy, and a user query.

```python
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

>>> messages
[{'role': 'user', 'content': 'Answer this question: How do I identify common factors?'
''
'Reference this text in your answer:'
'We will now look at an expression containing a product that is raised to a power. Look for a pattern. The exponent applies to each of the factors. This leads to the Product to a Power Property for Exponents. An example with numbers helps to verify this property:'}]
```

We can pass the formatted messages to the OpenAI API.

```python
import openai
completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-0613",
    messages=messages,
)
assistant_message = completion["choices"][0]["message"]

>>> assistant_message
{
  "role": "assistant",
  "content": "To identify common factors, you need to look for a pattern in an expression containing a product raised to a power. The exponent applies to each of the factors in this case. \n\nFor example, let's consider the expression (ab)^2. Here, (ab) is the product, and the exponent 2 applies to both 'a' and 'b'. To identify the common factors, you can separate the product into its individual factors:\n\n(ab)^2 = ab * ab\n\nNow, you can see that both 'a' and 'b' appear as factors in the expression. Therefore, 'a' and 'b' are the common factors. By identifying the factors that appear in multiple terms, you can determine the common factors of an expression.\n\nUsing numbers to verify this property, suppose we have the expression (2*3)^2, which simplifies to (6)^2. In this case, the common factor is 6, as both 2 and 3 are factors of 6."
}
```

#### Using PromptManager for multi-turn chat conversations

Add stored messages to continue the conversation.

```python
pm.add_stored_message(assistant_message)
messages = pm.build_query("I have a follow-up question...")
```

Clear stored messages to start a new conversation on the next call to `build_query()`.

```python
pm.clear_stored_messages()
```

### Using built-in prompts for math QA or hint generation

```python
from llm_math_education.prompts import mathqa as mathqa_prompts
pm.set_intro_messages(mathqa_prompts.intro_prompts["general_math_qa_intro"])
```

## Development

See the [developer's guide](/DEVELOPMENT.md).

Primary contributor:

 - Zachary Levonian (<levon003@umn.edu>)

Other contributors:

 - Owen Henkel
 - Bill Roberts

## FAQ

1. How can I cite this work?

    You should cite [our paper](https://arxiv.org/abs/2310.03184) at the NeurIPS’23 Workshop on Generative AI for Education (GAIED).

    You can cite this using the CITATION.cff file above (and the "Cite this repository" drop-down on GitHub for BibTeX) or the following citation:

    >Zachary Levonian, Chenglu Li, Wangda Zhu, Anoushka Gade, Owen Henkel, Millie-Ellen Postle, and Wanli Xing. 2023. [Retrieval-augmented Generation to Improve Math Question-Answering: Trade-offs Between Groundedness and Human Preference](https://arxiv.org/abs/2310.03184). In _NeurIPS’23 Workshop on Generative AI for Education (GAIED)_, New Orleans, USA. DOI:https://doi.org/10.48550/arXiv.2310.03184

2. How should I use this code?

   We aren't currently planning to add additional features to this package, although pull requests and bug reports are welcome.

   You should use the Python package as a dependency if you want a quick way to try retrieval augmented generation with the OpenAI API.
   However, this code is likely more useful as inspiration. You should fork or otherwise borrow from various components if you want some of the specific functionality implemented here. Heres a quick overview of the most important modules and their implementation:
     - `llm_math_education.prompts.{mathqa,hints}` - Contains the prompt templates we use for math QA and hint generation.
     - `llm_math_education.prompt_utils` - `PromptManager` is an abstraction for iteratively creating conversations that include a retrieval component.
     - `llm_math_education.retrieval_strategies` - `RetrievalStrategy` and its implementations demonstrates implementations that use embeddings to fill a slot within a prompt template with relevant documents.
     - `llm_math_education.retrieval` - `RetrievalDb` creates an embedding-backed in-memory lookup database for a Pandas DataFrame with a text column.
     - `llm_math_education.logit_bias` - Using the most frequent tokens in a retrieved document, creates a [logit_bias](https://help.openai.com/en/articles/5247780-using-logit-bias-to-define-token-probability) that can be used to increase the [faithfulness](https://arxiv.org/abs/2307.16877) of generations based on that retrieved document.

3. What license does this repository use?

   The code is released under the MIT license. The example data used in the Streamlit app is released CC BY-SA 4.0; see the `data/app_data` folder for more info. Additional details on the data are present in the developer's guide.
