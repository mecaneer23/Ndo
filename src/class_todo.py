"""
Class definitions for a Todo, Todos (list of Todo),
and TodoList (list of Todo + cursor (int)).
"""

from collections.abc import Iterable
from enum import Enum

from src.get_args import CHECKBOX, INDENT
from src.utils import Chunk, Color


class FoldedState(Enum):
    """(FOLDED, DEFAULT, PARENT)"""

    FOLDED = 0
    DEFAULT = 1
    PARENT = 2


class BoxChar(Enum):
    """(MINUS -, PLUS +, NONE )"""

    MINUS = 0
    PLUS = 1
    NONE = 2

    @staticmethod
    def from_str(string: str) -> "BoxChar":
        """Convert a string to a BoxChar"""
        return {
            "-": BoxChar.MINUS,
            "+": BoxChar.PLUS,
        }[string]

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return {
            BoxChar.PLUS: "+",
            BoxChar.MINUS: "-",
            BoxChar.NONE: "",
        }[self]


class Todo:
    """
    A Todo object, representing parts of a
    string read from a text file.
    """

    def __init__(self, text: str = "") -> None:
        self._box_char: BoxChar = BoxChar.NONE
        self._color: Color = Color.WHITE
        self._display_text: str = ""
        self._text: str = ""
        self._indent_level: int = 0
        self._folded: FoldedState = FoldedState.DEFAULT
        self.set_text(text)

    def _init_box_char(self, pointer: int) -> tuple[BoxChar, int]:
        if len(self._text) > pointer and self._text[pointer] in "-+":
            return BoxChar.from_str(self._text[pointer]), pointer + 1
        return BoxChar.NONE, pointer

    def _init_color(self, pointer: int) -> tuple[Color, int]:
        if len(self._text) > pointer + 1 and self._text[pointer + 1] == " ":
            if self._text[pointer].isdigit():
                return Color(int(self._text[pointer])), pointer + 2
            if self._text[pointer] in "rgybmcw":
                return Color.from_first_char(self._text[pointer]), pointer + 2
        return Color.WHITE, pointer

    def _init_attrs(self) -> tuple[BoxChar, Color, str]:
        pointer = self._indent_level
        box_char, pointer = self._init_box_char(pointer)
        color, pointer = self._init_color(pointer)
        if len(self._text) > pointer and self._text[pointer] == " ":
            pointer += 1
        display_text = self._text[pointer:]

        return box_char, color, display_text

    def set_text(self, text: str) -> None:
        """
        Public _text setter method, can be used to
        reinitialize an existing instance.
        """
        self._text = text
        self._indent_level = len(text) - len(text.lstrip())
        if not self._text:
            self._box_char = BoxChar.MINUS
            self._color = Color.WHITE
            self._display_text = ""
            return
        self._box_char, self._color, self._display_text = self._init_attrs()

    def get_color(self) -> Color:
        """Getter for color"""

        return self._color

    def get_display_text(self) -> str:
        """Getter for display_text"""

        return self._display_text

    def get_indent_level(self) -> int:
        """Getter for indent level"""

        return self._indent_level

    def __getitem__(self, key: int) -> str:
        return self._text[key]

    def __len__(self) -> int:
        return len(self._display_text)

    def set_display_text(self, display_text: str) -> "Todo":
        """Setter method for display_text. Returns self."""
        self._display_text = display_text
        self._text = repr(self)
        return self

    def set_folded(self, state: FoldedState) -> None:
        """Setter for folded state"""
        self._folded = state

    def is_folded(self) -> bool:
        """Return if folded state is folded"""
        return self._folded == FoldedState.FOLDED

    def is_folded_parent(self) -> bool:
        """Return whether folded state is parent"""
        return self._folded == FoldedState.PARENT

    def is_toggled(self) -> bool:
        """Return True if this Todo is toggled on"""
        return self._box_char == BoxChar.PLUS

    def set_indent_level(self, indent_level: int) -> None:
        """Setter for indent_level"""
        self._indent_level = indent_level

    def set_color(self, color: Color) -> None:
        """Setter for color"""
        self._color = color

    def set_box_char(self, box_char: BoxChar) -> None:
        """Setter for box_char"""
        self._box_char = box_char

    def get_box(self) -> str:
        """Return fancy ASCII representation of box_char"""
        return {
            BoxChar.PLUS: f"{CHECKBOX}  ",
            BoxChar.MINUS: "☐  ",
            BoxChar.NONE: "",
        }[self._box_char]

    def get_simple_box(self) -> str:
        """Return simple ASCII representation of box_char"""
        return {
            BoxChar.PLUS: "[x] ",
            BoxChar.MINUS: "[ ] ",
            BoxChar.NONE: "",
        }[self._box_char]

    def has_box(self) -> bool:
        """Check if box_char is not None"""
        return self._box_char != BoxChar.NONE

    def is_empty(self) -> bool:
        """Check if display_text exists"""
        return self._display_text == ""

    def toggle(self) -> None:
        """Convert box_char to its compliment"""
        self._box_char = {
            BoxChar.PLUS: BoxChar.MINUS,
            BoxChar.MINUS: BoxChar.PLUS,
            BoxChar.NONE: BoxChar.NONE,
        }[self._box_char]
        self._text = repr(self)

    def indent(self) -> None:
        """Indent by global INDENT level"""
        self._indent_level += INDENT
        self._text = repr(self)

    def dedent(self) -> None:
        """De-indent by global INDENT level"""
        if self._indent_level >= INDENT:
            self._indent_level -= INDENT
            self._text = repr(self)

    def copy(self) -> "Todo":
        """Return a new object with the same data as this object"""
        return Todo(repr(self))

    def __repr__(self) -> str:
        return Chunk.join(
            Chunk(True, self._indent_level * " "),  # noqa: FBT003
            Chunk(
                self._box_char != BoxChar.NONE and not self.is_empty(),
                str(self._box_char),
            ),
            Chunk(self._color != Color.WHITE, str(self._color.as_char())),
            Chunk(
                (self._box_char != BoxChar.NONE and not self.is_empty())
                or self._color != Color.WHITE,
                " ",
            ),
            Chunk(True, self._display_text),  # noqa: FBT003
        )


class Todos(list[Todo]):
    """Wrapper around list of Todo objects"""

    def __init__(self, iterable: Iterable[Todo]) -> None:
        super().__init__(iterable)
