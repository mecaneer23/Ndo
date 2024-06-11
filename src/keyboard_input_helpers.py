"""
Utility functions for handling keyboard input in curses
systems
"""

from typing import TypeVar

_T = TypeVar("_T")

def get_executable_args(
    args: str,
    possible_args: dict[str, _T | int],
) -> list[_T | int]:
    """
    Convert `args` from a comma-space (, ) delimited string
    to separate python objects provided in `possible_args`.

    If `args` == None, return empty list

    Example `possible_args`:
    possible_args: dict[str, list | int | str] = {
        "lst": lst,
        "len(lst)": len(lst),
        "set_str": set_str,
    }
    """
    params: list[_T | int] = []
    for arg in args.split(", "):
        if arg.isdigit():
            params.append(int(arg))
            continue
        if arg != "None":
            params.append(possible_args[arg])
    return params
