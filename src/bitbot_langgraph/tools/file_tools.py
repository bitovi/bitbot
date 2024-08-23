import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Optional, Annotated, List
from langchain_core.tools import tool

from langchain_experimental.utilities import PythonREPL
from typing_extensions import TypedDict

import logging
logger = logging.getLogger(__name__)

WORKING_DIRECTORY_ENV = os.getenv("WORKING_DIRECTORY", "/app/docs_root")
WORKING_DIRECTORY = Path(WORKING_DIRECTORY_ENV)


@tool
def create_outline(
    points: Annotated[List[str], "List of main points or sections."],
    file_name: Annotated[str, "File path to save the outline."],
) -> Annotated[str, "Path of the saved outline file."]:
    """Create and save an outline."""

    # ensure path to file exists
    full_path = WORKING_DIRECTORY / file_name

    logger.info(f"tool(createOutline): Creating outline at {full_path}")
    try:
        full_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating directory {full_path.parent}: {e}"

    try:
        with (full_path).open("w") as file:
            for i, point in enumerate(points):
                file.write(f"{i + 1}. {point}\n")
    except Exception as e:
        return f"Error writing to file {full_path}: {e}"

    return f"Outline saved to {file_name}"


@tool
def read_document(
    file_name: Annotated[str, "File path to save the document."],
    start: Annotated[Optional[int], "The start line. Default is 0"] = None,
    end: Annotated[Optional[int], "The end line. Default is None"] = None,
) -> str:
    """Read the specified document."""
    full_path = WORKING_DIRECTORY / file_name
    logger.info(f"tool(readDocument): Reading document from {full_path}")

    try:
        with (full_path).open("r") as file:
            lines = file.readlines()
        if start is not None:
            start = 0
    except Exception as e:
        return f"Error reading file {file_name}: {e}"
    return "\n".join(lines[start:end])


@tool
def write_document(
    content: Annotated[str, "Text content to be written into the document."],
    file_name: Annotated[str, "File path to save the document."],
) -> Annotated[str, "Path of the saved document file."]:
    """Create and save a text document."""

    full_path = WORKING_DIRECTORY / file_name
    logger.info(f"tool(writeDocument): Writing document to {full_path}")
    try:
        WORKING_DIRECTORY.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return f"Error creating directory {WORKING_DIRECTORY}: {e}"
    
    try:
        with (full_path).open("w") as file:
            file.write(content)
    except Exception as e:
        return f"Error writing to file {file_name}: {e}"
    return f"Document saved to {file_name}"


@tool
def edit_document(
    file_name: Annotated[str, "Path of the document to be edited."],
    inserts: Annotated[
        Dict[int, str],
        "Dictionary where key is the line number (1-indexed) and value is the text to be inserted at that line.",
    ],
) -> Annotated[str, "Path of the edited document file."]:
    """Edit a document by inserting text at specific line numbers."""

    full_path = WORKING_DIRECTORY / file_name
    logger.info(f"tool(editDocument): Editing document {full_path}")
    try:
        with (full_path).open("r") as file:
            lines = file.readlines()
    except Exception as e:
        return f"Error reading file {file_name}: {e}"

    sorted_inserts = sorted(inserts.items())

    for line_number, text in sorted_inserts:
        if 1 <= line_number <= len(lines) + 1:
            lines.insert(line_number - 1, text + "\n")
        else:
            return f"Error: Line number {line_number} is out of range."

    try:
        with (full_path).open("w") as file:
            file.writelines(lines)
    except Exception as e:
        return f"Error writing to file {file_name}: {e}"

    return f"Document edited and saved to {full_path}"
