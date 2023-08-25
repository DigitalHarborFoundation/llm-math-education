# Developer's Guide

Basic background on developing from this codebase.

## Local development setup

### First-time setup

This repository uses Conda to manage two dependencies: Python and Poetry. ([This SO post](https://stackoverflow.com/a/71110028) provides more context on using Conda and Poetry together.)

Install conda or miniconda. Then, create the needed environment, called `llm-math-education`.

```bash
conda env create -f conda-environment.yml
```

### Python development

1. Activate the conda environment: `conda activate llm-math-education`
2. Use `make install` to install all needed dependencies (including the pre-commit hooks).

Ideally, the Makefile would activate the needed conda environment, but I don't actually know enough `make` to add that.

### Python releases

To deploy to PyPI, set your API token and deploy (see [guide](https://www.digitalocean.com/community/tutorials/how-to-publish-python-packages-to-pypi-using-poetry-on-ubuntu-22-04)):
```bash
poetry config pypi-token.pypi "{your API token generated on pypi.org}"
poetry build
poetry publish
```

### OpenAI API env variable

Create a `.env` file in the project root with your OpenAI API key defined as an environment variable inside it:

```bash
echo "OPENAI_API_KEY={your-api-key-here}" > .env
```

### Run tests

```bash
make test
```

### Other useful commands

 - `poetry run <command>` - Run the given command, e.g. `poetry run pytest` invokes the tests.
 - `source $(poetry env info --path)/bin/activate` - An alternative to `poetry shell` that's less buggy in conda environments.
 - `poetry add <package>` - Add the given package as a dependency. Use flag `-G dev` to add it as a development dependency.
 - `conda remove -n llm-math-education --all` - Tear it all down, so first-time setup can be repeated.

### Anserini support

To use Pyserini, need to install a few additional things.

First, Java 7+ JDK should be installed and configured reasonably. I installed the latest build (JDK 20.0.1) with no issues.

To install NMSLib: (see [issue](https://github.com/nmslib/nmslib/issues/476))
    CFLAGS="-mavx -DWARN(a)=(a)" pip install --use-pep517 nmslib

Ultimately, I added it to a new dependency group (`anserini`) like so:
    CFLAGS="-mavx -DWARN(a)=(a)" poetry add nmslib -G anserini

This likely means that rebuilds won't succeed without first installing nmslib with these CFLAGS, although I haven't tested it. Use `poetry install --with anserini` to include during a build.

FAISS (needed for Pyserini) installed in the outer conda environment:
    conda install -c pytorch faiss-cpu

I did not include the FAISS dependency in `environment.yaml`.

### Streamlit

A few notes about the app.

#### Authentication

For local development, streamlit secrets need to be stored in `.streamlit/secrets.toml`

Here's a sample file:
```
OPENAI_API_KEY = "{key goes here}"
AUTH_TOKEN = "argon2:$argon2id$v=19$m=10240,t=10,p=8$MuVIOw20jkOi1nKR90hPhA$H22nY8aNyfztLYQCSj5NRw5/Cy2WOo6kl3K61RyaoZY"
```

To generate the auth_token:
```
>>> import notebook.auth.security
>>> notebook.auth.security.passwd()
Enter password: abc
Verify password: abc
'argon2:$argon2id$v=19$m=10240,t=10,p=8$MuVIOw20jkOi1nKR90hPhA$H22nY8aNyfztLYQCSj5NRw5/Cy2WOo6kl3K61RyaoZY'
```

If the AUTH_TOKEN is provided in the secrets, can authenticate automatically via URL parameter, e.g. `{base_url}?auth_token=abc`.

## Data

The Streamlit demo draws on data from a few sources.

### OpenStax

OpenStax is a Rice University project to make high-quality math textbooks available (under a CC BY 4.0 license). Access for free at https://openstax.org.

### Rori

[Rori](https://rori.ai/) is a project of [Rising Academies](https://www.risingacademies.com/). Micro-lessons help students learn at their level.

### Math Nation

[Math Nation](https://www.mathnation.com/about/history-mission/) is an interactive math tool for middle and high school math. Student questions asked in pre-algebra and algebra forums are a high-validity example of general QA questions asked by middle-school math students.

### Misconception data

Math misconception data assembled by Nancy Otero. See [this GitHub repository](https://github.com/creature-ai/math-misconceptions).
