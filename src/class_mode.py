# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring


class Mode:
    def __init__(self, toggle_mode: bool) -> None:
        self.toggle_mode = toggle_mode

    def toggle(self) -> None:
        self.toggle_mode = not self.toggle_mode

    def is_not_on(self) -> bool:
        return not self.toggle_mode
