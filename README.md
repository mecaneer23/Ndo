# Ndo - an ncurses todo application

A curses implementation of a todo list helper. Most of the keybindings are similar to Vim-bindings so Vim users should feel relatively comfortable.

## OS Support

- Ndo is optimized for Linux, as most Vim users use Linux.
- MacOS is also supported however some keyboard shortcuts use different modifier keys.
- In Windows, general editing is available using the following external package, although some keyboard shortcuts might not work.

```bash
pip install windows-curses
```

## Running

```bash
python3 todo.py [options] [filename]
```

## Flags

Positional arguments:
| Argument | Description                                                          |
| -------- | -------------------------------------------------------------------- |
| filename | Provide a filename to store the todo list in. Default is `todo.txt`. |

Options:
| Option                     | Description                                                                                                     |
| -------------------------- | --------------------------------------------------------------------------------------------------------------- |
| --help, -h                 | Show this help message and exit.                                                                                |
| --autosave, -a             | Boolean: determines if file is saved on every action or only once at the program termination.                   |
| --strikethrough, -s        | Boolean: strikethrough completed todos - option to disable because some terminals don't support strikethroughs. |
| --title TITLE, -t TITLE    | Allows passing alternate header. Default is `TODO`.                                                             |
| --help-file HELP_FILE      | Allows passing alternate file to specify help menu. Default is `README.md`.                                     |

## Controls

| Keys                              | Description                 |
| --------------------------------- | --------------------------- |
| <kbd>h</kbd>                      | Show a list of controls     |
| <kbd>k</kbd>/<kbd>j</kbd>         | Move cursor up and down     |
| <kbd>K</kbd>/<kbd>J</kbd>         | Move todo up and down       |
| <kbd>o</kbd>                      | Add a new todo              |
| <kbd>O</kbd>                      | Add a todo on current line  |
| <kbd>d</kbd>                      | Remove selected todo        |
| <kbd>c</kbd>                      | Change selected todo color  |
| <kbd>i</kbd>                      | Edit an existing todo       |
| <kbd>y</kbd>                      | Copy todo to clipboard      |
| <kbd>p</kbd>                      | New todo from clipboard     |
| <kbd>g</kbd>/<kbd>G</kbd>         | Jump to top/bottom of todos |
| <kbd>u</kbd>                      | Undo change                 |
| <kbd>Ctrl + r</kbd>               | Redo change                 |
| <kbd>-</kbd>                      | Insert blank line           |
| <kbd>q</kbd>, <kbd>Ctrl + c</kbd> | Quit                        |
| <kbd>Enter</kbd>                  | Toggle a todo as completed  |

## Bugs

- Long todos don't render properly in strikethrough mode (in certain terminals)
- Some terminals display the checkbox character weirdly (currently uses two space workaround)
