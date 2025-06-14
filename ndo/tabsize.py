"""
Functions to detect tab size in a file.
"""

from collections import Counter
from itertools import combinations

from ndo.get_args import INDENT
from ndo.todo import Todos


def detect_tab_size(lines: list[str]) -> int:
    """
    Return the most likely tab size for the given lines
    """

    indents = Counter(len(line) - len(line.lstrip()) for line in lines)
    indents.pop(0, None)
    if not indents:
        return 0

    if len(indents) == 1:
        return next(iter(indents))

    differences: Counter[int] = Counter()
    for upper, lower in combinations(indents, 2):
        diff = abs(upper - lower)
        if diff > 0:
            differences[diff] += indents[lower] * indents[upper]

    if not differences:
        return 0

    return differences.most_common(1)[0][0]


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
