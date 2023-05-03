#!/usr/bin/env python3
# pyright: reportMissingImports=false

import curses
from pathlib import Path

STRIKETHROUGH = False
FILENAME = Path(__file__).parent.joinpath("todo.txt").absolute()
HELP_FILE = Path(__file__).parent.joinpath("README.md").absolute()
AUTOSAVE = True
HEADER = "TODO"
DEBUG_FLAG = False

COLORS = {
    "Red": 1,
    "Green": 2,
    "Yellow": 3,
    "Blue": 4,
    "Magenta": 5,
    "Cyan": 6,
    "White": 7,
}


class Todo:
    def _set_color(self, color):
        if str(color).isalpha():
            if len(self.text) - len(self.display_text) == 3:
                return int(self.text[1])
            return get_color(color)
        return color

    def __init__(self, text, color="White"):
        self.text = str(text)
        self.box_char = self.text[0]
        self.display_text = self.text.split(" ", 1)[1]
        self.color = self._set_color(color)

    def __getitem__(self, key):
        return self.text[key]

    def split(self, *a):
        return self.text.split(*a)

    def startswith(self, *a):
        return self.text.startswith(*a)

    def set_color(self, color):
        self.color = color if color not in (None, 0) else 7

    def get_box(self):
        table = {
            "+": "☑",
            "-": "☐",
        }

        if self.box_char in table:
            return table[self.box_char]
        raise KeyError(f"The first character of `{self.text}` is not one of (+, -)")

    def __repr__(self):
        return f"{self.box_char}{self.color} {self.display_text}"

    @staticmethod
    def join(items, separator: str = ""):
        return separator.join([item.display_text for item in items])

    @staticmethod
    def join_repr(items, separator: str = ""):
        return separator.join([repr(item) for item in items])


class EmptyTodo(Todo):
    def __init__(self):
        super().__init__("-7 \t")

    def get_box(self):
        return " "


class UndoRedo:
    def __init__(self):
        self.history = []
        self.redos = []
        self.index = -1

    def handle_return(self, undo_or_redo, todos: list, selected: int):
        """
        this is the only non-reusable function from this class
        This function takes in a list of current values and
        returns a list with the values after being undone
        """
        returns = undo_or_redo(todos, selected)
        if isinstance(returns, tuple):
            return returns
        elif isinstance(returns, list):
            return returns, selected
        elif isinstance(returns, int):
            return todos, returns
        else:
            return todos, selected

    def undo(self, todos, selected):
        if self.index < 0:
            return todos, selected
        func, args = self.history[self.index]
        self.index -= 1
        to_debug_file(Path("debugging/pointer.txt"), self.index)
        return func(*args)

    def redo(self, todos, selected):
        if self.index >= len(self.history) - 1:
            return todos, selected
        self.index += 1
        func, args = self.redos[self.index]
        to_debug_file(Path("debugging/pointer.txt"), self.index)
        return func(*args)

    def add_undo(self, revert_with, *args):
        self.history.append((revert_with, deepcopy_ignore(args)))
        self.index = len(self.history) - 1
        to_debug_file(Path("debugging/history.txt"), repr(self))
        to_debug_file(Path("debugging/pointer.txt"), self.index)

    def do(self, func, *args):
        # TODO: now I have the redo function and the
        # args it needs... how should I store it?
        # self.redos.append((func, deepcopy_ignore(args).append(args[1][args[2]]) if func.__name__ == "new_todo_next" else deepcopy_ignore(args)))
        return func(*args)

    def __repr__(self):
        return "\n".join(f"{i[0].__name__}: {i[1]}" for i in self.history)


def to_debug_file(filename: Path, message: str, mode="w"):
    if DEBUG_FLAG:
        with filename.open(mode) as f:
            f.write(str(message))


def read_file(filename: Path):
    if not filename.exists():
        with filename.open("w") as f:
            return ""
    with filename.open() as f:
        return f.read()


def validate_file(data):
    if len(data) == 0:
        return []
    lines = data.split("\n")
    for i in lines.copy():
        if len(i) == 0:
            lines.remove(i)
            continue
    return lines


