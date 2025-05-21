"""
Command line argument parser for Ndo

Modification instructions (adding a command line argument):


- add default

- add type to TypedNamespace

- add argument to parser

- add global variable to list at bottom of file


- update /README.md with new option

- ensure CONTROLS_BEGIN_INDEX and CONTROLS_END_INDEX in this file are still
correct
"""

from argparse import (
    ArgumentParser,
    ArgumentTypeError,
    Namespace,
    RawDescriptionHelpFormatter,
)
from enum import Enum
from pathlib import Path
from sys import argv
from types import ModuleType
from typing import TypeVar

CONTROLS_BEGIN_INDEX: int = 68
CONTROLS_END_INDEX: int = 99
INPUT_BEGIN_INDEX: int = 102
INPUT_END_INDEX: int = 121

_DEFAULT_BULLETS: bool = False
_DEFAULT_ENUMERATE: bool = False
_DEFAULT_FILENAME: Path = Path("todo.txt")
_DEFAULT_HEADER: list[str] = [""]
_DEFAULT_HELP_FILE: Path = (
    Path(__file__).parent.parent.joinpath("README.md").absolute()
)
_DEFAULT_INDENT: int = 2
_DEFAULT_RELATIVE_ENUMERATE: bool = False
_DEFAULT_RENAME: bool = False
_DEFAULT_SIMPLE_BOXES: bool = False
_DEFAULT_STRIKETHROUGH: bool = False

_CHECKBOX_OPTIONS = ("🗹", "☑")
_CONFIG_FILE_NAME = ".ndoconfig"


class UiType(Enum):
    """Represent various supported User Interfaces"""

    CURSES = "curses"
    ANSI = "ansi"
    TKINTER = "tkinter"
    NONE = "none"

    def __str__(self) -> str:
        return self.value


_DEFAULT_UI = UiType.ANSI


class TypedNamespace(Namespace):  # pylint: disable=too-few-public-methods
    """
    Add types to expected Namespace attributes
    """

    bullet_display: bool
    enumerate: bool
    filename: str
    title: list[str]
    help_file: Path
    indentation_level: int
    relative_enumeration: bool
    rename: bool
    simple_boxes: bool
    strikethrough: bool
    user_interface: UiType


_GenericEnum = TypeVar("_GenericEnum", bound=Enum)


def get_first_char_dict(enum: type[_GenericEnum]) -> dict[str, _GenericEnum]:
    """
    Return a dictionary mapping the first letter of each Enum
    item to the corresponding Enum item.
    """
    keys = [item.name for item in enum]
    return dict(zip((key[0] for key in keys), enum))


_FIRST_CHAR_DICT = get_first_char_dict(UiType)


def _get_ui_type(string: str) -> UiType:
    try:
        if len(string) == 1:
            return _FIRST_CHAR_DICT[string.upper()]
        return UiType[string.upper()]
    except KeyError as err:
        msg = f"Invalid UI type: {string}"
        raise ArgumentTypeError(msg) from err


