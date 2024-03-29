# Ndo - an ncurses todo application

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/746b6de92fed4209aa46905463efd3f4)](https://app.codacy.com/gh/mecaneer23/Ndo/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

A curses implementation of a todo list helper. Most of the keybindings are similar to Vim-bindings so Vim users should feel relatively comfortable.

![Shopping List](res/shopping-list.png)

## OS Support

- Ndo is optimized for Linux, as most Vim users use Linux.
- MacOS is also supported however some keyboard shortcuts use different modifier keys.
- In Windows, general editing is available using the following [external package](#curses-for-windows), although some keyboard shortcuts might not work.

## Setup

### Magnify, copy, and paste

```bash
pip install pyfiglet pyperclip
```

### Curses for Windows

```bash
pip install windows-curses
```

## Running

```bash
python3 todo.py [options] [filename]
```

Or with Docker:

```bash
./docker_build.sh
./docker_run.sh filename
```

## Flags

Positional arguments:

| Argument | Description                                                          |
| -------- | -------------------------------------------------------------------- |
| filename | Provide a filename to store the todo list in. Default is `todo.txt`. |

Options:

| Option                                                      | Description                                                                                                                         |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| --bullet-display, -b                                        | Boolean: determine if Notes are displayed with a bullet point in front or not. Default is `False`.                                  |
| --enumerate, -e                                             | Boolean: determines if todos are numbered when printed or not. Default is `False`.                                                  |
| --tk-gui, -g                                                | Boolean: determine if curses (False) or tkinter gui (True) should be used. Default is `False`.                                      |
| --help, -h                                                  | Show this help message and exit.                                                                                                    |
| --help-file HELP_FILE                                       | Allows passing alternate file to specify help menu. Default is `README.md`.                                                         |
| --indentation-level INDENTATION_LEVEL, -i INDENTATION_LEVEL | Allows specification of indentation level. Default is `2`.                                                                          |
| --no-gui, -n                                                | Boolean: If true, do not start a curses gui, rather, just print out the todo list. Default is `False`.                              |
| --relative-enumeration, -r                                  | Boolean: determines if todos are numbered when printed. Numbers relatively rather than absolutely. Default is `False`.              |
| --simple-boxes, -x                                          | Boolean: allow rendering simpler checkboxes if terminal doesn't support default ascii checkboxes. Default is `False`.               |
| --strikethrough, -s                                         | Boolean: strikethrough completed todos - option to disable because some terminals don't support strikethroughs. Default is `False`. |
| --title TITLE, -t TITLE                                     | Allows passing alternate header. Default is `filename`.                                                                             |

## Controls

| Keys (arranged alphabetically)                                           | Description                         |
| ------------------------------------------------------------------------ | ----------------------------------- |
| <kbd>-</kbd>                                                             | Insert blank line                   |
| <kbd>/</kbd>                                                             | Search for a sequence               |
| <kbd>Alt</kbd>+<kbd>g</kbd>/<kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>g</kbd> | Select all todos above/below        |
| <kbd>Alt</kbd>+<kbd>k</kbd>/<kbd>j</kbd>                                 | Move todo up and down               |
| <kbd>Backspace</kbd>                                                     | Combine with previous todo          |
| <kbd>Ctrl</kbd>+<kbd>a</kbd>                                             | Select all todos                    |
| <kbd>Ctrl</kbd>+<kbd>r</kbd>                                             | Redo change                         |
| <kbd>Ctrl</kbd>+<kbd>x</kbd>, <kbd>k</kbd>                               | Toggle `toggle` and `entry` modes   |
| <kbd>Delete</kbd>                                                        | Toggle between `Todo` and `Note`    |
| <kbd>Enter</kbd>                                                         | Toggle a todo as completed          |
| Numbers                                                                  | Move a number of lines              |
| <kbd>Shift</kbd>+<kbd>k</kbd>/<kbd>j</kbd>                               | Select/deselect multiple todos      |
| <kbd>Shift</kbd>+<kbd>o</kbd>                                            | Add a todo on current line          |
| <kbd>Tab</kbd>/<kbd>Shift</kbd>+<kbd>Tab</kbd>                           | Indent/unindent selected todo       |
| <kbd>a</kbd>                                                             | Display selected todo as an alert   |
| <kbd>b</kbd>                                                             | Make selected todo bigger (magnify) |
| <kbd>c</kbd>                                                             | Change selected todo color          |
| <kbd>d</kbd>                                                             | Remove selected todo                |
| <kbd>g</kbd>/<kbd>Shift</kbd>+<kbd>g</kbd>                               | Jump to top/bottom of todos         |
| <kbd>h</kbd>                                                             | Show a list of controls             |
| <kbd>i</kbd>                                                             | Edit an existing todo               |
| <kbd>k</kbd>/<kbd>j</kbd>                                                | Move cursor up and down             |
| <kbd>o</kbd>                                                             | Add a new todo                      |
| <kbd>p</kbd>                                                             | New todo from clipboard             |
| <kbd>q</kbd>, <kbd>Ctrl</kbd>+<kbd>c</kbd>, <kbd>Esc</kbd>               | Quit                                |
| <kbd>s</kbd>                                                             | Sort top-level todos various ways   |
| <kbd>u</kbd>                                                             | Undo change                         |
| <kbd>y</kbd>                                                             | Copy todo to clipboard              |

## Contributing

Use the following linters and formatters:

### Python files

- pylint
- black
- ruff
- mypy
- vulture

### Markdown files

- markdownlint

## Troubleshooting

### Docker error

`Cannot connect to the Docker daemon at ... Is the Docker daemon running?`

```bash
systemctl start docker
```

## Bugs

- Long todos don't render properly in strikethrough mode (in certain terminals)
- "TypeError: Multiple inheritance with NamedTuple" is not supported when trying to start `Ndo` using python3.10. This can be worked around by removing `Generic[T]` from the `SublistItems` class definition in [src/print_todos.py](src/print_todos.py), however this breaks static type checkers. This change should not be implemented as it is fixed in both earlier and later python versions.
