import argparse
import textwrap
from typing import List, Union

import requests
from bs4 import BeautifulSoup, NavigableString, Tag


def fetch_html(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def extract_main_content(html: str) -> Tag:
    soup = BeautifulSoup(html, "html.parser")

    candidates = [
        soup.find("article"),
        soup.find("main"),
        soup.find("div", id="content"),
        soup.body,
    ]

    for candidate in candidates:
        if candidate:
            return candidate

    raise ValueError("Could not find a content container in the provided HTML")


def inline_to_markdown(node: Union[Tag, NavigableString]) -> str:
    if isinstance(node, NavigableString):
        return str(node)

    if node.name == "strong" or node.name == "b":
        return f"**{''.join(inline_to_markdown(c) for c in node.children)}**"
    if node.name == "em" or node.name == "i":
        return f"*{''.join(inline_to_markdown(c) for c in node.children)}*"
    if node.name == "code":
        return f"`{node.get_text(strip=True)}`"
    if node.name == "a":
        href = node.get("href", "").strip()
        text = ''.join(inline_to_markdown(c) for c in node.children).strip()
        if not text:
            text = href or "link"
        return f"[{text}]({href})" if href else text
    if node.name == "br":
        return "\n"

    return ''.join(inline_to_markdown(c) for c in node.children)


def block_to_markdown(node: Tag, indent_level: int = 0) -> str:
    lines: List[str] = []
    indent = "    " * indent_level

    if node.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(node.name[1])
        prefix = "#" * level
        lines.append(f"{prefix} {inline_to_markdown(node).strip()}\n")
    elif node.name == "p":
        text = inline_to_markdown(node).strip()
        if text:
            lines.append(f"{text}\n")
    elif node.name in {"ul", "ol"}:
        is_ordered = node.name == "ol"
        for idx, li in enumerate(node.find_all("li", recursive=False), start=1):
            bullet = f"{idx}. " if is_ordered else "- "
            content_parts: List[str] = []
            for child in li.children:
                if isinstance(child, NavigableString):
                    content_parts.append(str(child))
                elif isinstance(child, Tag):
                    if child.name in {"ul", "ol"}:
                        nested = block_to_markdown(child, indent_level + 1)
                        if nested:
                            content_parts.append("\n" + nested)
                    else:
                        content_parts.append(inline_to_markdown(child))
            line = indent + bullet + ''.join(content_parts).strip()
            lines.append(line)
        lines.append("")
    elif node.name == "table":
        rows = node.find_all("tr")
        table_data = [[inline_to_markdown(th).strip() for th in row.find_all(["th", "td"])] for row in rows]
        if table_data:
            header = table_data[0]
            separator = ["---" for _ in header]
            lines.append(" | ".join(header))
            lines.append(" | ".join(separator))
            for row in table_data[1:]:
                lines.append(" | ".join(row))
            lines.append("")
    elif node.name == "pre":
        code_text = node.get_text("\n").rstrip()
        if code_text:
            lines.append("```\n" + code_text + "\n```\n")
    else:
        for child in node.children:
            if isinstance(child, Tag):
                lines.append(block_to_markdown(child, indent_level))
            elif isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    lines.append(f"{indent}{text}\n")

    return "\n".join(filter(None, lines))


def html_to_markdown(html: str) -> str:
    content = extract_main_content(html)
    blocks = []
    for child in content.children:
        if isinstance(child, Tag):
            md = block_to_markdown(child)
            if md:
                blocks.append(md)
    markdown = "\n".join(blocks)
    return textwrap.dedent(markdown).strip() + "\n"


def scrape_release_notes(url: str) -> str:
    html = fetch_html(url)
    return html_to_markdown(html)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Salesforce release notes as Markdown")
    parser.add_argument("url", help="Release note URL to scrape")
    parser.add_argument(
        "--output",
        "-o",
        default="release_notes.md",
        help="Path to save the generated Markdown file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown = scrape_release_notes(args.url)
    with open(args.output, "w", encoding="utf-8") as file:
        file.write(markdown)
    print(f"Saved Markdown to {args.output}")


if __name__ == "__main__":
    main()
