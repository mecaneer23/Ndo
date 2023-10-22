# pylint: disable=missing-class-docstring, import-error
# pylint: disable=missing-function-docstring, missing-module-docstring

from get_args import CHECKBOX, INDENT


class Todo:
    def __init__(self, text: str = "") -> None:
        self.box_char: str | None = None
        self.color: int = 7
        self.display_text: str = ""
        self.text: str = ""
        self.indent_level: int = 0
        self.call_init(text)

    def _init_box_char(self, pointer: int) -> tuple[str | None, int]:
        if len(self.text) > pointer and self.text[pointer] in "-+":
            return self.text[pointer], pointer + 1
        return None, pointer

    def _init_color(self, pointer: int) -> tuple[int, int]:
        if (
            len(self.text) > pointer + 1
            and self.text[pointer].isdigit()
            and self.text[pointer + 1] == " "
        ):
            return int(self.text[pointer]), pointer + 2
        return 7, pointer

    def _init_attrs(self) -> tuple[str | None, int, str]:
        pointer = self.indent_level
        box_char, pointer = self._init_box_char(pointer)
        color, pointer = self._init_color(pointer)
        if len(self.text) > pointer and self.text[pointer] == " ":
            pointer += 1
        display_text = self.text[pointer:]

        return box_char, color, display_text

    def call_init(self, text: str) -> None:
        self.text = text
        self.indent_level = len(text) - len(text.lstrip())
        if not self.text:
            self.box_char = "-"
            self.color = 7
            self.display_text = ""
            return
        self.box_char, self.color, self.display_text = self._init_attrs()

    def __getitem__(self, key: int) -> str:
        return self.text[key]

    def __len__(self) -> int:
        return len(self.display_text)

    def set_display_text(self, display_text: str) -> None:
        self.display_text = display_text
        self.text = repr(self)

    def is_toggled(self) -> bool:
        if self.box_char is None:
            return False
        return self.box_char == "+"

    def set_indent_level(self, indent_level: int) -> None:
        self.indent_level = indent_level

    def set_color(self, color: int) -> None:
        self.color = color

    def get_box(self) -> str:
        table = {
            "+": f"{CHECKBOX}  ",
            "-": "☐  ",
            None: "",
        }

        if self.box_char in table:
            return table[self.box_char]
        raise KeyError(
            f"The completion indicator of `{self.text}` is not one of (+, -)"
        )

    def get_simple_box(self) -> str:
        table = {
            "+": "[x] ",
            "-": "[ ] ",
            None: "",
        }

        if self.box_char in table:
            return table[self.box_char]
        raise KeyError(
            f"The completion indicator of `{self.text}` is not one of (+, -)"
        )

    def has_box(self) -> bool:
        return self.box_char is not None

    def is_empty(self) -> bool:
        return self.display_text == ""

    def toggle(self) -> None:
        self.box_char = {"+": "-", "-": "+", None: ""}[self.box_char]
        self.text = repr(self)

    def indent(self) -> None:
        self.indent_level += INDENT
        self.text = repr(self)

    def dedent(self) -> None:
        if self.indent_level >= INDENT:
            self.indent_level -= INDENT
            self.text = repr(self)

    def __repr__(self) -> str:
        chunks: tuple[tuple[bool, str], ...] = (
            (True, self.indent_level * " "),
            (self.box_char is not None and not self.is_empty(), str(self.box_char)),
            (self.color != 7, str(self.color)),
            (
                (self.box_char is not None and not self.is_empty()) or self.color != 7,
                " ",
            ),
            (True, self.display_text),
        )
        return "".join([item for condition, item in chunks if condition])
