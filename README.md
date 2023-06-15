# LLMs for Middle-School Math Question-Answering

External math knowledge for math QA.

### Local development setup

#### First-time setup

This repository uses Conda to manage two dependencies: Python and Poetry.

Install conda or miniconda. Then, create the needed environment, called `llm-math-education`.

```bash
conda create -f environment.yml
```

#### Python

Activate the conda environment: `conda activate llm-math-education`

Use `make install` to install all needed dependencies.

#### OpenAI API env variable

Create a `.env` file in the project root with your OpenAI API key defined as an environment variable inside it:

```bash
echo "OPENAI_API_KEY={your-api-key-here}" > .env
```

#### Run tests

```bash
make test
```

#### Other useful commands

 - `poetry run <command>` - Run the given command, e.g. `poetry run pytest` invokes the tests.
 - `source $(poetry env info --path)/bin/activate` - An alternative to `poetry shell` that's less buggy in conda environments.
