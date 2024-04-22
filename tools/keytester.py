#!/usr/bin/env python3
# pylint: disable=missing-docstring

# run with `python3 -m tools.keytester`

from argparse import ArgumentParser, Namespace


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("-a", "--acurses", action="store_true")
    return parser.parse_args()


if parse_args().acurses:
    import src.acurses as curses
else:
    import curses


def main(stdscr: curses.window) -> None:
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
