# pylint: disable=global-statement, missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from typing import Any


def to_lines_split(
    lines: list[str], remove: tuple[str, ...]
) -> tuple[int, list[list[str]]]:
    split: list[list[str]] = [[]] * len(lines)
    for i, _ in enumerate(lines):
        for item in remove:
            lines[i] = lines[i].replace(item, "")
        split[i] = lines[i].split("|")[1:-1]
    column_count = len(split[0])
    split[1] = ["-" for _ in range(column_count)]
    return column_count, split


def to_lines_join(split_lines: list[list[str]], columns: list[list[int]]) -> list[str]:
    joined_lines: list[str] = [""] * len(split_lines)
    for i, line in enumerate(split_lines):
        for j, char in enumerate(line):
            line[j] = char.strip().ljust(columns[j][0] + 2)
        joined_lines[i] = "".join(split_lines[i])
    joined_lines[1] = "-" * (sum(list(zip(*columns))[0]) + 2 * (len(columns) - 1))
    return joined_lines


def md_table_to_lines(
    first_line_idx: int,
    last_line_idx: int,
    filename: str = "README.md",
    remove: tuple[str, ...] = (),
) -> list[str]:
    """
    Converts a Markdown table to a list of formatted strings.

    Args:
        first_line_idx (int): The index of the first line of the Markdown
        table to be converted.
        last_line_idx (int): The index of the last line of the Markdown
        table to be converted.
        filename (str, optional): The name of the markdown file containing the
        table. Default is "README.md".
        remove (list[str], optional): The list of strings to be removed from each line.
        This is in the case of formatting that should exist in markdown but not
        python. Default is an empty list.

    Returns:
        list[str]: A list of formatted strings representing the converted
        Markdown table.

    Raises:
        ValueError: If the last line index is less than or equal to the
        first line index.
        FileNotFoundError: If the specified markdown file cannot be found.
    """

    # Check for valid line indices
    if last_line_idx <= first_line_idx:
        raise ValueError("Last line index must be greater than first line index.")

    # Get raw lines from the markdown file
    try:
        with open(filename, encoding="utf-8") as markdown_file:
            lines = markdown_file.readlines()[first_line_idx - 1 : last_line_idx - 1]
    except FileNotFoundError as err:
        raise FileNotFoundError("Markdown file not found.") from err

    # Remove unwanted characters and split each line into a list of values
    column_count, split_lines = to_lines_split(lines, remove)

    # Create lists of columns
    columns: list[list[Any]] = [[0, []] for _ in range(column_count)]
    for i in range(column_count):
        for line in split_lines:
            columns[i][1].append(line[i])

    # Find the maximum length of each column
    for i, (_, column) in enumerate(columns):
        columns[i][0] = len(max(map(str.strip, column), key=len))
    split_lines[1] = ["-" * (length + 1) for length, _ in columns]

    # Join the lines together into a list of formatted strings
    return to_lines_join(split_lines, columns)
