"""
Standardized colors for Ndo
"""

from enum import Enum
from functools import cache
from typing import NamedTuple


class _InnerColor(NamedTuple):
    """
    Inner class to represent a color
    """

    color: "Color"
    name: str
    value: int


class Color(Enum):
    """
    Standardized colors for Ndo
    """

    NONE = 0
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    MAGENTA = 5
    CYAN = 6
    WHITE = 7

    @cache
    @staticmethod
    def _get_colors() -> list[_InnerColor]:
        """
        Get all colors as _InnerColors
        """
        return [
            _InnerColor(
                color=color,
                name=color.name,
                value=color.value,
            )
            for color in Color
            if color.value > 0
        ]

    def as_int(self) -> int:
        """
        Main getter for Ndo colors
        """
        return self.value

    def as_char(self) -> str:
        """Get lowercase first letter of color"""
        return self.name[0].lower()

    @staticmethod
    def from_first_char(char: str) -> "Color":
        """
        Return the color corresponding to its first character. Cannot
        distinguish between colors with the same first letter, so will return
        the first color that starts with `char`.
        """
        return {
            color.name.lower()[0]: color.color for color in Color._get_colors()
        }[char]

    @staticmethod
    def as_dict() -> dict[str, int]:
        """
        Get all colors represented as a mapping of color name
        to corresponding int value
        """
        return {
            color.name.capitalize(): color.value
            for color in Color._get_colors()
        }

    @staticmethod
    def is_valid(color: "Color | int") -> bool:
        """
        Check if a color is valid, either as an int or a Color
        """
        if isinstance(color, Color):
            return True
        return color in Color.as_dict().values()
