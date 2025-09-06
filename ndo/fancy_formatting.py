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

        Iterate through a string using two pointers (left and right).
        When a style marker is found, create a new StyledText object,
        with the correct section of text and style.

        Currently doesn't support nested styles.
        """
        text_styles = [style.value for style in TextStyle]
        counter = 0
        current_style = TextStyle.NORMAL
        section_start = -1
        while counter < len(string):
            if string[counter] in text_styles:  # counter points to a single-char style or the first character of a double-char style
                # if string[counter : counter + 2] in text_styles:
                #     if section_start != -1:
                #         section_start = counter
                #     else:
                #         right = counter
                if current_style == TextStyle.NORMAL:
                    current_style = TextStyle(string[counter])
                    section_start = counter + 1
                else:
                    self._styles.append(
                        StyledText(
                            string[section_start : counter],
                            current_style,
                        ),
                    )
                    current_style = TextStyle.NORMAL
                    section_start = counter + 1
            counter += 1


if __name__ == "__main__":
    styles = Styles()
    # styles.tokenize_to_map("This is **bold** and *italic* text with `code`.")
    styles.tokenize_to_map("This is *italic* text with `code`.")
    print(styles.get_styles())
