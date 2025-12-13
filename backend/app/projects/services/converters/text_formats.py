from pathlib import Path
from typing import Union


def convert_text_to_markdown(temp_file_path: Union[str, Path]) -> str:
    """
    Convert plain text files (.txt) to markdown.
    Plain text is already compatible with markdown, so we just read and return the content.
    """
    with open(str(temp_file_path), "r", encoding="utf-8") as f:
        content = f.read()
    return content


def convert_markdown_to_markdown(temp_file_path: Union[str, Path]) -> str:
    """
    Process markdown files (.md).
    Simply reads and returns the markdown content as-is.
    """
    with open(str(temp_file_path), "r", encoding="utf-8") as f:
        content = f.read()
    return content
