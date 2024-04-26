#!/usr/bin/env python3

from sys import stdin
import tty
import termios
from time import time as now
from queue import Queue, Empty as queue_empty
import threading

_SHORT_TIME_SECONDS = 0.01


def _fill_queue(queue: Queue[int]):
    while True:
        queue.put(ord(stdin.read(1)))


def _main() -> None:
    chars: list[int] = []
    queue: Queue[int] = Queue()

    threading.Thread(target=_fill_queue, args=(queue,), daemon=True).start()

    while True:
        char = queue.get()
        if char != 27:
            if char == 113:
                return
            print(f"key: {char}", end="\n\r")
            continue
        esc = now()
        chars.append(27)
        while now() - esc < _SHORT_TIME_SECONDS:
            try:
                char = queue.get(timeout=_SHORT_TIME_SECONDS)
            except queue_empty:
                break
            if char not in chars:
                chars.append(char)
        print(chars, end="\n\r")
        chars.clear()


if __name__ == "__main__":
    old_settings = termios.tcgetattr(stdin)
    try:
        tty.setraw(stdin.fileno())
        _main()
    finally:
        termios.tcsetattr(stdin, termios.TCSADRAIN, old_settings)
        print("byeeeee")
