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
        self.extra_data: str = ""

    def toggle(self) -> None:
        if self.mode == SingleLineMode.ON:
            self.mode = SingleLineMode.OFF
        elif self.mode == SingleLineMode.OFF:
            self.mode = SingleLineMode.ON

    def is_off(self) -> bool:
        return self.mode == SingleLineMode.OFF

    def is_once(self) -> bool:
        return self.mode == SingleLineMode.ONLY_ONCE

    def set_on(self) -> None:
        self.mode = SingleLineMode.ON

    def set_once(self) -> None:
        self.mode = SingleLineMode.ONLY_ONCE

    def get_extra_data(self) -> str:
        return self.extra_data

    def set_extra_data(self, extra_data: str) -> None:
        self.extra_data = extra_data

    def __repr__(self):
        return f"{self.mode} {self.extra_data}"
