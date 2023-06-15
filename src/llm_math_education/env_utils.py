from pathlib import Path

import dotenv


def load_dotfile(env_dir: Path, dotfile_name: str = ".env"):
    assert dotenv.load_dotenv(env_dir / dotfile_name)
