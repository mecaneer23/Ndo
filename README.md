# Ndo - an ncurses todo application

A curses implementation of a todo list helper. Most of the keybindings are similar to vim-bindings so vim users should feel relatively comfortable.

## Running

```bash
python3 todo.py
```

## Flags

If you want to use the tool for something other than todos, you can rename the header simply by passing an alternative header. For example:

```bash
python3 todo.py This is a very cool header
```

## Controls

| Keys                              | Description                 |
| --------------------------------- | --------------------------- |
| <kbd>h</kbd>                      | Show a list of controls     |
| <kbd>k</kbd>/<kbd>j</kbd>         | Move cursor up and down     |
| <kbd>K</kbd>/<kbd>J</kbd>         | Move todo up and down       |
| <kbd>o</kbd>                      | Add a new todo              |
| <kbd>d</kbd>                      | Remove selected todo        |
| <kbd>q</kbd>, <kbd>Ctrl + c</kbd> | Quit                        |
| <kbd>Enter</kbd>                  | Toggle a todo as completed  |
| <kbd>i</kbd>                      | Edit an existing todo       |
| <kbd>g</kbd>/<kbd>G</kbd>         | Jump to top/bottom of todos |
| <kbd>c</kbd>                       | Change selected todo color  |

## Bugs

- For some reason long todos don't render properly in strikethrough mode (in certain terminals)
