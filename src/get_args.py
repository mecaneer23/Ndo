# pylint: disable=global-statement, missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from curses import wrapper
from pathlib import Path
from typing import Any

from src.md_to_py import md_table_to_lines

BULLETS = False
CHECKBOX = ""
CONTROLS_BEGIN_INDEX = 67
CONTROLS_END_INDEX = 91
DEFAULT_TODO = "todo.txt"
ENUMERATE = False
FILENAME = Path(DEFAULT_TODO)
HEADER = ""
HELP_FILE = Path(__file__).parent.parent.joinpath("README.md").absolute()
INDENT = 2
NO_GUI = False
RELATIVE_ENUMERATE = False
SIMPLE_BOXES = False
STRIKETHROUGH = False

CHECKBOX_OPTIONS = ("🗹", "☑")


def _get_checkbox(win: Any) -> str:
    try:
        win.addch(0, 0, CHECKBOX_OPTIONS[0])
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
                str(HELP_FILE),
                ("<kbd>", "</kbd>"),
            )
        ),
    )
    parser.add_argument(
        "filename",
        type=str,
        nargs="?",
        default=FILENAME,
        help=f"Provide a filename to store the todo list in.\
            Default is `{FILENAME}`.",
    )
    parser.add_argument(
        "--bullet-display",
        "-b",
        action="store_true",
        default=BULLETS,
        help=f"Boolean: determine if Notes are displayed with\
            a bullet point in front or not. Default is `{BULLETS}`.",
    )
    parser.add_argument(
        "--enumerate",
        "-e",
        action="store_true",
        default=ENUMERATE,
        help=f"Boolean: determines if todos are numbered when\
            printed or not. Default is `{ENUMERATE}`.",
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
        default=HELP_FILE,
        help=f"Allows passing alternate file to\
        specify help menu. Default is `{HELP_FILE}`.",
    )
    parser.add_argument(
        "--indentation-level",
        "-i",
        type=int,
        default=INDENT,
        help=f"Allows specification of indentation level. \
            Default is `{INDENT}`.",
    )
    parser.add_argument(
        "--no-gui",
        "-n",
        action="store_true",
        default=NO_GUI,
        help=f"Boolean: If true, do not start a curses gui,\
            rather, just print out the todo list. Default is\
            `{NO_GUI}`.",
    )
    parser.add_argument(
        "--relative-enumeration",
        "-r",
        action="store_true",
        default=RELATIVE_ENUMERATE,
        help=f"Boolean: determines if todos are numbered\
            when printed. Numbers relatively rather than\
            absolutely. Default is `{RELATIVE_ENUMERATE}`.",
    )
    parser.add_argument(
        "--simple-boxes",
        "-x",
        action="store_true",
        default=SIMPLE_BOXES,
        help=f"Boolean: allow rendering simpler checkboxes if\
            terminal doesn't support default ascii checkboxes.\
            Default is `{SIMPLE_BOXES}`.",
    )
    parser.add_argument(
        "--strikethrough",
        "-s",
        action="store_true",
        default=STRIKETHROUGH,
        help=f"Boolean: strikethrough completed todos\
            - option to disable because some terminals\
            don't support strikethroughs. Default is\
            `{STRIKETHROUGH}`.",
    )
    parser.add_argument(
        "--title",
        "-t",
        type=str,
        nargs="+",
        default=HEADER,
        help="Allows passing alternate header.\
            Default is filename.",
    )
    args = vars(parser.parse_args())
    args["checkbox"] = wrapper(_get_checkbox) if not args["simple_boxes"] else ""
    return Namespace(**args)


command_line_args = get_args()
BULLETS = command_line_args.bullet_display
CHECKBOX = command_line_args.checkbox
ENUMERATE = command_line_args.enumerate
FILENAME = (
    Path(command_line_args.filename, DEFAULT_TODO)
    if Path(command_line_args.filename).is_dir()
    else Path(command_line_args.filename)
)
HEADER = (
    FILENAME.as_posix()
    if command_line_args.title == HEADER
    else " ".join(command_line_args.title)
)
HELP_FILE = Path(command_line_args.help_file)
INDENT = command_line_args.indentation_level
NO_GUI = command_line_args.no_gui
RELATIVE_ENUMERATE = command_line_args.relative_enumeration
SIMPLE_BOXES = command_line_args.simple_boxes
STRIKETHROUGH = command_line_args.strikethrough
del command_line_args
