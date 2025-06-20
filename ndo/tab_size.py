"""
Functions to detect tab size in a file.
"""

from collections import Counter
from itertools import combinations

from ndo.get_args import FILENAME, INDENT
from ndo.io_ import update_file
from ndo.keys import Key
from ndo.todo import Todos
from ndo.ui_protocol import CursesWindow
from ndo.window_interactions import alert


def _detect_tab_size(lines: list[str]) -> int:
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


def _modify_tab_size(todos: Todos, tab_size: int) -> None:
    """
    Modify the tab size of each line to match the current INDENT level
    """
    for todo in todos:
        spaces = todo.get_indent_level()
        if spaces == 0:
            continue
        todo.set_indent_level(int(spaces / tab_size * INDENT))


def format_todos(stdscr: CursesWindow, todos: Todos) -> None:
    """
    Format the todos to match the current INDENT level.
    """

    if len(todos) == 0:
        return

    tab_size = _detect_tab_size([repr(todo) for todo in todos])

    if tab_size in {INDENT, 0}:
        return

    if (
        alert(
            stdscr,
            "Automatically modify indent from tab size "
            f"{tab_size} spaces to {INDENT} spaces? "
            "Press `Enter` to proceed, or any other "
            "key to cancel",
        )
        != Key.enter
    ):
        return

    _modify_tab_size(todos, tab_size)
    update_file(FILENAME, todos)
