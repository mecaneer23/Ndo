#!/usr/bin/env python3

import curses

def main(stdscr):
	stdscr.addstr("Ctrl+C to exit\n")
	while True:
		try:
			ch = stdscr.getch()
		except KeyboardInterrupt:
			return
		stdscr.addstr(*[i//2 for i in stdscr.getmaxyx()], str(ch))

if __name__ == "__main__":
	curses.wrapper(main)
