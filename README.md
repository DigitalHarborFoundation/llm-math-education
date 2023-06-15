# LLMs for Middle-School Math Question-Answering

External math knowledge for math QA.

### Local development setup

#### Python env

Install conda or miniconda.

```bash
conda create -f environment.yml
```

TODO update me with instructions on Make

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