def get_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="Ndo is a todo list program to help you manage your todo lists",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Controls:\n  "
        + "\n  ".join(md_table_to_lines(HELP_FILE, 29, 47, ["<kbd>", "</kbd>"])),
    )
    parser.add_argument(
        "--help",
        action="help",
        help="Show this help message and exit.",
    )
    parser.add_argument(
        "--autosave",
        "-s",
        action="store_true",
        default=AUTOSAVE,
        help="Boolean: determines if file is saved on every\
            action or only once at the program termination.",
    )
    parser.add_argument(
        "filename",
        type=str,
        nargs="?",
        default=FILENAME,
        help=f"Provide a filename to store the todo list in.\
            Default is `{FILENAME}`.",
    )
    parser.add_argument(
        "--strikethrough",
        "-t",
        action="store_true",
        default=STRIKETHROUGH,
        help="Boolean: strikethrough completed todos\
            - option to disable because some terminals\
            don't support strikethroughs.",
    )
    parser.add_argument(
        "--header",
        "-h",
        type=str,
        default=HEADER,
        help=f"Allows passing alternate header.\
            Make sure to quote multi-word headers.\
            Default is `{HEADER}`.",
    )
    parser.add_argument(
        "--help-file",
        type=str,
        default=HELP_FILE,
        help=f"Allows passing alternate file to\
        specify help menu. Default is `{HELP_FILE}`.",
    )
    return parser.parse_args()


def handle_args(args):
    global AUTOSAVE, FILENAME, HELP_FILE, STRIKETHROUGH, HEADER
    AUTOSAVE = args.autosave
    FILENAME = Path(args.filename)
    HELP_FILE = Path(args.help_file)
    STRIKETHROUGH = args.strikethrough
    HEADER = args.header


def deepcopy_ignore(lst):
    from _curses import window as curses_window
    from copy import deepcopy

    return [i if isinstance(i, curses_window) else deepcopy(i) for i in lst]


def ensure_within_bounds(counter: list, minimum: list, maximum: list):
    if counter < minimum:
        return minimum
    elif counter > maximum - 1:
        return maximum - 1
    else:
        return counter


def toggle_completed(char):
    return {
        "+": "-",
        "-": "+",
    }[char]


def update_file(filename, lst, save=AUTOSAVE):
    if not save:
        return 0
    with filename.open("w") as f:
        return f.write(Todo.join_repr(lst, "\n"))


def wgetnstr(win, n=1024, chars="", cursor="█"):
    """
    Reads a string from the given window with max chars n\
    and initial chars chars. Returns a string from the user\
    Functions like a JavaScript alert box for user input.

    Args:
        win (Window object):
            The window to read from. The entire window\
            will be used, so a curses.newwin() should be\
            generated specifically for use with this\
            function. As a box will be created around the\
            window's border, the window must have a minimum\
            height of 3 characters. The width will determine\
            a maximum value of n.
        n (int, optional):
            Max number of characters in the read string.\
            It might error if this number is greater than\
            the area of the window. Defaults to 1024.
        chars (str, optional):
            Initial string to occupy the window.\
            Defaults to "" (empty string).
        cursor (str, optional):
            Cursor character to display while typing.\
            Defaults to "█".

    Returns:
        str: Similar to the built in input() function,\
        returns a string of what the user entered.
    """
    if win.getmaxyx()[0] < 3:
        raise ValueError(
            "Window is too short, it won't be able to display the minimum 1 line of text."
        )
    original = chars
    chars = list(chars)
    position = len(chars)
    win.box()
    win.nodelay(False)
    while True:
        for i, v in enumerate("".join(chars).ljust(win.getmaxyx()[1] - 3)):
            win.addstr(1, i + 1, v, curses.A_REVERSE if i == position else 0)
        if position == len(chars):
            win.addstr(1, len(chars) + 1, cursor)
        win.refresh()
        try:
            ch = win.getch()
        except KeyboardInterrupt:  # ctrl+c
            return original
        if ch in (10, 13):  # enter
            break
        elif ch in (8, 127, 263):  # backspace
            if position > 0:
                position -= 1
                chars.pop(position)
        elif ch == 27:  # any escape sequence
            win.nodelay(True)
            if win.getch() == -1:  # escape, otherwise skip `[`
                return original
            win.nodelay(False)
            try:
                arrow = win.getch()
            except KeyboardInterrupt:
                return original
            if arrow == 68:  # left arrow
                if position > 0:
                    position -= 1
            elif arrow == 67:  # right arrow
                if position < len(chars):
                    position += 1
            elif arrow == 51:  # delete
                win.getch()  # skip the `~`
                if position < len(chars):
                    chars.pop(position)
        else:  # typable characters (basically alphanum)
            if len(chars) >= n:
                curses.beep()
                continue
            chars.insert(position, chr(ch))
            if position < len(chars):
                position += 1

    return "".join(chars)


