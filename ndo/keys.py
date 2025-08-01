"""
MIT License (c) 2023-2025
"""

# pylint: disable=invalid-name

from enum import IntEnum


class Key(IntEnum):
    """
    A wrapper to access keys as curses refers to them. Mostly ascii.
    """

    nodelay_escape = -1
    windows_esc_prefix = 0
    ctrl_a = 1
    ctrl_f = 6
    backspace = 8
    tab = 9
    enter = 10
    ctrl_k = 11
    enter_ = 13
    shift = 16
    ctrl = 17
    alt = 18
    ctrl_r = 18
    ctrl_backspace = 23
    ctrl_x = 24
    escape = 27
    space = 32
    double_quote = 34
    single_quote = 39
    comma = 44
    minus = 45
    period = 46
    slash = 47
    zero = 48
    one = 49
    two = 50
    three = 51
    four = 52
    five = 53
    six = 54
    seven = 55
    eight = 56
    nine = 57
    semicolon = 59
    G = 71
    alt_G = 71  # noqa: N815
    J = 74
    alt_J = 74  # noqa: N815
    K = 75
    alt_K = 75  # noqa: N815
    uppercase_O = 79  # noqa: N815
    T = 84
    open_bracket = 91
    backslash = 92
    close_bracket = 93
    underscore = 95
    a = 97
    b = 98
    c = 99
    d = 100
    e = 101
    f = 102
    ctrl_delete = 100
    g = 103
    alt_g = 103
    h = 104
    alt_h = 104
    i = 105
    j = 106
    alt_j = 106
    k = 107
    alt_k = 107
    lowercase_l = 108
    m = 109
    n = 110
    o = 111
    p = 112
    q = 113
    r = 114
    s = 115
    t = 116
    u = 117
    v = 118
    w = 119
    x = 120
    y = 121
    z = 122
    backspace_ = 127
    ctrl_backspace_ = 127
    windows_esc_prefix_ = 224
    down_arrow = 258
    up_arrow = 259
    left_arrow = 260
    right_arrow = 261
    home = 262
    backspace__ = 263
    delete = 330
    page_down = 338
    page_up = 339
    shift_tab_windows = 351
    shift_tab = 353
    end_windows = 358
    end = 360
    shift_delete = 383
    alt_j_windows = 426
    alt_k_windows = 427
    ctrl_left_arrow_windows = 443
    ctrl_right_arrow_windows = 443
    alt_delete_windows = 478
    ctrl_backspace__ = 504
    alt_delete = 522
    ctrl_right_arrow = 565
    ctrl_left_arrow = 550

    def __eq__(self, other: object) -> bool:
        """
        Compare two Key objects.
        """
        if isinstance(other, Key):
            return self.value == other.value
        if isinstance(other, int):
            return self.value == other
        msg = (
            f"Cannot compare Key with {type(other)}. "
            f"Use `Key.{self.name}` or `Key.{self.name}.value`."
        )
        raise NotImplementedError(msg)

    def __hash__(self) -> int:
        return super().__hash__()

    @classmethod
    def _missing_(cls, value: object) -> "Key":
        if not isinstance(value, int):
            msg = f"Key must be an int, not {type(value)}."
            raise TypeError(msg)
        obj = int.__new__(cls, value)
        obj._name_ = chr(value)
        obj._value_ = value
        return obj

    @staticmethod
    def digits() -> tuple["Key", ...]:
        """
        Return a tuple with the ascii value of every digit (0-9).
        """
        return (
            Key.zero,
            Key.one,
            Key.two,
            Key.three,
            Key.four,
            Key.five,
            Key.six,
            Key.seven,
            Key.eight,
            Key.nine,
        )

    @staticmethod
    def normalize_ascii_digit_to_digit(ascii_digit: "int | Key") -> int:
        """
        Take in a Key which represents a digit and
        return the digit it represents.
        """
        if isinstance(ascii_digit, Key):
            ascii_digit = ascii_digit.value
        if Key.zero.value <= ascii_digit <= Key.nine.value:
            return ascii_digit - Key.zero.value
        msg = f"Ascii digit `{ascii_digit}` must represent a digit."
        raise ValueError(msg)
