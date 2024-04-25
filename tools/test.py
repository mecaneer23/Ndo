#!/usr/bin/env python3
"""Tester for acurses"""

# import curses
import src.acurses as curses

def _main(stdscr: curses.window):
    curses.use_default_colors()
    for i, color in enumerate(
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
        curses.init_pair(i, color, -1)
    # stdscr.box()
    # stdscr.addstr(1, 1, "Hello, world!", curses.color_pair(6))
    # win = curses.newwin(3, 7, 3, 3)
    # win.addstr(1, 1, str(win._height))
    # win.clear()
    # stdscr.refresh()
    # win.box()
    # win.refresh()
    # win.addstr(1, 1, "Bold text", color_pair(2))
    # win.clear()
    # stdscr.addstr(1, 1, "Bold text", color_pair(5) | A_STANDOUT)
    while True:
        x = stdscr.getch()
        stdscr.addstr(str(x) + "\n")
        if x == 113:
            break
        # stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(_main)
