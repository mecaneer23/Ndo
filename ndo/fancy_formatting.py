"""
Handle LaTeX-style formatting for text rendering
"""

from enum import Enum
from functools import cache
from typing import NamedTuple


class TextStyle(Enum):
    """
    StyleMap text styles
    """

    NORMAL = ""
    STYLE = "<STYLE>"
    BOLD = "**"
    ITALIC = "*"
    UNDERLINE = "__"
    STRIKETHROUGH = "~~"
    CODE = "`"


class StyledText(NamedTuple):
    """
    A piece of text with a style
    """

    text: str
    start_index: int
    end_index: int
    style: TextStyle


class Styles:
    """
    Ordered mapping for formatted text
    """

    def __init__(self) -> None:
        self._styles: list[StyledText] = []

    def get_styles(self) -> list[StyledText]:
        """
        Get the list of StyledText objects
        """
        return self._styles

    def tokenize_to_map(self, string: str) -> None:
        """
        Tokenize a string into an Styles object representing
        LaTeX-style formatting.

        Iterate through a string using two pointers.
        When a style marker is found, create a new StyledText object,
        with the correct section of text and style.

        Currently doesn't support the following:
          - nested styles
          - unmatched style markers
          - using style markers as normal text
        """
        counter = 0
        current_style = TextStyle.NORMAL
        section_start = 0
        while counter < len(string):
            if string[counter] not in {"*", "_", "~", "`"}:
                counter += 1
                continue
            if section_start != counter:
                self._styles.append(
                    StyledText(
                        string[section_start:counter],
                        section_start,
                        counter,
                        current_style,
                    ),
                )
            style_token_len = 1
            if string[counter : counter + 2] in {"**", "__", "~~"}:
                style_token_len = 2
            if style_token_len == 1 and string[counter] == "_":
                counter += 1
                continue
            current_style = (
                TextStyle(string[counter : counter + style_token_len])
                if current_style == TextStyle.NORMAL
                else TextStyle.NORMAL
            )
            counter += style_token_len
            section_start = counter
            self._styles.append(
                StyledText(
                    " " * style_token_len,
                    counter,
                    counter,
                    TextStyle.STYLE,
                ),
            )

        if section_start == counter:
            return
        self._styles.append(
            StyledText(
                string[section_start:],
                section_start,
                len(string),
                TextStyle.NORMAL,
            ),
        )

    def as_string(self) -> str:
        """
        Return a string representation of the styles
        """
        output = ""
        for style in self._styles:
            if style.style == TextStyle.STYLE:
                continue
            symbol = style.style.value
            output += f"{symbol}{style.text}{symbol}"
        return output


@cache
def as_char_list(styles: Styles) -> list[TextStyle]:
    """
    Return a list of TextStyles, one for each
    character in the original string
    """
    if not styles:
        return []
    output: list[TextStyle] = []
    for style in styles.get_styles():
        output.extend([style.style] * len(style.text))
    return output
