#!/usr/bin/env python3

import curses
import os

STRIKETHROUGH = False
FILENAME = "todo.txt"
ACTIONS = {
    "MOVEUP": [
        ["up arrow", "k"],
        "move up to select a todo",
    ],
    "MOVEDOWN": [
        ["down arrow", "j"],
        "move down to select a todo",
    ],
    "INSERT": [
        [
            "o",
        ],
        "Add a new todo",
    ],
    "REMOVE": [
        [
            "d",
        ],
        "Remove selected todo",
    ],
    "QUIT": [
        [
            "q",
            "ctrl+c",
        ],
        "Quit",
    ],
    "TOGGLE": [
        [
            "enter",
        ],
        "Toggle a todo as completed",
    ],
    "EDIT": [
        [
            "i",
        ],
        "Edit an existing todo",
    ],
}
AUTOSAVE = True


def read_file(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            return ""
    with open(filename) as f:
        return f.read()


def validate_file(data):
    if len(data) == 0:
        return
    lines = data.split("\n")
    for i in lines.copy():
        if len(i) == 0:
            lines.remove(i)
            continue
        assert i[0] in "+-", "not a vaild file: line {}".format(
            data.split("\n").index(i)
        )
    return lines


def ensure_within_bounds(counter, minimum, maximum):
    if counter < minimum:
        return minimum
    elif counter > maximum - 1:
        return maximum - 1
    else:
        return counter


def format_item(item):
    table = {
        "+": "☑",
        "-": "☐",
    }
    return table[item[0]], item.split(" ", 1)[1]


def toggle_completed(char):
    if char == "+":
        return "-"
    elif char == "-":
        return "+"


def update_file(filename, lst, save=AUTOSAVE):
    if not save:
        return 0
    with open(filename, "w") as f:
        return f.write("\n".join(lst))


def end(filename, todos):
    return update_file(filename, todos, True)


def wgetnstr(win, n=1024, chars=""):
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
            Initial string to occupy the window. Defaults to "" (empty string).

    Returns:
        str: Similar to the built in input() function, returns a string of what the user entered.
    """
    assert (
        win.getmaxyx()[0] >= 3
    ), "Window is too short, it won't be able to display the minimum 1 line of text."
    original = chars
    win.box()
    win.nodelay(False)
    win.addstr(1, 1, f"{chars}█")
    while True:
        try:
            ch = win.getch()
        except KeyboardInterrupt:  # ctrl+c
            return original
        if ch in (10, 13):  # enter
            break
        elif ch == 127:  # backspace
            chars = chars[:-1]
            win.addstr(1, len(chars) + 1, "█ ")
        elif ch == 27:  # escape
            return original
        else:
            if len(chars) < n:
                ch = chr(ch)
                chars += ch
                win.addstr(1, len(chars), f"{ch}█")
            else:
                curses.beep()
        win.refresh()

    return chars


def insert_todo(stdscr, todos: list, index, existing_todo=False):
    y, x = stdscr.getmaxyx()
    input_win = curses.newwin(3, 40, y // 2 - 3, x // 2 - 20)
    if existing_todo:
        todos[index] = f"- {wgetnstr(input_win, chars=todos[index].split(' ', 1)[1])}"
    else:
        if (todo := wgetnstr(input_win)) == "":
            return todos
        todos.insert(index, f"- {todo}")
    return todos


def remove_todo(todos: list, index):
    todos.pop(index)
    return todos


def strikethrough(text):
    return "\u0336".join(text) if STRIKETHROUGH else text


def swap_todos(todos: list, idx1, idx2):
    if min(idx1, idx2) >= 0 and max(idx1, idx2) < len(todos):
        todos[idx1], todos[idx2] = todos[idx2], todos[idx1]
    return todos


def main(stdscr, header):
    curses.use_default_colors()
    curses.curs_set(0)

    todo = validate_file(read_file(FILENAME))
    selected = 0
    # revert_with = None
    if not header:
        header = "TODO"

    while True:
        stdscr.addstr(0, 0, f"{header}:", curses.A_BOLD)
        for i, v in enumerate(todo):
            box, text = format_item(v)
            stdscr.addstr(
                i + 1, 0, f"{box}  ", curses.A_REVERSE if i == selected else 0
            )
            stdscr.addstr(
                i + 1,
                3,
                strikethrough(text) if v.startswith("+") else text,
                curses.A_REVERSE if i == selected else 0,
            )
        try:
            key = stdscr.getch()  # python3 -c "print(ord('x'))"
        except KeyboardInterrupt:  # exit on ^C
            return end(FILENAME, todo)
        if key in (259, 107):  # up | k
            selected -= 1
            # revert_with = ACTIONS["MOVEDOWN"]
        elif key == 75:  # K
            todo = swap_todos(todo, selected, selected - 1)
            stdscr.clear()
            selected -= 1
            update_file(FILENAME, todo)
        elif key == 74:  # J
            todo = swap_todos(todo, selected, selected + 1)
            stdscr.clear()
            selected += 1
            update_file(FILENAME, todo)
        elif key in (258, 106):  # down | j
            selected += 1
            # revert_with = ACTIONS["MOVEUP"]
        elif key == 111:  # o
            temp = todo.copy()
            todo = insert_todo(stdscr, todo, selected + 1)
            stdscr.clear()
            if temp != todo:
                selected += 1
            update_file(FILENAME, todo)
            # revert_with = ACTIONS["REMOVE"]
        elif key == 100:  # d
            todo = remove_todo(todo, selected)
            stdscr.clear()
            selected -= 1
            update_file(FILENAME, todo)
            # revert_with = ACTIONS["INSERT"]
        # elif key == 117:  # u
        #     pass  # undo remove (or last action)
        elif key == 105:  # i
            todo = insert_todo(stdscr, todo, selected, True)
            stdscr.clear()
            update_file(FILENAME, todo)
            # revert_with = ACTIONS["EDIT"]
        elif key == 103:  # g
            selected = 0
        elif key == 71:  # G
            selected = len(todo)
        elif key == 104:  # h
            pass  # display help menu
        elif key in (113, 27):  # q | esc
            return end(FILENAME, todo)
        elif key == 10:  # enter
            todo[selected] = toggle_completed(todo[selected][0]) + todo[selected][1:]
            update_file(FILENAME, todo)
            # revert_with = ACTIONS["TOGGLE"]
        else:
            continue
        selected = ensure_within_bounds(selected, 0, len(todo))
        stdscr.refresh()


if __name__ == "__main__":
    from sys import argv

    curses.wrapper(main, header=" ".join(argv[1:]) if len(argv) > 1 else None)
