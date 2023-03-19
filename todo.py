#!/usr/bin/env python3

import curses
import os

STRIKETHROUGH = False
FILENAME = "todo.txt"
ACTIONS = {
    "MOVEUP": [
        ["w", "up arrow", "k"],
        "move up to select a todo",
    ],
    "MOVEDOWN": [
        ["s", "down arrow", "j"],
        "move down to select a todo",
    ],
    "INSERT": [
        [
            "i",
        ],
        "Add a new todo",
    ],
    "REMOVE": [
        [
            "r",
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
    win.nodelay(False)
    win.addstr(1, 1, chars)
    while True:
        ch = win.getch()
        if ch == 10:  # enter
            break
        elif ch == 127:  # backspace
            chars = chars[:-1]
            win.addch(1, len(chars) + 1, " ")
        else:
            if len(chars) < n:
                ch = chr(ch)
                chars += ch
                win.addch(1, len(chars), ch)
            else:
                curses.beep()
        win.refresh()

    return chars


def insert_todo(stdscr, todos: list, index, existing_todo=False):
    y, x = stdscr.getmaxyx()
    input_win = curses.newwin(3, 40, y // 2 - 3, x // 2 - 20)
    input_win.box()
    if existing_todo:
        todos[index] = f"- {wgetnstr(input_win, chars=todos[index].split(' ', 1)[1])}"
    else:
        todos.insert(index, f"- {wgetnstr(input_win)}")
    return todos


def remove_todo(todos: list, index):
    todos.pop(index)
    return todos


def strikethrough(text):
    return "\u0336".join(text) + "\u0336" if STRIKETHROUGH else text


def main(stdscr):
    curses.use_default_colors()
    curses.curs_set(0)

    todo = validate_file(read_file(FILENAME))
    selected = 0
    # revert_with = None

    while True:
        stdscr.addstr(0, 0, "TODO:", curses.A_BOLD)
        for i, v in enumerate(todo):
            box, text = format_item(v)
            stdscr.addstr(i + 1, 0, f"{box} ", curses.A_REVERSE if i == selected else 0)
            stdscr.addstr(
                i + 1,
                2,
                strikethrough(text) if v.startswith("+") else text,
                curses.A_REVERSE if i == selected else 0,
            )
        try:
            key = stdscr.getch()  # python3 -c "print(ord('x'))"
        except KeyboardInterrupt:  # exit on ^C
            return end(FILENAME, todo)
        if key in (119, 259, 107):  # w | ^ | k
            selected -= 1
            # revert_with = ACTIONS["MOVEDOWN"]
        elif key in (115, 258, 106):  # s | v | j
            selected += 1
            # revert_with = ACTIONS["MOVEUP"]
        elif key == 105:  # i
            todo = insert_todo(stdscr, todo, selected + 1)
            stdscr.clear()
            selected += 1
            update_file(FILENAME, todo)
            # revert_with = ACTIONS["REMOVE"]
        elif key == 114:  # r
            todo = remove_todo(todo, selected)
            stdscr.clear()
            selected -= 1
            update_file(FILENAME, todo)
            # revert_with = ACTIONS["INSERT"]
        # elif key == 117:  # u
        #     pass  # undo remove (or last action)
        elif key == 101:  # e
            todo = insert_todo(stdscr, todo, selected, True)
            stdscr.clear()
            update_file(FILENAME, todo)
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
    curses.wrapper(main)
