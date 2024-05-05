"""Command line argument parser for Ndo"""

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from enum import Enum
from pathlib import Path

from src.md_to_py import md_table_to_lines

CONTROLS_BEGIN_INDEX: int = 69
CONTROLS_END_INDEX: int = 99

_DEFAULT_BULLETS: bool = False
_DEFAULT_ENUMERATE: bool = False
_DEFAULT_FILENAME: Path = Path("todo.txt")
_DEFAULT_HEADER: list[str] = [""]
_DEFAULT_HELP_FILE: Path = Path(__file__).parent.parent.joinpath("README.md").absolute()
_DEFAULT_INDENT: int = 2
_DEFAULT_RELATIVE_ENUMERATE: bool = False
_DEFAULT_SIMPLE_BOXES: bool = False
_DEFAULT_STRIKETHROUGH: bool = False

_CHECKBOX_OPTIONS = ("🗹", "☑")


class GuiType(Enum):
    """Specifiy a GUI type, (curses default tui, ansi custom tui, tkinter gui)"""

    CURSES = "curses"
    ANSI = "ansi"
    TKINTER = "tkinter"
    NONE = "none"

    def __str__(self) -> str:
        return self.value


_DEFAULT_GUI = GuiType.ANSI


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
    simple_boxes: bool
    strikethrough: bool
    gui: GuiType


def _get_args() -> TypedNamespace:
    parser = ArgumentParser(
        description="Ndo is a todo list program to help you manage your todo lists",
        add_help=False,
        formatter_class=RawDescriptionHelpFormatter,
        epilog="Controls:\n  "
        + "\n  ".join(
            md_table_to_lines(
                CONTROLS_BEGIN_INDEX,
                CONTROLS_END_INDEX,
                str(_DEFAULT_HELP_FILE),
                frozenset({"<kbd>", "</kbd>"}),
            ),
        ),
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
        help=f"Boolean: determine if Notes are displayed with\
            a bullet point in front or not. Default is `{_DEFAULT_BULLETS}`.",
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
        "--gui",
        "-g",
        type=GuiType,
        choices=list(GuiType),
        default=_DEFAULT_GUI,
        help=f"GuiType: determine how todos should be rendered.\
            Default is `{_DEFAULT_GUI}`. If `none` is passed,\
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
        help=f"Allows passing alternate file to\
        specify help menu. Default is `{_DEFAULT_HELP_FILE}`.",
    )
    parser.add_argument(
        "--indentation-level",
        "-i",
        type=int,
        default=_DEFAULT_INDENT,
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
    return parser.parse_args(namespace=TypedNamespace())


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


command_line_args = _get_args()
BULLETS: bool = command_line_args.bullet_display
CHECKBOX: str = _CHECKBOX_OPTIONS[1] if not command_line_args.simple_boxes else ""
ENUMERATE: bool = command_line_args.enumerate
FILENAME: Path = _parse_filename(command_line_args.filename)
HEADER: str = _get_header(command_line_args.title)
HELP_FILE: Path = Path(command_line_args.help_file)
INDENT: int = command_line_args.indentation_level
RELATIVE_ENUMERATE: bool = command_line_args.relative_enumeration
SIMPLE_BOXES: bool = command_line_args.simple_boxes
STRIKETHROUGH: bool = command_line_args.strikethrough
GUI_TYPE: GuiType = command_line_args.gui
del command_line_args
