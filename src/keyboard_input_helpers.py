"""
Utility functions for handling keyboard input in curses
systems
"""

from typing import Mapping, TypeVar

_T = TypeVar("_T")

def get_executable_args(
    args: str,
    possible_args: Mapping[str, _T | int | str],
) -> list[_T | int | str]:
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
    if args == "None":
        return []
    params: list[_T | int | str] = []
    for arg in args.split(", "):
        if arg.isdigit():
            params.append(int(arg))
            continue
        params.append(possible_args.get(arg, arg))
    return params
