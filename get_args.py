# pylint: disable=global-statement, missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path

from md_to_py import md_table_to_lines

BULLETS = False
CONTROLS_BEGIN_INDEX = 0
CONTROLS_END_INDEX = 0
DEFAULT_TODO = ""
ENUMERATE = False
FILENAME = Path()
HEADER = ""
HELP_FILE = Path()
INDENT = 0
NO_GUI = False
RELATIVE_ENUMERATE = False
SIMPLE_BOXES = False
STRIKETHROUGH = False


def init(
    bullets,
    controls_begin_index,
    controls_end_index,
    default_todo,
    this_enumerate,
    filename,
    header,
    help_file,
    indent,
    no_gui,
    relative_enumerate,
    simple_boxes,
    strikethrough,
):
    global BULLETS
    global CONTROLS_BEGIN_INDEX
    global CONTROLS_END_INDEX
    global DEFAULT_TODO
    global ENUMERATE
    global FILENAME
    global HEADER
    global HELP_FILE
    global INDENT
    global NO_GUI
    global RELATIVE_ENUMERATE
    global SIMPLE_BOXES
    global STRIKETHROUGH

    BULLETS = bullets
    CONTROLS_BEGIN_INDEX = controls_begin_index
    CONTROLS_END_INDEX = controls_end_index
    DEFAULT_TODO = default_todo
    ENUMERATE = this_enumerate
    FILENAME = filename
    HEADER = header
    HELP_FILE = help_file
    INDENT = indent
    NO_GUI = no_gui
    RELATIVE_ENUMERATE = relative_enumerate
    SIMPLE_BOXES = simple_boxes
    STRIKETHROUGH = strikethrough


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
    return parser.parse_args()
