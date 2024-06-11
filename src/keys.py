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

    nodelay_escape = -1
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
    two = 50
    three = 51
    four = 52
    five = 53
    six = 54
    seven = 55
    eight = 56
    nine = 57
    G = 71
    alt_G = 71
    J = 74
    K = 75
    O = 79
    open_bracket = 91
    close_bracket = 93
    a = 97
    b = 98
    c = 99
    d = 100
    ctrl_delete = 100
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
    backspace_ = 127
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
    end = 360
    shift_delete = 383
    alt_j_windows = 426
    alt_k_windows = 427
    alt_delete = 522
    ctrl_right_arrow = 565
    ctrl_left_arrow = 550

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
