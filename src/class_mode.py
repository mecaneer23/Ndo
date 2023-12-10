# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring, missing-module-docstring

from enum import Enum


class SingleLineMode(Enum):
    OFF = 0
    ON = 1
    NONE = 2
    ONLY_ONCE = 3


class SingleLineModeImpl:
    def __init__(self, mode: "SingleLineMode") -> None:
        self.mode = mode

    def toggle(self) -> None:
        if self.mode == SingleLineMode.ON:
            self.mode = SingleLineMode.OFF
        elif self.mode == SingleLineMode.OFF:
            self.mode = SingleLineMode.ON

    def is_off(self) -> bool:
        return self.mode == SingleLineMode.OFF

    def is_not_none(self) -> bool:
        return self.mode != SingleLineMode.NONE

    def set_on(self) -> None:
        self.mode = SingleLineMode.ON

    def set_off(self) -> None:
        self.mode = SingleLineMode.OFF

    def set_once(self) -> None:
        self.mode = SingleLineMode.ONLY_ONCE
