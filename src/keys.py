"""
MIT License (c) 2023
"""

# most of the key values aren't good variable names out of context,
# so the following line tells Ruff to ignore them
# ruff: noqa: E741


class Key:
    """
    A wrapper to access keys as curses refers to them. Mostly ascii.
    """

    ctrl_a = 1
    backspace = 8
    tab = 9
    enter = 10
    ctrl_k = 11
    enter_ = 13
    ctrl_r = 18
    ctrl_backspace = 23
    ctrl_x = 24
    escape = 27
    minus = 45
    slash = 47
    zero = 48
    one = 49
    ctrl_arrow = 49
    two = 50
    modifier_shift = 50
    three = 51
    modifier_delete = 51
    modifier_alt = 51
    four = 52
    five = 53
    modifier_ctrl = 53
    six = 54
    seven = 55
    eight = 56
    nine = 57
    semi_colon = 59
    right_arrow = 67
    left_arrow = 68
    end = 70
    G = 71
    alt_G = 71
    home = 72
    J = 74
    K = 75
    O = 79
    indent_dedent = 90
    a = 97
    b = 98
    c = 99
    d = 100
    g = 103
    alt_g = 103
    h = 104
    i = 105
    j = 106
    alt_j = 106
    k = 107
    alt_k = 107
    o = 111
    p = 112
    q = 113
    s = 115
    u = 117
    y = 121
    tilde = 126
    backspace_ = 127
    down = 258
    up = 259
    backspace__ = 263
    delete = 330
    shift_tab_windows = 351
    shift_tab = 353
    alt_j_windows = 426
    alt_k_windows = 427

    @staticmethod
    def digits() -> tuple[int, ...]:
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
    def normalize_ascii_digit_to_digit(ascii_digit: int) -> int:
        """
        Take in a Key which represents a digit and
        return the digit it represents.
        """
        if 48 <= ascii_digit <= 57:
            return ascii_digit - 48
        raise ValueError(f"Ascii digit `{ascii_digit}` must represent a digit.")

    class ctrl_c(KeyboardInterrupt):  # pylint: disable=invalid-name
        """
        Wrapper for KeyboardInterrupt
        """
