#!/usr/bin/env python3

import curses
from _curses import window


def main(stdscr: window) -> None:
    curses.curs_set(0)
    y, x = (i // 2 for i in stdscr.getmaxyx())
    stdscr.addstr(0, 0, "Ctrl+C to exit\n")
    while True:
        try:
            ch = stdscr.getch()
            # ch = stdscr.getkey()
            # ch = stdscr.get_wch()
        except KeyboardInterrupt:
            return
        if ch == 3:  # ^C
            return
        stdscr.addstr(y, x, str(ch) + "      ")


if __name__ == "__main__":
    curses.wrapper(main)
