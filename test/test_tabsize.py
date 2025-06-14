"""
Tests for tabsize.py
"""
# ruff: noqa: S101, PLR2004
# pylint: disable=missing-function-docstring

from ndo.tabsize import detect_tab_size


def test_detect_tab_size() -> None:
    assert (
        detect_tab_size(
            [
                "\t-",
                "\t\t-",
                "\t\t\t-",
            ],
        )
        == 1
    )
    assert detect_tab_size([
        "  -",
        "   -",
        "  -",
    ]) == 2
    assert detect_tab_size([
        "-",
        " -",
        "  -",
        "-",
        "  -",
        "-",
        "-",
        "-",
        "  -",
        "  -",
        "  -",
        "  -",
        " -",
    ]) == 2
    assert detect_tab_size([
        "  -",
        "    -",
        "    -",
        "      -",
        "  -",
        "    -",
        "    -",
        "      -",
    ]) == 2
    assert detect_tab_size([
        "  -",
        "  -",
        "    -",
        "    -",
        "    -",
        "    -",
        "      -",
        "   -",
    ]) == 2
