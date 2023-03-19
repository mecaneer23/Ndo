# Ndo - a todo application

A curses implementation of a todo list helper.

## Running

```bash
$ python3 todo.py
```

## Flags

If you want to use the tool for something other than todos, you can rename the header simply by passing an alternative header. For example:

```bash
$ python3 todo.py This is a very cool header
```

## Controls

| Keys                              | Description                |
| --------------------------------- | -------------------------- |
| <kbd>k</kbd>/<kbd>j</kbd>         | Move cursor up and down    |
| <kbd>o</kbd>                      | Add a new todo             |
| <kbd>d</kbd>                      | Remove selected todo       |
| <kbd>q</kbd>, <kbd>Ctrl + c</kbd> | Quit                       |
| <kbd>Enter</kbd>                  | Toggle a todo as completed |
| <kbd>i</kbd>                      | Edit an existing todo      |
