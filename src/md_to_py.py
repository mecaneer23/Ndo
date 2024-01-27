"""
Convert a MarkDown table to a formatted Python list.
"""

from typing import Callable, Iterable, Iterator, TypeVar

T = TypeVar("T")
S = TypeVar("S")


def _get_column_widths(
    row: str, delimiter: str = "|", strip_spaces: bool = True
) -> list[int]:
    """
    Return a list of column widths. Columns are determined by a delimiter
    character.

    `strip_spaces` provides a toggle between counting all characters
    in each column, versus counting characters excluding leading and
    trailing spaces

    The length of the returned list should be equal to row.count(delimiter) - 1
    """

    if len(delimiter) != 1:
        raise ValueError(
            f"`delimiter` must be one character, is {len(delimiter)} characters"
        )
    if delimiter == " ":
        raise ValueError("`delimiter` cannot be a space")

    count = 0
    backward_count = 1
    column = -1
    output: list[int] = []
    starts_with_space = strip_spaces

    while count < len(row):
        if row[count] != " ":
            starts_with_space = False
        if row[count] == delimiter:
            if strip_spaces:
                while row[count - backward_count] == " ":
                    backward_count += 1
                    output[column] -= 1
                backward_count = 1
            column += 1
            output.append(-1)
            if strip_spaces:
                output[column] += 1
                starts_with_space = True
        if column > -1 and not starts_with_space:
            output[column] += 1
        count += 1

    return output[:-1]


def _exclusive_map(
    func: Callable[[T], S],
    *sequences: Iterable[T],
    exclude: frozenset[int] = frozenset(),
) -> Iterator[S]:
    """
    Similar to the built-in `map` function, but allows for
    exclusion of certain elements of `seq`.

    `exclude` should be a set of indices to exclude.
    """

    for i, arguments in enumerate(zip(*sequences)):
        if i not in exclude:
            yield func(*arguments)


def md_table_to_lines(
    first_line_idx: int,
    last_line_idx: int,
    filename: str = "README.md",
    remove: frozenset[str] = frozenset(),
) -> list[str]:
    """
    Convert a Markdown table to a list of formatted strings.

    Arguments
    ---------

    - `first_line_idx` (int): The index of the first line of the markdown
    table to be converted.
    - `last_line_idx` (int): The index of the last line of the markdown
    table to be converted.
    - `filename` (str, optional): The name of the file
    containing the table. Default is "README.md".
    - `remove` (frozenset[str], optional): The set of strings to be
    removed from each line. Default is an empty set.

    Returns
    -------

    -  `list[str]`: A list of formatted strings representing the converted
    Markdown table.

    """

    _ = """
    ## Examples

    | Item      | Quantity | Price |
    | --------- | -------- | ----- |
    | Apple     | 5        | $1.00 |
    | Banana    | 3        | $1.50 |
    | Orange    | 2        | $0.75 |
    | Pineapple | 1        | $3.50 |

    ```python
    >>> print("\n".join(md_table_to_lines(23, 29)))
    Item       Quantity  Price
    --------------------------
    Apple      5         $1.00
    Banana     3         $1.50
    Orange     2         $0.75
    Pineapple  1         $3.50

    ```

    | Flag            | Description                     |
    | --------------- | ------------------------------- |
    | **-h**          | Display help message            |
    | **-v**          | Enable verbose output           |
    | **-f** FILENAME | Specify input file              |
    | **-o** FILENAME | Specify output file             |
    | **-n**          | Do not overwrite existing files |

    ```python
    >>> print("\n".join(md_table_to_lines(41, 48, remove=("**",))))
    Flag         Description
    --------------------------------------------
    -h           Display help message
    -v           Enable verbose output
    -f FILENAME  Specify input file
    -o FILENAME  Specify output file
    -n           Do not overwrite existing files

    ```
    """

    if last_line_idx <= first_line_idx:
        raise ValueError("Last line index must be greater than first line index.")

    try:
        with open(filename, encoding="utf-8") as markdown_file:
            lines = markdown_file.read().splitlines()[
                first_line_idx - 1 : last_line_idx - 1
            ]
    except FileNotFoundError as err:
        raise FileNotFoundError("File not found.") from err

    for i, _ in enumerate(lines):
        for item in remove:
            lines[i] = lines[i].replace(item, "")

    max_column_lengths = list(
        map(
            max,
            zip(*_exclusive_map(_get_column_widths, lines, exclude=frozenset({1}))),
        )
    )
    print(max_column_lengths)
    for i, _ in enumerate(lines):
        for old, new in {" | ": "  ", "| ": "", " |": ""}.items():
            lines[i] = lines[i].replace(old, new)

    lines[1] = "-" * (sum(max_column_lengths) + 2 * (len(max_column_lengths) - 1))

    return lines


if __name__ == "__main__":
    for line in md_table_to_lines(182, 189, "md_to_py.py", frozenset({"**"})):
        print(line)
    _ = """
| Flag            | Description                     | what stuff goes here? |
| --------------- | ------------------------------- | --------------------- |
| **-h**          | Display help message            | what stuff goes here? |
| **-v**          | Enable verbose output           | what stuff goes here? |
| **-f** FILENAME | Specify input file              | what stuff goes here? |
| **-o** FILENAME | Specify output file             | what stuff goes here? |
| **-n**          | Do not overwrite existing files | what stuff goes here? |
"""