def _get_args() -> TypedNamespace:
    parser = ArgumentParser(
        description="Ndo is a todo list program to "
        "help you manage your todo lists",
        add_help=False,
        formatter_class=RawDescriptionHelpFormatter,
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "filename",
        type=str,
        nargs="?",
        default=_DEFAULT_FILENAME,
        help=f"Provide a filename to store the todo list in.\
            Default is `{_DEFAULT_FILENAME}`.",
    )
    parser.add_argument(
        "--bullet-display",
        "-b",
        action="store_true",
        default=_DEFAULT_BULLETS,
        help=f"Boolean: determine if Todos are displayed with\
            a bullet point rather than a checkbox.\
            Default is `{_DEFAULT_BULLETS}`.",
    )
    parser.add_argument(
        "--enumerate",
        "-e",
        action="store_true",
        default=_DEFAULT_ENUMERATE,
        help=f"Boolean: determines if todos are numbered when\
            printed or not. Default is `{_DEFAULT_ENUMERATE}`.",
    )
    parser.add_argument(
        "--user-interface",
        "--ui",
        "-g",
        type=_get_ui_type,
        choices=list(UiType),
        default=_DEFAULT_UI,
        help=f"UiType: determine how todos should be rendered.\
            Default is `{_DEFAULT_UI}`. If `none` is passed,\
            print state of a todolist to stdout without a user\
            interface.",
    )
    parser.add_argument(
        "--help",
        "-h",
        action="help",
        help="Show this help message and exit.",
    )
    parser.add_argument(
        "--help-file",
        type=str,
        default=_DEFAULT_HELP_FILE,
        metavar="FILE",
        help=f"Allows passing alternate file to\
        specify help menu. Default is `{_DEFAULT_HELP_FILE}`.",
    )
    parser.add_argument(
        "--indentation-level",
        "-i",
        type=int,
        default=_DEFAULT_INDENT,
        metavar="LEVEL",
        help=f"Allows specification of indentation level. \
            Default is `{_DEFAULT_INDENT}`.",
    )
    parser.add_argument(
        "--relative-enumeration",
        "-r",
        action="store_true",
        default=_DEFAULT_RELATIVE_ENUMERATE,
        help=f"Boolean: determines if todos are numbered\
            when printed. Numbers relatively rather than\
            absolutely. Default is `{_DEFAULT_RELATIVE_ENUMERATE}`.",
    )
    parser.add_argument(
        "--rename",
        "-n",
        action="store_true",
        default=_DEFAULT_RENAME,
        help=f"Boolean: if true, show prompt to rename\
            file, rename file to input, and exit. Default\
            is `{_DEFAULT_RENAME}`.",
    )
    parser.add_argument(
        "--simple-boxes",
        "-x",
        action="store_true",
        default=_DEFAULT_SIMPLE_BOXES,
        help=f"Boolean: allow rendering simpler checkboxes if\
            terminal doesn't support default ascii checkboxes.\
            Default is `{_DEFAULT_SIMPLE_BOXES}`.",
    )
    parser.add_argument(
        "--strikethrough",
        "-s",
        action="store_true",
        default=_DEFAULT_STRIKETHROUGH,
        help=f"Boolean: strikethrough completed todos\
            - option to disable because some terminals\
            don't support strikethroughs. Default is\
            `{_DEFAULT_STRIKETHROUGH}`.",
    )
    parser.add_argument(
        "--title",
        "-t",
        nargs="+",
        default=_DEFAULT_HEADER,
        help="Allows passing alternate header.\
            Default is filename.",
    )
    extra_args: list[str] = []
    if (Path.home() / _CONFIG_FILE_NAME).exists():
        extra_args.append(f"@{Path.home() / _CONFIG_FILE_NAME}")
    if Path(_CONFIG_FILE_NAME).exists():
        extra_args.append(f"@{_CONFIG_FILE_NAME}")
    return parser.parse_args(
        [*extra_args, *argv[1:]],
        namespace=TypedNamespace(),
    )


def _parse_filename(filename: str) -> Path:
    path = Path(filename)
    if path.is_dir():
        return path.joinpath(_DEFAULT_FILENAME)
    return path


def _get_header(title: list[str]) -> str:
    if title != _DEFAULT_HEADER:
        return " ".join(title)
    if FILENAME.exists():
        with FILENAME.open(encoding="utf-8") as file:
            if file.read(2) == "# ":
                return file.readline().strip("\n")
    return FILENAME.as_posix()


def _fail_if_not_implemented() -> None:
    if STRIKETHROUGH and UI_TYPE == UiType.CURSES:
        msg = (
            "Curses UI doesn't fully support strikethrough. "
            "Try running either in acurses mode or without strikethrough. "
            "(`-sga` or `-gc`)"
        )
        raise NotImplementedError(msg)


command_line_args = _get_args()
BULLETS: bool = command_line_args.bullet_display
CHECKBOX: str = (
    _CHECKBOX_OPTIONS[1] if not command_line_args.simple_boxes else ""
)
ENUMERATE: bool = command_line_args.enumerate
FILENAME: Path = _parse_filename(command_line_args.filename)
HEADER: str = _get_header(command_line_args.title)
HELP_FILE: Path = Path(command_line_args.help_file)
INDENT: int = command_line_args.indentation_level
RELATIVE_ENUMERATE: bool = command_line_args.relative_enumeration
RENAME: bool = command_line_args.rename
SIMPLE_BOXES: bool = command_line_args.simple_boxes
STRIKETHROUGH: bool = command_line_args.strikethrough
UI_TYPE: UiType = command_line_args.user_interface
_fail_if_not_implemented()
del command_line_args


if UI_TYPE == UiType.ANSI:
    import ndo.acurses as curses
    from ndo.acurses import wrapper
elif UI_TYPE == UiType.TKINTER:
    import ndo.tcurses as curses
    from ndo.tcurses import wrapper
else:
    import curses

    from ndo.working_initscr import wrapper

curses_module: ModuleType = curses
wrapper_func = wrapper
