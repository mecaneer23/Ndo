"""Windows specific implementation of acurses"""

from ctypes import (
    Structure,
    Union,
    WinError,
    byref,
    windll,
    wintypes,
)
from enum import Enum
from sys import stdin
from typing import ClassVar

from ndo.keys import Key

TCSADRAIN = 1

_KEY_EVENT = 1
_EVENTS_IN_INPUT_RECORD = 1
_STD_INPUT_HANDLE = -10
_STD_OUTPUT_HANDLE = -11
_ENABLE_VIRTUAL_TERMINAL_PROCESSING = 4
_ENABLE_ECHO_INPUT = 4
_ENABLE_LINE_INPUT = 2

_CTRL_MOD = 12
_ALT_MOD = 3
_SHIFT_MOD = 16

_BACKSPACE = (0x57, 0x08)


def _enable_ansi(handle: int, mode_attrs: int) -> None:
    """Enable ANSI escape codes in the console"""
    handle = windll.kernel32.GetStdHandle(handle)
    mode = wintypes.DWORD()
    if not windll.kernel32.GetConsoleMode(
        handle,
        byref(mode),
    ):
        raise WinError()
    windll.kernel32.SetConsoleMode(
        handle,
        mode.value | mode_attrs,
    )


class _KeyEventRecord(Structure):  # pylint: disable=too-few-public-methods
    _fields_: ClassVar = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("uChar", wintypes.WCHAR),
        ("dwControlKeyState", wintypes.DWORD),
    ]


class _InputRecord(Structure):  # pylint: disable=too-few-public-methods
    class Event(Union):  # pylint: disable=too-few-public-methods
        """
        Represent an event

        https://learn.microsoft.com/en-us/windows/console/input-record-str
        """

        _fields_: ClassVar = [("KeyEvent", _KeyEventRecord)]

    _anonymous_ = ("Event",)
    _fields_: ClassVar = [
        ("EventType", wintypes.WORD),
        ("Event", Event),
    ]


class _VirtualKeyCode(Enum):
    """
    Virtual key codes when they differ to curses Keys (ndo.keys)

    https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    """

    VK_LEFT = 0x25
    VK_UP = 0x26
    VK_RIGHT = 0x27
    VK_DOWN = 0x28
    VK_INSERT = 0x2D
    VK_DELETE = 0x2E
    VK_PRIOR = 0x21  # Page Up
    VK_NEXT = 0x22  # Page Down
    VK_END = 0x23
    VK_HOME = 0x24

    def __hash__(self) -> int:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            return self.value == other
        msg = f"Cannot compare with {type(other)}"
        raise NotImplementedError(msg)


def _ansify(char: str, vk: int, mod: int) -> str:  # noqa: PLR0911
    ctrl = mod & _CTRL_MOD
    alt = mod & _ALT_MOD
    shift = mod & _SHIFT_MOD

    if ctrl and char.isalpha():
        return chr(ord(char.upper()) - ord("A") + 1)

    if alt and char != "\x00":
        return f"\x1b{char}"

    if vk == Key.tab and shift:
        return "\x1b[Z"

    if vk in _BACKSPACE and ctrl:
        return "\x1b\x7f"

    if vk in {
        _VirtualKeyCode.VK_LEFT,
        _VirtualKeyCode.VK_UP,
        _VirtualKeyCode.VK_RIGHT,
        _VirtualKeyCode.VK_DOWN,
    }:
        return "".join(
            (
                "\x1b[",
                "1;5" if ctrl else "",
                ["D", "A", "C", "B"][vk - _VirtualKeyCode.VK_LEFT.value],
            ),
        )

    specials: dict[_VirtualKeyCode, str] = {
        _VirtualKeyCode.VK_INSERT: "\x1b[2~",
        _VirtualKeyCode.VK_DELETE: "\x1b[3~",
        _VirtualKeyCode.VK_PRIOR: "\x1b[5~",
        _VirtualKeyCode.VK_NEXT: "\x1b[6~",
        _VirtualKeyCode.VK_END: "\x1b[F",
        _VirtualKeyCode.VK_HOME: "\x1b[H",
    }
    if vk in specials:
        return specials[_VirtualKeyCode(vk)]

    if char != "\x00":
        return char

    msg = f"Unsupported virtual key code: {vk} and character: {char}"
    raise ValueError(msg)


_read_buffer: list[str] = []


def _read(size: int = 1) -> str:
    """Read a character from the user"""

    if size != 1:
        msg = "Reading an amount of characters other than 1 is not supported"
        raise NotImplementedError(msg)

    if _read_buffer:
        return _read_buffer.pop(0)

    input_record = _InputRecord()

    while True:
        try:
            windll.kernel32.ReadConsoleInputW(
                windll.kernel32.GetStdHandle(_STD_INPUT_HANDLE),
                byref(input_record),
                _EVENTS_IN_INPUT_RECORD,
                byref(wintypes.DWORD()),
            )
        except KeyboardInterrupt as err:
            raise KeyboardInterrupt from err

        if input_record.EventType != _KEY_EVENT:
            continue
        key = input_record.KeyEvent
        if not key.bKeyDown:
            continue

        char = key.uChar
        vk = key.wVirtualKeyCode

        if char not in {
            Key.windows_esc_prefix,
            Key.windows_esc_prefix_,
        } and vk in {Key.shift, Key.ctrl, Key.alt}:
            continue

        _read_buffer.extend(
            _ansify(char, vk, key.dwControlKeyState) * (key.wRepeatCount or 1),
        )
        return _read_buffer.pop(0)


def tcgetattr(fd: int) -> int:
    """Get the terminal attributes"""
    mode = wintypes.DWORD()
    if not windll.kernel32.GetConsoleMode(
        windll.kernel32.GetStdHandle(fd),
        byref(mode),
    ):
        raise WinError()
    return mode.value


def tcsetattr(fd: int, when: int, mode: int) -> None:
    """Set the terminal attributes"""
    if when != TCSADRAIN:
        msg = "Only TCSADRAIN is supported for when"
        raise NotImplementedError(msg)
    windll.kernel32.SetConsoleMode(
        windll.kernel32.GetStdHandle(fd),
        mode,
    )


def setcbreak(fd: int) -> None:
    """Set the terminal to cbreak mode"""
    tcsetattr(
        fd,
        TCSADRAIN,
        tcgetattr(fd) & ~(_ENABLE_LINE_INPUT | _ENABLE_ECHO_INPUT),
    )


def init_windows() -> None:
    """Initialize the terminal"""
    stdin.read = _read
    stdin.fileno = lambda: _STD_INPUT_HANDLE
    _enable_ansi(_STD_OUTPUT_HANDLE, _ENABLE_VIRTUAL_TERMINAL_PROCESSING)

if __name__ == "__main__":
    init_windows()
