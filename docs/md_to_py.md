# `md_table_to_lines()` function

This function converts a markdown table to a list of formatted strings.

## Arguments

- `first_line_idx` (int): The index of the first line of the markdown table to be converted.
- `last_line_idx` (int): The index of the last line of the markdown table to be converted.
- `filename` (str, optional): The name of the markdown file containing the table. Default is "README.md".
- `remove` (list[str], optional): The list of characters to be removed from each line. Default is an empty list.

## Returns

- `list[str]`: A list of formatted strings representing the converted markdown table.

## Raises

- `ValueError`: If the last line index is less than or equal to the first line index.
- `FileNotFoundError`: If the specified markdown file cannot be found.

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
>>> print("\n".join(md_table_to_lines(41, 48, remove=["**"])))
Flag         Description
--------------------------------------------
-h           Display help message
-v           Enable verbose output
-f FILENAME  Specify input file
-o FILENAME  Specify output file
-n           Do not overwrite existing files

```
