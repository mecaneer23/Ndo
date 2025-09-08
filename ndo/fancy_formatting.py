"""
Handle LaTeX-style formatting for text rendering
"""

from enum import Enum
from typing import NamedTuple


class TextStyle(Enum):
    """
    StyleMap text styles
    """

    NORMAL = ""
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

        Currently doesn't support nested styles.
        """
        counter = 0
        current_style = TextStyle.NORMAL
        section_start = 0
        while counter < len(string):
            if string[counter] not in {"*", "_", "~", "`"}:
                counter += 1
                continue
            self._styles.append(
                StyledText(
                    string[section_start:counter],
                    section_start,
                    counter,
                    current_style,
                ),
            )
            if string[counter : counter + 2] in {"**", "__", "~~"}:
                if current_style == TextStyle.NORMAL:
                    current_style = TextStyle(string[counter : counter + 2])
                else:
                    current_style = TextStyle.NORMAL
                counter += 2
                section_start = counter
                continue
            if current_style == TextStyle.NORMAL:
                current_style = TextStyle(string[counter])
            else:
                current_style = TextStyle.NORMAL
            counter += 1
            section_start = counter
        self._styles.append(
            StyledText(
                string[section_start:],
                section_start,
                len(string),
                current_style,
            ),
        )

    def as_string(self) -> str:
        """
        Return a string representation of the styles
        """
        output = ""
        for style in self._styles:
            symbol = style.style.value
            output += f"{symbol}{style.text}{symbol}"
        return output
