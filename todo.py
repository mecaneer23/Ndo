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
    for i in data.split("\n"):
        assert i.startswith("-"), "not a vaild file"
    return data


def parse_todos(data):
    return data.split("\n")


def main(stdscr):
    curses.use_default_colors()
    curses.init_pair(1, -1, curses.COLOR_WHITE)
    todo = parse_todos(validate_file(read_file(FILENAME)))
    selected = 0
    while True:
        for i, v in enumerate(todo):
            stdscr.addstr(v, curses.color_pair(1 if i == selected else 0))
        stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(main)
