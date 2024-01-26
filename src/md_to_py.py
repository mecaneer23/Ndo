"""
Convert a MarkDown table to a formatted Python list.
"""


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


def md_table_to_lines(
    first_line_idx: int,
    last_line_idx: int,
    filename: str = "README.md",
    remove: tuple[str, ...] = (),
) -> list[str]:
    """
    Convert a Markdown table to a list of formatted strings.

    Arguments
    ---------

    - `first_line_idx` (int): The index of the first line of the markdown
    table to be converted.
    - `last_line_idx` (int): The index of the last line of the markdown
    table to be converted.
    - `filename` (str, optional): The name of the markdown file
    containing the table. Default is "README.md".
    - `remove` (tuple[str], optional): The list of characters to be
    removed from each line. Default is an empty list.

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

    if not isinstance(remove, tuple):  # pyright: ignore
        raise TypeError(f"`remove` must be a tuple, is `{type(remove).__name__}`")

    try:
        with open(filename, encoding="utf-8") as markdown_file:
            lines = markdown_file.read().splitlines()[
                first_line_idx - 1 : last_line_idx - 1
            ]
    except FileNotFoundError as err:
        raise FileNotFoundError("Markdown file not found.") from err

    max_column_lengths = list(map(_get_column_widths, lines))

    for i, _ in enumerate(lines):
        lines[i] = lines[i].replace("- | -", "----").replace(" | ", " " * +2)
        for item in remove + ("| ", " |"):
            lines[i] = lines[i].replace(item, "")

    return lines


if __name__ == "__main__":
    print(_get_column_widths("| Flag            | Description                     |"))
    for line in md_table_to_lines(130, 137, "md_to_py.py", ("*",)):
        pass
    _ = """
| Flag            | Description                     |
| --------------- | ------------------------------- |
| **-h**          | Display help message            |
| **-v**          | Enable verbose output           |
| **-f** FILENAME | Specify input file              |
| **-o** FILENAME | Specify output file             |
| **-n**          | Do not overwrite existing files |
"""
