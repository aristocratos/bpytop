from bpytop import Term
import os
from unittest import mock


def test_empty():
    assert Term.title() == "\033]0;\a"


def test_nonempty():
    assert Term.title("BpyTOP") == "\033]0;BpyTOP\a"


def test_empty_with_environ():
    with mock.patch.dict("os.environ", {"TERMINAL_TITLE": "hello"}, clear=True):
        assert Term.title() == "\033]0;hello\a"


def test_nonempty_with_environ():
    with mock.patch.dict("os.environ", {"TERMINAL_TITLE": "hello"}, clear=True):
        assert Term.title("BpyTOP") == "\033]0;hello BpyTOP\a"
