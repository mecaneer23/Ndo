"""Tests for fancy_formatting.py"""

import pytest

from ndo.fancy_formatting import Styles, TextStyle, as_char_list

# ruff: noqa: S101
# pylint: disable=missing-function-docstring


@pytest.mark.parametrize(
    "string",
    [
        "No formatting here.",
        "",
        "Special characters !@#$%^&() should be ignored.",
        "Code snippet: `print('Hello, World!')` in text.",
        "Just some **bold** text.",
        "Mixed **bold** and __underline__ text.",
        "This is **bold** and *italic* text with `code`.",
        "Multiple ~~strikethrough~~ examples ~~here~~.",
        "Ends with *italics*",
        "This is **bold back***to back with italics*.",
        # "Edge case with unmatched *asterisks.",
        # "Nested *italic and **bold*** text."
    ],
)
def test_tokenize_to_map(string: str) -> None:
    """Test the tokenize_to_map function."""
    styles = Styles()
    styles.tokenize_to_map(string)
    assert styles.as_string() == string, styles.get_styles()


def test_as_char_list() -> None:
    """Test the as_char_list function."""
    string = "a **b** c"
    styles = Styles()
    styles.tokenize_to_map(string)
    char_list = as_char_list(styles)
    assert char_list == [
        TextStyle.NORMAL,
        TextStyle.NORMAL,
        TextStyle.STYLE,
        TextStyle.STYLE,
        TextStyle.BOLD,
        TextStyle.STYLE,
        TextStyle.STYLE,
        TextStyle.NORMAL,
        TextStyle.NORMAL,
    ], char_list
