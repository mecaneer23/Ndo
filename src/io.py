"""
File Input/Output handlers for Ndo
"""

# pylint: disable=missing-function-docstring

from pathlib import Path

from src.class_todo import Todo


def read_file(filename: Path) -> str:
    if not filename.exists():
        with filename.open("w"):
            return ""
    with filename.open() as file_obj:
        return file_obj.read()


def file_string_to_todos(raw_data: str) -> list[Todo]:
    if len(raw_data) == 0:
        return []
    return [Todo(line) for line in raw_data.split("\n")]


def update_file(filename: Path, lst: list[Todo]) -> int:
    with filename.open("w", newline="\n") as file_obj:
        return file_obj.write("\n".join(map(repr, lst)))
