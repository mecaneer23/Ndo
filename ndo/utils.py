"""
General utilities, useful across multiple other files
"""

from collections.abc import Iterator
from enum import Enum
from typing import NamedTuple


class Chunk(NamedTuple):
    """
    A chunk of text that can be toggled on or off based on a condition
    """

    condition: bool
    text: str

    @staticmethod
    def join(*chunks: "Chunk") -> str:
        """Join chunks with a True condition into one string"""
        return "".join([item for condition, item in chunks if condition])


class NewTodoPosition(Enum):
    """
    Represent how far offset a new todo should be from a current todo

    Usage might include values assumed to be integer representations
    of boolean values. Be careful when adding new values to this enum.
    """

    CURRENT = 0
    NEXT = 1


class Response(NamedTuple):
    """Represent a response object, similar to that from an HTTP response"""

    status_code: int
    message: str


def clamp(number: int, minimum: int, maximum: int) -> int:
    """
    Clamp a number in between a minimum and maximum.
    """
    return min(max(number, minimum), maximum - 1)


def overflow(counter: int, minimum: int, maximum: int) -> int:
    """
    Similar to clamp(), but instead of keeping a counter between
    two values, by leaving it at the min or max end, it wraps over
    the top or bottom.
    """
    if counter >= maximum:
        return minimum + (counter - maximum)
    if counter < minimum:
        return maximum - (minimum - counter)
    return counter


def chunk_message(
    message: str,
    width: int,
    delimiter: str = " ",
) -> Iterator[str]:
    """
    Split a message into chunks of length `width`
    (or as close as possible by splitting on `delimiter`)

    Algorithm:
      - Initialize a left and right pointer, left at
      the left end of the `message`, and right at the
      theoretical full width position
      - while True:
        - decrement right
        - if `message` has been exhausted, yield
        remaining as final value and break
        - if character at right position is delimiter,
        yield chunk upto that point and slide window to
        begin at next available position
        - if no delimiter in window, yield full width
        and slide window
    """
    left = 0
    right = width + 1
    while True:
        right -= 1
        if right >= len(message):
            yield message[left:]
            break
        if message[right] == delimiter:
            yield message[left:right]
            left = right + 1
            right += width
            continue
        if right == left:
            yield message[left : left + width]
            left += width
            right = left + width
