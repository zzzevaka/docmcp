from pathlib import Path
from typing import Union

from nbconvert import MarkdownExporter
from traitlets.config import Config

from app.projects.services.converters.ipython_notebook_preprocessors.image_preprocessor import (
    EmbedImagesAsDataURI,
)
from app.projects.services.converters.ipython_notebook_preprocessors.table_preprocessor import (
    HtmlTableToMarkdownPreprocessor,
)

CONFIG = Config()
CONFIG.NbConvertBase.display_data_priority = [
    "text/markdown",
    "text/plain",
    "image/png",
    "image/jpeg",
]


def convert_jupyter_notebook_to_markdown(temp_file_path: Union[str, Path]) -> str:
    exporter = MarkdownExporter(config=CONFIG)
    exporter.register_preprocessor(HtmlTableToMarkdownPreprocessor, enabled=True)
    exporter.register_preprocessor(EmbedImagesAsDataURI, enabled=True)

    markdown_content, _ = exporter.from_filename(str(temp_file_path))

    return markdown_content
