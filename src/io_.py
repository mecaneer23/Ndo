"""
File Input/Output handlers for Ndo
"""

from pathlib import Path

from src.todo import Todo, Todos


def read_file(filename: Path) -> str:
    """
    Attempt to read a file and return its contents.

    If the file does not exist, create it and return
    an empty string.
    """
    if not filename.exists():
        with filename.open("w"):
            return ""
    with filename.open() as file_obj:
        return file_obj.read()


def file_string_to_todos(raw_data: str) -> Todos:
    """Convert a TextIOWrapper to a list of `Todo`s"""
    if len(raw_data) == 0:
        return Todos([])
    return Todos([Todo(line) for line in raw_data.split("\n")])


def update_file(filename: Path, lst: Todos) -> int:
    """Write a list of `Todo`s to a provided file"""
    with filename.open("w", newline="\n") as file_obj:
        return file_obj.write("\n".join(map(repr, lst)))
