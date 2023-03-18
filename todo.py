#!/usr/bin/env python3

import curses
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
        return data
    for i in data.split("\n")[:-1]:
        assert i.startswith("-"), "not a vaild file"
    return data.split("\n")[:-1]


def parse_todos(data):
    return data


def ensure_within_bounds(counter, minimum, maximum):
    if counter < minimum:
        return minimum
    elif counter > maximum - 1:
        return maximum - 1
    else:
        return counter


def main(stdscr):
    curses.use_default_colors()
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, -1, -1)

    todo = parse_todos(validate_file(read_file(FILENAME)))
    selected = 1
    while True:
        for i, v in enumerate(todo):
            stdscr.addstr(i, 0, v, curses.color_pair(1 if i == selected else 2))
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:  # exit on ^C
            return end(stdscr, "Quit", score=score, best_score=best_score)
        if key in (119, 259, 107): # w | ^ | k
            selected -= 1
        # elif key in (97, 260, 104):  # a | < | h
        #     pass
        elif key in (115, 258, 106):  # s | v | j
            selected += 1
        # elif key in (100, 261, 108):  # d | > | l
        #     pass
        elif key in (113, 27):  # q | esc
            return
        else:
            continue
        selected = ensure_within_bounds(selected, 0, len(todo))
        stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(main)
