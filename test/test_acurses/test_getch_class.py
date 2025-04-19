"""
Tests for ndo.acurses._Getch
"""
# ruff: noqa: ANN201, S101
# pylint: disable=missing-function-docstring

import time
from collections.abc import Generator
from contextlib import suppress
from io import StringIO
from queue import Empty

import pytest

from ndo.acurses import _Getch, window  # type: ignore[reportPrivateUsage]

from .test_utils import mock_stdin_input

window._GETCH.destroy()  # type: ignore[reportPrivateUsage]  # noqa: SLF001  # pylint: disable=protected-access


@pytest.fixture(autouse=True)
def cleanup_instance() -> Generator[None, None, None]:
    """
    Automatically clean up the singleton instance before and after each test.
    """
    with suppress(RuntimeError):
        _Getch.destroy()
    yield
    with suppress(RuntimeError):
        _Getch.destroy()


def test_singleton_enforcement() -> None:
    """Test that only one instance of _Getch can be created."""
    _Getch()
    with pytest.raises(
        RuntimeError,
        match="Only one instance of _Getch is allowed.",
    ):
        _ = _Getch()
    _Getch.destroy()


def test_destroy_allows_reinstantiation() -> None:
    """Test that destroying the singleton instance allows reinstantiation."""
    g1 = _Getch()
    _Getch.destroy()
    g2 = _Getch()
    assert g2 is not g1  # New instance after destruction


def test_context_manager_creates_and_destroys() -> None:
    """Test that the context manager works and destroys the instance."""
    with _Getch() as g:
        assert isinstance(g, _Getch)
        assert _Getch._instance is g  # type: ignore[reportPrivateUsage]  # noqa: SLF001  # pylint: disable=protected-access
    assert _Getch._instance is None  # type: ignore[reportPrivateUsage]  # noqa: SLF001  # pylint: disable=protected-access


def test_double_destroy_raises() -> None:
    """Test that destroying an already destroyed instance raises an error."""
    _Getch()
    _Getch.destroy()
    with pytest.raises(RuntimeError, match="No instance of _Getch to destroy."):
        _Getch.destroy()


def test_start_and_is_started(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the 'start' method works and '_started' is set correctly."""
    monkeypatch.setattr("sys.stdin", StringIO("a"))
    with _Getch() as g:
        g.set_blocking(False)
        g.start()
        time.sleep(0.05)
        assert g.is_started()
        with suppress(Empty):
            assert chr(g.get(timeout=0.1)) == "a"


def test_get_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that the 'get' method raises an Empty exception after a timeout."""
    monkeypatch.setattr("sys.stdin", StringIO(""))
    with _Getch() as g:
        g.set_blocking(True)
        g.start()
        with pytest.raises(Empty):
            g.get(timeout=0.1)


def test_set_blocking_and_get_blocking_status() -> None:
    """Test setting and getting the blocking status of the _Getch object."""
    with _Getch() as g:
        assert g.is_blocking() is True
        g.set_blocking(False)
        assert g.is_blocking() is False


def test_initial_state() -> None:
    g = _Getch()
    assert g.is_blocking() is True
    assert g.is_started() is False


def test_set_blocking() -> None:
    g = _Getch()
    g.set_blocking(False)
    assert g.is_blocking() is False
    g.set_blocking(True)
    assert g.is_blocking() is True


def test_start_sets_started_flag() -> None:
    g = _Getch()
    assert not g.is_started()
    g.start()
    time.sleep(0.1)  # Give thread time to spin up
    assert g.is_started()


def test_fill_queue_and_get() -> None:
    data = "abc"
    with mock_stdin_input(data):
        g = _Getch()
        g.set_blocking(False)
        g.start()

        chars: list[int] = []
        start = time.time()
        while time.time() - start < 1.0:
            try:
                c = g.get(timeout=0.05)
                if c not in chars:
                    chars.append(c)
                if len(chars) == len(data):
                    break
            except Empty:
                continue

        result = [chr(c) for c in chars]
        assert result == list(data)


def test_get_with_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", StringIO(""))

    g = _Getch()
    g.set_blocking(True)
    g.start()

    with pytest.raises(Empty):
        g.get(timeout=0.1)
