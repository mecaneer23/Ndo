"""
Functions to detect tab size in a file.
"""

from collections import Counter

from ndo.get_args import INDENT
from ndo.todo import Todos


def detect_tab_size(lines: list[str]) -> int:
    """Return the most likely tab size for the given lines"""
    indent_sizes: Counter[int] = Counter(
        [len(line) - len(line.lstrip()) for line in lines],
    )
    if 0 in indent_sizes:
        indent_sizes.pop(0)
    # doesn't account for modulo 0 tab sizes - so if we have 2, 4,
    # and 6 spaces, we should consider 2 as the tab size
    return indent_sizes.most_common(1)[0][0] if indent_sizes else 0


def modify_tab_size(todos: Todos) -> None:
    """
    Modify the tab size of each line to match the current INDENT level
    """
    raise NotImplementedError("Not yet tested")
    tab_size = detect_tab_size([repr(todo) for todo in todos])
    for todo in todos:
        spaces = todo.get_indent_level()
        if spaces == 0:
            continue
        todo.set_indent_level(spaces // INDENT * tab_size)
