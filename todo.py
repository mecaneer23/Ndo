#!/usr/bin/env python3

import curses
from curses.textpad import rectangle as rect
import os

FILENAME = "todo.txt"


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
    return f"{table[item[0]]} {item.split(' ', 1)[1]}"


def toggle_completed(char):
    if char == "+":
        return "-"
    elif char == "-":
        return "+"


def update_file(filename, lst):
    with open(filename, "w") as f:
        return f.write("\n".join(lst))


def wgetnstr(win, n=1024, chars=""):
    win.nodelay(False)
    while True:
        ch = win.getch()
        # exit(str(ch))
        if ch == 10:  # enter
            break
        elif ch == 127:  # backspace
            chars = chars[:-1]
            win.delch(1, len(chars) + 1)
            win.insch(1, len(chars) + 1, " ")
        else:
            if (len(chars) < n):
                ch = chr(ch)
                chars += ch
                win.addch(1, len(chars), ch)
            else:
                curses.beep()
        win.refresh()

    return chars

def insert_todo(stdscr, todos: list, index):
    y, x = stdscr.getmaxyx()
    input_win = curses.newwin(3, 40, y // 2 - 3, x // 2 - 20)
    input_win.box()
    todo = wgetnstr(input_win)
    todos.insert(index, f"- {todo}")
    return todos


def remove_todo(stdscr, todos: list, index):
    todos.pop(index)
    return todos


def main(stdscr):
    curses.use_default_colors()
    curses.curs_set(0)

    todo = validate_file(read_file(FILENAME))
    selected = 0
    while True:
        stdscr.addstr(0, 0, "TODO:", curses.A_BOLD)
        for i, v in enumerate(todo):
            stdscr.addstr(
                i + 1, 0, format_item(v), curses.A_REVERSE if i == selected else 0
            )
        try:
            key = stdscr.getch()  # python3 -c "print(ord('x'))"
        except KeyboardInterrupt:  # exit on ^C
            return
        if key in (119, 259, 107):  # w | ^ | k
            selected -= 1
        elif key in (115, 258, 106):  # s | v | j
            selected += 1
        elif key == 105:  # i
            todo = insert_todo(stdscr, todo, selected + 1)
            stdscr.clear()
            selected += 1
            update_file(FILENAME, todo)
        elif key == 114:  # r
            todo = remove_todo(stdscr, todo, selected)
            stdscr.clear()
            selected -= 1
            update_file(FILENAME, todo)
        elif key == 101:  # e
            pass
        elif key in (113, 27):  # q | esc
            return
        elif key == 10:  # enter
            todo[selected] = toggle_completed(todo[selected][0]) + todo[selected][1:]
            update_file(FILENAME, todo)
        else:
            continue
        selected = ensure_within_bounds(selected, 0, len(todo))
        stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(main)
