#!/usr/bin/env python3

import curses


def main(stdscr):
    curses.curs_set(0)
    stdscr.addstr("Ctrl+C to exit\n")
    while True:
        try:
            ch = stdscr.getch()
            # ch = stdscr.getkey()
            # ch = stdscr.get_wch()
        except KeyboardInterrupt:
            return
        if ch == 3:  # ^C
            return
        stdscr.addstr(*[i // 2 for i in stdscr.getmaxyx()], str(ch) + "      ")


if __name__ == "__main__":
    curses.wrapper(main)
