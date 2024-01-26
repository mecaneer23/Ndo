"""
Convert a MarkDown table to a formatted Python list.
"""


def _get_column_widths(row: str, delimiter: str = "|") -> list[int]:
    """
    Return a list of column widths. Columns are determined by a delimiter
    character.

    The length of the returned list should be equal to row.count(delimiter) - 1
    """
    if len(delimiter) > 1:
        raise TypeError(f"`delimiter` must be one character, is {len(delimiter)} characters")

    counter = 0
    column = -1
    output: list[int] = []

    while counter < len(row):
        if row[counter] == delimiter:
            column += 1
            output.append(-1)
        if column > -1:
            output[column] += 1
        counter += 1

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
    containing the table. Default is “README.md”.
    - `remove` (tuple[str], optional): The list of characters to be
    removed from each line. Default is an empty list.

    Returns
    -------

    -  `list[str]`: A list of formatted strings representing the converted
    Markdown table.

    Raises
    ------

    -  `ValueError`: If the last line index is less than or equal to the
    first line index.
    -  `FileNotFoundError`: If the specified markdown file cannot be
    found.
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
    column_count, split_lines = _to_lines_split(lines, remove)

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
    return _to_lines_join(split_lines, columns)
