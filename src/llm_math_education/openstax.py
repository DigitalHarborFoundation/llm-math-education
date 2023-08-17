# Utilities for parsing OpenStax textbooks into a structured form
import re
import time
from pathlib import Path

import bs4
import pandas as pd
import requests

RETRIEVAL_DELAY_S = 0.25


def get_subsection_dataframe(textbook_data: list[dict]):
    textbook_data = parse_all_textbook_sections(textbook_data)

    ds = []
    for chapter_section in textbook_data:
        if "subsections" not in chapter_section:
            continue
        for subsection in chapter_section["subsections"]:
            subsection = subsection.copy()
            if "subsections" in subsection and subsection["subsections"] != []:
                for subsubsection in subsection["subsections"]:
                    subsection["content"] += subsubsection["title"] + ":\n" + subsubsection["content"]
            del subsection["subsections"]
            subsection["chapter"] = chapter_section["chapter"]
            subsection["section"] = chapter_section["section"]
            ds.append(subsection)
    openstax_subsection_df = pd.DataFrame(ds)
    return openstax_subsection_df


def parse_all_textbook_sections(textbook_data: list[dict]) -> pd.DataFrame:
    for chapter in textbook_data:
        if chapter["section"] == 0 or type(chapter["section"]) is str:
            continue
        if "subsections" not in chapter:
            subsections, suptitle = parse_textbook_soup(chapter["soup"])
            chapter["subsections"] = subsections
            chapter["title_text"] = suptitle
    return textbook_data


def cache_openstax_textbook_contents(url: str, outdir: Path, overwrite: bool = False):
    intro_filepath = outdir / "intro.html"
    if intro_filepath.exists() and not overwrite:
        with open(intro_filepath) as infile:
            html_doc = infile.read()
        soup = bs4.BeautifulSoup(html_doc, "html.parser")
    else:
        data = requests.get(url)
        html_doc = data.content.decode()
        soup = bs4.BeautifulSoup(html_doc, "html.parser")
        with open(intro_filepath, "w") as outfile:
            outfile.write(soup.prettify())
    toc = soup.find_all(attrs={"class": "os-text"})
    assert len(toc) > 0, "Unexpected table-of-contents structure."

    # parse URLs from the table of contents
    textbook_data = []
    toc_links = toc[3].parent.parent.parent.parent.parent.parent.find_all("a")
    for link in toc_links:
        href = link["href"]
        url_tokens = href.split("-")
        try:
            chapter = int(url_tokens[0])
        except ValueError:
            continue
        try:
            section = int(url_tokens[1])
        except ValueError:
            section = 0
        if section == 0:
            for expected_section_name in ["key-terms", "key-concepts", "review-exercises", "practice-test"]:
                if href.endswith(expected_section_name):
                    section = expected_section_name.replace("-", "_")
        if section == 0:
            continue
        textbook_data.append(
            {
                "chapter": chapter,
                "section": section,
                "href": href,
            },
        )
    # retrieve textbook data page by page
    root_url = url.split("pages")[0] + "pages/"
    for i, chapter_data in enumerate(textbook_data):
        part_filepath = outdir / f"part{i}.html"
        if part_filepath.exists() and not overwrite:
            with open(part_filepath) as infile:
                html_doc = infile.read()
            soup = bs4.BeautifulSoup(html_doc, "html.parser")
        else:
            data = requests.get(root_url + chapter_data["href"])
            html_doc = data.content.decode()
            soup = bs4.BeautifulSoup(html_doc, "html.parser")
            with open(part_filepath, "w") as outfile:
                outfile.write(soup.prettify())
            time.sleep(RETRIEVAL_DELAY_S)
        chapter_data["soup"] = soup
    return textbook_data


def parse_section(section):
    header_tags = ["title", "h1", "h2", "h3", "h4", "h5"]
    content_tags = [None, "strong", "em", "b", "li", "span", "a", "sup", "u"]
    if section.has_attr("class") and "section-exercises" in section["class"]:
        return
    section_title = ""
    section_content = ""
    n_replacements = 0
    n_tables = 0
    n_images = 0
    # replace math with text representation
    # (this avoids a problem with duplicating math spans)
    for math_span in section.find_all("math"):
        math_span.replace_with(math_span.find("annotation-xml").text)
        n_replacements += 1
    # replace images
    for img in section.find_all("img"):
        # img.replace_with("Figure: " + img["alt"])
        # TODO could also include the figure number and caption without much difficulty, if desired
        img.replace_with("")
        n_replacements += 1
        n_images += 1
    subsubsections = []
    for tag in section.contents:
        text_content = None
        if tag.name == "section":
            subsubsections.append(parse_section(tag))
            continue
        if tag.name in header_tags:
            tag_text = tag.text.strip()
            section_title += tag_text + " "
            # if tag_text.endswith("Exercises") or tag_text == "Practice Makes Perfect":
            #    break
        elif tag.name == "div":
            if tag.has_attr("data-type"):
                assert tag["data-type"] in ["note", "example", "equation"], tag
                # currently dropping this text, could save it
            elif tag.table is not None:
                n_tables += 1
                # text_content = tag.table["aria-label"]
            else:
                assert tag.figure is not None, tag
        elif type(tag) is bs4.NavigableString:
            text_content = tag.string
        else:
            assert len(tag.contents) == 1 or all(
                [child.name in content_tags for child in tag.children],
            ), f"{[child.name for child in tag.children if child.name not in content_tags]} {tag}"
            text_content = tag.text
        if text_content is not None:
            section_content += text_content + "\n"
    section_title = section_title.strip()
    section_content = re.sub(r"\n(\n)+", "\n\n", section_content.strip())
    return {
        "title": section_title,
        "content": section_content,
        "subsections": subsubsections,
    }


def parse_textbook_soup(soup):
    page = soup.find(attrs={"tabindex": "0"})
    suptitle = soup.find("h1").text
    # assert len(page.contents) == 1
    sections = []
    for i, section in enumerate(page.find_all("section", attrs={"data-depth": "1"})):
        parsed = parse_section(section)
        if parsed:
            parsed["index"] = i
            sections.append(parsed)
    return sections, suptitle
