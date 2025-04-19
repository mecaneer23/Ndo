"""Utils for testing acurses."""

import contextlib
import time
from collections.abc import Iterator
from unittest.mock import patch


@contextlib.contextmanager
def mock_stdin_input(data: str) -> Iterator[None]:
    """
    Context manager to mock sys.stdin.read(1) for threaded stdin readers.

    Args:
        data (str): Simulated keystroke input, like "abc" or escape sequences.
    """
    input_iter = iter(data)

    def fake_stdin_read(_: int) -> str:
        try:
            return next(input_iter)
        except StopIteration:
            time.sleep(1)  # Simulate blocking after input is exhausted
            return ""

    with patch("sys.stdin.read", side_effect=fake_stdin_read):
        yield
