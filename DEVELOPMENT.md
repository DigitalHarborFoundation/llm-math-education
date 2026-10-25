# Developer's Guide

Basic background on developing from this codebase.

## Local development setup

### First-time setup

This repository uses [uv](https://docs.astral.sh/uv/) to manage Python and all dependencies. [Install uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
make install
```

This creates a `.venv` with the locked dependencies (`uv sync`), installs the pre-commit hooks, and registers a Jupyter kernel.

### Python releases

To deploy to PyPI, bump the version in `pyproject.toml`, then build and publish with your PyPI API token:
```bash
uv build
uv publish --token "{your API token generated on pypi.org}"
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

 - `uv run <command>` - Run the given command in the project environment, e.g. `uv run pytest` invokes the tests.
 - `uv add <package>` - Add the given package as a dependency. Use flag `--dev` to add it as a development dependency.
 - `uv lock --upgrade` - Upgrade all locked dependencies to the latest compatible versions.

### Dependency updates

Dependabot (configured in `.github/dependabot.yml`) opens monthly PRs for Python dependencies (`uv.lock`), pre-commit hooks, GitHub Actions, and the Dockerfile base images. The `Tests` workflow runs the tests and pre-commit hooks on every PR.

### Streamlit

A few notes about the app.

#### Deployment

Manually deployed via `levon003`'s (GitHub-linked) [Streamlit account](https://share.streamlit.io/).
Community Cloud installs dependencies from `uv.lock`. The app's Python version (currently 3.14) is set in the Streamlit console, and `.python-version` should match it.

#### Authentication

For local development, streamlit secrets need to be stored in `.streamlit/secrets.toml`

Here's a sample file:
```
OPENAI_API_KEY = "{key goes here}"
AUTH_TOKEN = "argon2:$argon2id$v=19$m=10240,t=10,p=8$MuVIOw20jkOi1nKR90hPhA$H22nY8aNyfztLYQCSj5NRw5/Cy2WOo6kl3K61RyaoZY"
```

To generate the auth_token:
```
>>> from streamlit_app import auth_utils
>>> import getpass
>>> auth_utils.passwd_hash(getpass.getpass())
Password: abc
'argon2:$argon2id$v=19$m=10240,t=10,p=8$VfrxYg66b419O8hFi+vCLA$HZXq1dU0+KMUbOBxJjLaweXoHguJH+2AkPL1EurOOys'
```

If the AUTH_TOKEN is provided in the secrets, can authenticate automatically via URL parameter, e.g. `{base_url}?auth_token=abc`.

Generate your own secure auth token.

First:

```
>>> from streamlit_app import auth_utils
>>> auth_token = auth_utils.generate_auth_token()
>>> auth_token
'21bbeab31ed2a3ebcd5563df65db64ba'
>>> auth_utils.passwd_hash(auth_token)
'argon2:$argon2id$v=19$m=10240,t=10,p=8$ECyPoKgu51axdr4rgktOCA$qmrYxYoSaVq4uCwm9W5csfltApcKBQRTHLdtQY9OVKI'
```

Second, put the generated token in `secrets.toml`:

```
AUTH_TOKEN="argon2:$argon2id$v=19$m=10240,t=10,p=8$ECyPoKgu51axdr4rgktOCA$qmrYxYoSaVq4uCwm9W5csfltApcKBQRTHLdtQY9OVKI"
```

Third, you can then authenticate with `{base_url}?auth_token=21bbeab31ed2a3ebcd5563df65db64ba`

#### Hint generation app

The standalone hint-generation app is hosted at `src/hint_generation/app.py`.

The password-protected demo for the hint generation component is deployed at this URL: <https://levi-math-hints.streamlit.app>

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
