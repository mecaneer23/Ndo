"""
Convert a MarkDown table to a formatted Python list.
"""

from itertools import repeat
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


def _pad_columns(row: str, widths: tuple[int, ...] | int, delimiter: str = "|") -> str:
    """
    Pad each column (determined by `delimiter`), to a given width.

    `widths` can be a single int, which will be used for every column,
    or can be a tuple with length row.count(delimiter) - 1, with each
    index corresponding to a different column.

    Returns padded version of `row`.
    """

    if len(delimiter) != 1:
        raise ValueError(
            f"`delimiter` must be one character, is {len(delimiter)} characters"
        )
    if delimiter == " ":
        raise ValueError("`delimiter` cannot be a space")

    column_count = row.count(delimiter) - 1

    if isinstance(widths, tuple) and len(widths) != column_count:
        raise ValueError(
            "`widths` cannot be a tuple of arbitrary length. "
            f"Is {len(widths)}, should be {column_count}."
        )

    if isinstance(widths, int):
        widths = tuple(repeat(widths, column_count))

    column = 0
    backward_count = 1
    trailing_space_start = 0
    prev_delimiter_index = 0
    change_amount = 0
    new_row = ""

    for delim_loc, char in enumerate(row):
        if char != delimiter or delim_loc == 0:
            continue
        while row[delim_loc - backward_count] == " ":
            backward_count += 1
        trailing_space_start = delim_loc - backward_count + 1
        non_space_len = trailing_space_start - prev_delimiter_index
        if widths[column] < non_space_len:
            raise ValueError(
                f"Width of column `{column}` cannot be less than "
                f"{non_space_len}, is {widths[column]}"
            )
        change_amount = widths[column] - non_space_len
        for index in range(
            prev_delimiter_index, prev_delimiter_index + non_space_len + 1
        ):
            new_row += row[index]
        new_row += " " * change_amount
        prev_delimiter_index = delim_loc
        backward_count = 1
        column += 1

    new_row += delimiter
    return new_row


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

    max_column_lengths: tuple[int, ...] = tuple(
        map(
            lambda iterable: max(iterable) + 2,
            zip(*_exclusive_map(_get_column_widths, lines, exclude=frozenset({1}))),
        )
    )

    for i, _ in enumerate(lines):
        if i == 1:
            lines[1] = "-" * (sum(max_column_lengths) - 2)
            continue
        lines[i] = _pad_columns(lines[i], max_column_lengths)
        for old, new in {" | ": "  ", "| ": "", " |": ""}.items():
            lines[i] = lines[i].replace(old, new)

    return lines
