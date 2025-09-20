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

        Iterate through a string.
        When a style marker is found, create a new StyledText object,
        with the correct section of text and style.

        Currently doesn't support the following:
          - nested styles
          - unmatched style markers
          - using style markers as normal text
        """
        # TODO: reimplement using stack; handle nested styles, unmatched markers
        counter = 0
        current_style = TextStyle.NORMAL
        section_start = 0
        while counter < len(string):
            if string[counter] not in {"*", "_", "~", "`"} or (
                string[counter] == "_" and string[counter : counter + 2] != "__"
            ):
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

    def _get_superscript(self, char: str) -> str:
        """
        Convert a standard character to a superscript character
        """
        chars: dict[str, str] = {
            "0": "⁰",
            "1": "¹",
            "2": "²",
            "3": "³",
            "4": "⁴",
            "5": "⁵",
            "6": "⁶",
            "7": "⁷",
            "8": "⁸",
            "9": "⁹",
            "a": "ᵃ",
            "b": "ᵇ",
            "c": "ᶜ",
            "d": "ᵈ",
            "e": "ᵉ",
            "f": "ᶠ",
            "g": "ᵍ",
            "h": "ʰ",
            "i": "ⁱ",
            "j": "ʲ",
            "k": "ᵏ",
            "l": "ˡ",
            "m": "ᵐ",
            "n": "ⁿ",
            "o": "ᵒ",
            "p": "ᵖ",
            "q": "𐞥",
            "r": "ʳ",
            "s": "ˢ",
            "t": "ᵗ",
            "u": "ᵘ",
            "v": "ᵛ",
            "w": "ʷ",
            "x": "ˣ",
            "y": "ʸ",
            "z": "ᶻ",
            "A": "ᴬ",
            "B": "ᴮ",
            "C": "ᶜ",
            "D": "ᴰ",
            "E": "ᴱ",
            "F": "ꟳ",
            "G": "ᴳ",
            "H": "ᴴ",
            "I": "ᴵ",
            "J": "ᴶ",
            "K": "ᴷ",
            "L": "ᴸ",
            "M": "ᴹ",
            "N": "ᴺ",
            "O": "ᴼ",
            "P": "ᴾ",
            "Q": "ꟴ",
            "R": "ᴿ",
            "S": "ᔆ",  # no S superscript - use centered `S` or superscript `s`
            "T": "ᵀ",
            "U": "ᵁ",
            "V": "ⱽ",
            "W": "ᵂ",
            "X": "ᕽ",  # no X superscript, this one is close-ish  # noqa: RUF001
            "Y": "ʸ",  # there is no Y superscript in Unicode
            "Z": "ᶻ",  # there is no Z superscript in Unicode
        }
        if char not in chars:
            msg = f"Character '{char}' cannot be converted to superscript"
            raise ValueError(msg)
        return chars[char]

    def _handle_superscripts(self) -> None:
        """
        Convert characters between a `^` and a ` ` to superscript characters
        """
        msg = "Superscript handling not implemented yet"
        raise NotImplementedError(msg)


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
