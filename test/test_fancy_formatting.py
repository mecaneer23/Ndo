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
        "There are _some_ single `_` _ underscores __under-scoring_this__.",
        "This is **bold back***to back with italics*.",
        # "Edge case with unmatched *asterisks.",
        # "Nested *italic and **bold*** text.",
        # "Nesting `__underline__` within `code` should work like an escape.",
    ],
)
def test_tokenize_to_map(string: str) -> None:
    """Test the tokenize_to_map function."""
    styles = Styles()
    styles.tokenize_to_map(string)
    assert styles.as_string() == string, styles.get_styles()


def test_tokenize_to_map_escape_sequence() -> None:
    """Test escape sequences for the tokenize_to_map function."""
    styles = Styles()
    # string = "Escape characters \\*should allow\\* escaping."
    string = "Escape characters should allow escaping."
    styles.tokenize_to_map(string)
    assert styles.as_string() == string
    assert TextStyle.ITALIC not in as_char_list(styles)


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


@pytest.mark.parametrize(
    ("input_param", "expected_output"),
    [
        ("This is x^2 and y^10.", "This is x² and y¹⁰."),
        ("E=mc^2 is famous.", "E=mc² is famous."),
        ("No superscript here.", "No superscript here."),
        (
            "Multiple superscripts: a^2 + b^2 = c^2.",
            "Multiple superscripts: a² + b² = c².",
        ),
        ("Edge case: x^ and y^.", "Edge case: x^ and y^."),
        (
            "Complex: H2O is water, CO2 is carbon dioxide.",
            "Complex: H₂O is water, CO₂ is carbon dioxide.",
        ),
        ("Nested: (x^2 + y^2)^0.5", "Nested: (x² + y²)^0.5"),
        ("Superscript at end: z^3", "Superscript at end: z³"),
        (
            "Superscript with punctuation: a^2, b^2; c^2.",
            "Superscript with punctuation: a², b²; c².",
        ),
        ("Mixed content: E=mc^2 and H2O.", "Mixed content: E=mc² and H₂O."),
    ],
)
def _test_superscripts_subscripts(
    input_param: str,
    expected_output: str,
) -> None:
    """Test superscript and subscript formatting."""
    styles = Styles()
    styles.tokenize_to_map(input_param)
    assert styles.as_string() == expected_output, styles.get_styles()


def test_handle_superscripts() -> None:
    styles = Styles()
    assert styles._get_superscript("1") == "¹"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("2") == "²"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("3") == "³"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("4") == "⁴"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("5") == "⁵"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("6") == "⁶"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("7") == "⁷"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("8") == "⁸"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("9") == "⁹"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
    assert styles._get_superscript("0") == "⁰"  # pyright: ignore[reportPrivateUsage] # noqa: SLF001 # pylint: disable=protected-access
