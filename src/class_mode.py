"""
Helpers to handle switching mode between one line
at a time and multiple lines at a time.
"""

from enum import Enum


class SingleLineMode(Enum):
    """
    Enum for mode

    OFF:
        multiple line mode

    ON:
        the default - one line at a time

    NONE:
        non-nullable None type

    ONLY_ONCE:
        represent a state which turns SingleLineMode off for just one line

    """

    OFF = 0
    ON = 1
    NONE = 2
    ONLY_ONCE = 3


class SingleLineModeImpl:
    """Implementation and helper methods for SingleLineMode"""

    def __init__(self, mode: "SingleLineMode") -> None:
        self.mode: SingleLineMode = mode
        self.extra_data: str = ""

    def toggle(self) -> None:
        """Toggle between ON and OFF"""
        if self.mode == SingleLineMode.ON:
            self.mode = SingleLineMode.OFF
        elif self.mode == SingleLineMode.OFF:
            self.mode = SingleLineMode.ON

    def is_off(self) -> bool:
        """Return if mode is OFF"""
        return self.mode == SingleLineMode.OFF

    def is_once(self) -> bool:
        """Return if mode is ONLY_ONCE"""
        return self.mode == SingleLineMode.ONLY_ONCE

    def set_on(self) -> None:
        """Set mode to ON"""
        self.mode = SingleLineMode.ON

    def set_once(self) -> None:
        """Set mode to ONLY_ONCE"""
        self.mode = SingleLineMode.ONLY_ONCE

    def get_extra_data(self) -> str:
        """
        Return extra data, which is any string

        `extra_data` allows for linking important
        information to the Mode object - likely
        used for ONLY_ONCE
        """
        return self.extra_data

    def set_extra_data(self, extra_data: str) -> None:
        """
        Set extra data, which is any string

        `extra_data` allows for linking important
        information to the Mode object - likely
        used for ONLY_ONCE
        """
        self.extra_data = extra_data

    def __repr__(self) -> str:
        return f"{self.mode} {self.extra_data}"
