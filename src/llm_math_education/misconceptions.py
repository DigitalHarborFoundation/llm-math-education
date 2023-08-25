import functools
import importlib.resources
import json
from operator import itemgetter

from llm_math_education import resources


@functools.cache
def get_misconception_list():
    """Cached version of `load_misconception_list`."""
    return load_misconception_list()


def load_misconception_list() -> list[dict[str, str]]:
    """Misconceptions resource generated in the `MisconceptionData.ipynb` notebook.

    Returns:
        list[dict[str, str]]: List of misconceptions.
    """
    resource_filepath = importlib.resources.files(resources) / "misconceptions.ndjson"
    with resource_filepath.open("r") as infile:
        misconception_list = json.load(infile)
    return misconception_list


@functools.cache
def get_misconceptions_string() -> str:
    misconception_list = get_misconception_list()
    misconception_list.sort(key=itemgetter("Topic", "ID"))
    descriptions = []
    for row in misconception_list:
        if not row["ID"].startswith("MaE"):
            continue
        description = row["Misconception"]
        description = description.split(".")[0]
        s = description.replace(";", ",").replace("\n", " ").strip()
        descriptions.append(s)
    misconception_string = "; ".join(descriptions)
    return misconception_string