def hline(win, y, x, ch, n):
    win.addch(y, x, curses.ACS_LTEE)
    win.hline(y, x + 1, ch, n - 2)
    win.addch(y, x + n - 1, curses.ACS_RTEE)


def insert_todo(stdscr, todos: list, index: int, existing_todo=False):
    y, x = stdscr.getmaxyx()
    if existing_todo:
        todo = todos[index].display_text
        ncols = max(x // 2, len(todo) + 3) if len(todo) < x - 1 else x // 2
        begin_x = x // 4 if len(todo) < x - 1 - ncols else (x - ncols) // 2
        todos[index].display_text = wgetnstr(
            curses.newwin(3, ncols, y // 2 - 3, begin_x), chars=todo
        )
        return todos
    if (todo := wgetnstr(curses.newwin(3, x // 2, y // 2 - 3, x // 4))) == "":
        return todos
    todos.insert(index, Todo(f"- {todo}"))
    return todos


def insert_empty_todo(todos, index):
    todos.insert(index, EmptyTodo())
    return todos


def remove_todo(todos: list, index):
    if len(todos) < 1:
        return todos
    todos.pop(index)
    return todos


def strikethrough(text):
    return "\u0336".join(text) if STRIKETHROUGH else text


def swap_todos(todos: list, idx1, idx2):
    if min(idx1, idx2) >= 0 and max(idx1, idx2) < len(todos):
        todos[idx1], todos[idx2] = todos[idx2], todos[idx1]
    return todos


def md_table_to_lines(filename, first_line_idx, last_line_idx, remove=[]):
    with filename.open() as f:
        lines = f.readlines()[first_line_idx - 1 : last_line_idx - 1]
    for i, _ in enumerate(lines):
        for item in remove:
            lines[i] = lines[i].replace(item, "")
        lines[i] = lines[i].split("|")[1:-1]
    lines[1] = ("-", "-")
    key_max = len(max([k.strip() for k, _ in lines], key=len))
    value_max = len(max([v.strip() for _, v in lines], key=len))
    lines[1] = ("-" * (key_max + 2), "-" * value_max)
    for i, (k, v) in enumerate(lines):
        lines[i] = (k.strip() + " " * (key_max - len(k.strip()) + 2) + v.strip()).ljust(
            key_max + value_max + 2
        )
    return lines


def help_menu(parent_win):
    parent_win.clear()
    parent_win.addstr(0, 0, "Help:", curses.A_BOLD)
    lines = md_table_to_lines(HELP_FILE, 29, 47, ["<kbd>", "</kbd>"])
    win = curses.newwin(
        len(lines) + 2,
        len(lines[0]) + 2,
        1,
        (parent_win.getmaxyx()[1] - (len(lines[0]) + 1)) // 2,
    )
    win.box()
    for i, v in enumerate(lines):
        win.addstr(i + 1, 1, v)
    hline(win, 2, 0, curses.ACS_HLINE, win.getmaxyx()[1])
    parent_win.refresh()
    win.refresh()
    win.getch()
    parent_win.clear()


def get_color(color):
    return COLORS[color]


def color_menu(parent_win, original: int):
    parent_win.clear()
    parent_win.addstr(0, 0, "Colors:", curses.A_BOLD)
    lines = [i.ljust(len(max(COLORS.keys(), key=len))) for i in COLORS.keys()]
    win = curses.newwin(
        len(lines) + 2,
        len(lines[0]) + 2,
        1,
        (parent_win.getmaxyx()[1] - (len(lines[0]) + 1)) // 2,
    )
    win.box()
    selected = original - 1
    while True:
        parent_win.refresh()
        for i, v in enumerate(lines):
            win.addstr(
                i + 1,
                1,
                v,
                curses.color_pair(get_color(v.strip()))
                | (curses.A_REVERSE if i == selected else 0),
            )
        try:
            key = win.getch()
        except KeyboardInterrupt:
            return original
        if key == 107:  # k
            selected -= 1
        elif key == 106:  # j
            selected += 1
        elif key == 103:  # g
            selected = 0
        elif key == 71:  # G
            selected = len(lines)
        elif key in (113, 27):  # q | esc
            return original
        elif key == 10:  # enter
            return get_color(lines[selected].strip())
        elif key in range(49, 56):  # numbers
            selected = key - 49
        else:
            continue
        selected = ensure_within_bounds(selected, 0, len(lines))
        parent_win.refresh()
        win.refresh()


def make_printable_sublist(height: int, lst: list, cursor: int):
    selected_buffer = min(height, 12) // 2
    sublist = lst.copy()
    if len(lst) <= height or cursor >= len(lst):
        return sublist, cursor
    start = max(0, cursor - selected_buffer)
    end = min(len(lst), cursor + selected_buffer + 1)
    if end - start < height:
        if start == 0:
            end = min(len(lst), height)
        else:
            start = max(0, end - height)
    sublist = lst[start:end]
    cursor = sublist.index(lst[cursor])
    return sublist, cursor


def print_todos(win, todos, selected):
    height, width = win.getmaxyx()
    new_todos, selected = make_printable_sublist(height - 1, todos, selected)
    for i, v in enumerate(new_todos):
        display_text = (
            strikethrough(v.display_text) if v.startswith("+") else v.display_text
        )
        win.addstr(
            i + 1,
            0,
            f"{v.get_box()}  {display_text[:width - 4].ljust(width - 4, ' ')}",
            curses.color_pair(v.color or get_color("White"))
            | (curses.A_REVERSE if i == selected else 0),
        )


def todo_from_clipboard(todos: list, selected: int):
    try:
        from pyperclip import paste
    except ModuleNotFoundError:
        exit(
            "`pyperclip` module required for paste operation.\
            Try `pip install pyperclip`"
        )
    todo = paste()
    if "\n" in todo:
        return todos
    todos.insert(selected + 1, Todo(f"- {todo}"))
    return todos


def cursor_up(selected, len_todos):
    return ensure_within_bounds(selected - 1, 0, len_todos)


def cursor_down(selected, len_todos):
    return ensure_within_bounds(selected + 1, 0, len_todos)


def cursor_top(len_todos):
    return ensure_within_bounds(0, 0, len_todos)


def cursor_bottom(len_todos):
    return ensure_within_bounds(len_todos, 0, len_todos)


def cursor_to(position, len_todos):
    return ensure_within_bounds(position, 0, len_todos)


def todo_up(stdscr, todos, selected):
    todos = swap_todos(todos, selected, selected - 1)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos, cursor_up(selected, len(todos))


def todo_down(stdscr, todos, selected):
    todos = swap_todos(todos, selected, selected + 1)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos, cursor_down(selected, len(todos))


def new_todo_next(
    stdscr, todos: list, selected: int, todo: Todo = None, paste: bool = False
):
    temp = todos.copy()
    if todo is None:
        todos = (
            insert_todo(stdscr, todos, selected + 1)
            if not paste
            else todo_from_clipboard(todos, selected)
        )
        stdscr.clear()
        if temp != todos:
            selected = cursor_down(selected, len(todos))
    else:
        todos.insert(selected, Todo(f"- {todo.display_text}"))
    update_file(FILENAME, todos)
    return todos, selected


def new_todo_current(stdscr, todos, selected):
    todos = insert_todo(stdscr, todos, selected)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def delete_todo(stdscr, todos, selected):
    todos = remove_todo(todos, selected)
    stdscr.clear()
    selected = cursor_up(selected, len(todos))
    update_file(FILENAME, todos)
    return todos, selected


def color_todo(stdscr, todos, selected):
    todos[selected].set_color(color_menu(stdscr, todos[selected].color))
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def edit_todo(stdscr, todos, selected):
    todos = insert_todo(stdscr, todos, selected, True)
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos


def copy_todo(todos, selected):
    try:
        from pyperclip import copy
    except ModuleNotFoundError:
        exit(
            "`pyperclip` module required for copy operation.\
            Try `pip install pyperclip`"
        )
    copy(todos[selected].display_text)


def paste_todo(stdscr, todos, selected):
    return new_todo_next(stdscr, todos, selected, paste=True)


def blank_todo(stdscr, todos, selected):
    insert_empty_todo(todos, selected + 1)
    selected = cursor_down(selected, len(todos))
    stdscr.clear()
    update_file(FILENAME, todos)
    return todos, selected


def toggle(todos, selected):
    todos[selected] = Todo(
        toggle_completed(todos[selected].box_char) + todos[selected][1:],
        color=todos[selected].color,
    )
    update_file(FILENAME, todos)
    return todos


def quit_program(todos):
    return update_file(FILENAME, todos, True)


def toggle_debug_flag(setting=None):
    global DEBUG_FLAG
    if setting is not None:
        DEBUG_FLAG = setting
        return
    DEBUG_FLAG = not DEBUG_FLAG


def reset_todos(todos: list):
    return todos.copy()


def relative_cursor_to(
    win, history: UndoRedo, todos: list, selected: int, first_digit: int
):
    total = str(first_digit)
    while True:
        try:
            key = win.getch()
        except KeyboardInterrupt:  # exit on ^C
            return selected
        if key in (259, 107):  # up | k
            history.add_undo(cursor_to, selected, len(todos))
            return history.do(cursor_to, selected - int(total), len(todos))
        elif key in (258, 106):  # down | j
            history.add_undo(cursor_to, selected, len(todos))
            return history.do(cursor_to, selected + int(total), len(todos))
        elif key in range(48, 58):  # digits
            total += str(key - 48)
            continue
        return selected


def init():
    curses.use_default_colors()
    curses.curs_set(0)
    for i, v in enumerate(
        [
            curses.COLOR_RED,
            curses.COLOR_GREEN,
            curses.COLOR_YELLOW,
            curses.COLOR_BLUE,
            curses.COLOR_MAGENTA,
            curses.COLOR_CYAN,
            curses.COLOR_WHITE,
        ],
        start=1,
    ):
        curses.init_pair(i, v, -1)


def main(stdscr, header):
    init()
    todos = [
        Todo(i) if i != "-7 \t" else EmptyTodo()
        for i in validate_file(read_file(FILENAME))
    ]
    selected = 0
    history = UndoRedo()

    while True:
        stdscr.addstr(0, 0, f"{header}:")
        print_todos(stdscr, todos, selected)
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:  # exit on ^C
            return quit_program(todos)
        if key in (259, 107):  # up | k
            history.add_undo(cursor_to, selected, len(todos))
            selected = history.do(cursor_up, selected, len(todos))
        elif key in (258, 106):  # down | j
            history.add_undo(cursor_to, selected, len(todos))
            selected = history.do(cursor_down, selected, len(todos))
        elif key == 75:  # K
            history.add_undo(todo_down, stdscr, todos, selected - 1)
            todos, selected = history.do(todo_up, stdscr, todos, selected)
        elif key == 74:  # J
            history.add_undo(todo_up, stdscr, todos, selected + 1)
            todos, selected = history.do(todo_down, stdscr, todos, selected)
        elif key == 111:  # o
            todos, selected = history.do(new_todo_next, stdscr, todos, selected)
            history.add_undo(delete_todo, stdscr, todos, selected)
        elif key == 79:  # O
            todos = history.do(new_todo_current, stdscr, todos, selected)
            history.add_undo(delete_todo, stdscr, todos, selected)
        elif key == 100:  # d
            history.add_undo(new_todo_next, stdscr, todos, selected, todos[selected])
            todos, selected = history.do(delete_todo, stdscr, todos, selected)
        elif key == 117:  # u
            todos, selected = history.handle_return(history.undo, todos, selected)
            update_file(FILENAME, todos)
        elif key == 18:  # ^R
            continue  # redo doesn't work right now
            todos, selected = history.handle_return(history.redo, todos, selected)
            update_file(FILENAME, todos)
        elif key == 99:  # c
            # TODO: not currently undoable (color to previous state)
            todos = color_todo(stdscr, todos, selected)
        elif key == 105:  # i
            history.add_undo(reset_todos, todos)
            todos = history.do(edit_todo, stdscr, todos, selected)
        elif key == 103:  # g
            history.add_undo(cursor_to, selected, len(todos))
            selected = history.do(cursor_top, len(todos))
        elif key == 71:  # G
            history.add_undo(cursor_to, selected, len(todos))
            selected = history.do(cursor_bottom, len(todos))
        elif key == 121:  # y
            # TODO: not currently undoable (copy previous item in clipboard)
            copy_todo(todos, selected)
        elif key == 112:  # p
            todos, selected = history.do(paste_todo, stdscr, todos, selected)
            history.add_undo(delete_todo, stdscr, todos, selected)
        elif key == 45:  # -
            todos, selected = history.do(blank_todo, stdscr, todos, selected)
            history.add_undo(delete_todo, stdscr, todos, selected)
        elif key == 104:  # h
            help_menu(stdscr)
        elif key == 98:  # b
            toggle_debug_flag()
        elif key in (113, 27):  # q | esc
            return quit_program(todos)
        elif key == 10:  # enter
            if isinstance(todos[selected], EmptyTodo):
                continue
            todos = history.do(toggle, todos, selected)
            history.add_undo(toggle, todos, selected)
        elif key in range(48, 58):  # digits
            selected = relative_cursor_to(stdscr, history, todos, selected, key - 48)
        else:
            continue
        stdscr.refresh()


if __name__ == "__main__":
    handle_args(get_args())
    curses.wrapper(main, header=HEADER)
