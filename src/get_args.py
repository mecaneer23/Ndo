# pylint: disable=missing-docstring

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Any

try:
    from curses import wrapper  # pyright: ignore

    DEFAULT_TKINTER_GUI = False
except ImportError:

    def wrapper(_: Any) -> str:
        return CHECKBOX_OPTIONS[1]

    DEFAULT_TKINTER_GUI = True  # pyright: ignore[reportConstantRedefinition]

from src.md_to_py import md_table_to_lines

DEFAULT_BULLETS: bool = False
CONTROLS_BEGIN_INDEX: int = 68
CONTROLS_END_INDEX: int = 96
DEFAULT_ENUMERATE: bool = False
DEFAULT_FILENAME: Path = Path("todo.txt")
DEFAULT_HEADER: str = ""
DEFAULT_HELP_FILE: Path = Path(__file__).parent.parent.joinpath("README.md").absolute()
DEFAULT_INDENT: int = 2
DEFAULT_NO_GUI: bool = False
DEFAULT_RELATIVE_ENUMERATE: bool = False
DEFAULT_SIMPLE_BOXES: bool = False
DEFAULT_STRIKETHROUGH: bool = False

CHECKBOX_OPTIONS = ("🗹", "☑")


def _get_checkbox(win: Any) -> str:
    try:
        win.addch(0, 0, CHECKBOX_OPTIONS[0])
        win.clear()
        return CHECKBOX_OPTIONS[0]
    except TypeError:
        return CHECKBOX_OPTIONS[1]


def get_args() -> Namespace:
    parser = ArgumentParser(
        description="Ndo is a todo list program to help you manage your todo lists",
        add_help=False,
        formatter_class=RawDescriptionHelpFormatter,
        epilog="Controls:\n  "
        + "\n  ".join(
            md_table_to_lines(
                CONTROLS_BEGIN_INDEX,
                CONTROLS_END_INDEX,
                str(DEFAULT_HELP_FILE),
                ("<kbd>", "</kbd>"),
            )
        ),
    )
    parser.add_argument(
        "filename",
        type=str,
        nargs="?",
        default=DEFAULT_FILENAME,
        help=f"Provide a filename to store the todo list in.\
            Default is `{DEFAULT_FILENAME}`.",
    )
    parser.add_argument(
        "--bullet-display",
        "-b",
        action="store_true",
        default=DEFAULT_BULLETS,
        help=f"Boolean: determine if Notes are displayed with\
            a bullet point in front or not. Default is `{DEFAULT_BULLETS}`.",
    )
    parser.add_argument(
        "--enumerate",
        "-e",
        action="store_true",
        default=DEFAULT_ENUMERATE,
        help=f"Boolean: determines if todos are numbered when\
            printed or not. Default is `{DEFAULT_ENUMERATE}`.",
    )
    parser.add_argument(
        "--tk-gui",
        "-g",
        action="store_true",
        default=DEFAULT_TKINTER_GUI,
        help=f"Boolean: determine if curses (False) or tkinter gui\
            (True) should be used. Default is `{DEFAULT_TKINTER_GUI}`.",
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
        default=DEFAULT_HELP_FILE,
        help=f"Allows passing alternate file to\
        specify help menu. Default is `{DEFAULT_HELP_FILE}`.",
    )
    parser.add_argument(
        "--indentation-level",
        "-i",
        type=int,
        default=DEFAULT_INDENT,
        help=f"Allows specification of indentation level. \
            Default is `{DEFAULT_INDENT}`.",
    )
    parser.add_argument(
        "--no-gui",
        "-n",
        action="store_true",
        default=DEFAULT_NO_GUI,
        help=f"Boolean: If true, do not start a curses gui,\
            rather, just print out the todo list. Default is\
            `{DEFAULT_NO_GUI}`.",
    )
    parser.add_argument(
        "--relative-enumeration",
        "-r",
        action="store_true",
        default=DEFAULT_RELATIVE_ENUMERATE,
        help=f"Boolean: determines if todos are numbered\
            when printed. Numbers relatively rather than\
            absolutely. Default is `{DEFAULT_RELATIVE_ENUMERATE}`.",
    )
    parser.add_argument(
        "--simple-boxes",
        "-x",
        action="store_true",
        default=DEFAULT_SIMPLE_BOXES,
        help=f"Boolean: allow rendering simpler checkboxes if\
            terminal doesn't support default ascii checkboxes.\
            Default is `{DEFAULT_SIMPLE_BOXES}`.",
    )
    parser.add_argument(
        "--strikethrough",
        "-s",
        action="store_true",
        default=DEFAULT_STRIKETHROUGH,
        help=f"Boolean: strikethrough completed todos\
            - option to disable because some terminals\
            don't support strikethroughs. Default is\
            `{DEFAULT_STRIKETHROUGH}`.",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        nargs="+",
        default=DEFAULT_HEADER,
        help="Allows passing alternate header.\
            Default is filename.",
    )
    args = vars(parser.parse_args())
    args["checkbox"] = wrapper(_get_checkbox) if not args["simple_boxes"] else ""
    return Namespace(**args)


def parse_filename(filename: str) -> Path:
    path = Path(filename)
    if path.is_dir():
        return path.joinpath(DEFAULT_FILENAME)
    return path


command_line_args = get_args()
BULLETS: bool = command_line_args.bullet_display
CHECKBOX: str = command_line_args.checkbox
ENUMERATE: bool = command_line_args.enumerate
FILENAME: Path = parse_filename(command_line_args.filename)
HEADER: str = (
    FILENAME.as_posix()
    if command_line_args.title == DEFAULT_HEADER
    else " ".join(command_line_args.title)
)
HELP_FILE: Path = Path(command_line_args.help_file)
INDENT: int = command_line_args.indentation_level
NO_GUI: bool = command_line_args.no_gui
RELATIVE_ENUMERATE: bool = command_line_args.relative_enumeration
SIMPLE_BOXES: bool = command_line_args.simple_boxes
STRIKETHROUGH: bool = command_line_args.strikethrough
TKINTER_GUI: bool = command_line_args.tk_gui
del command_line_args
