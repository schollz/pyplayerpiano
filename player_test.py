import os.path
import os

import pytest

from player import *


def test_player():
    c = PlayerPiano('G')
    c.add_note(2, 10, 100, 0, True)
    c.add_note(2, 12, 100, 0, True)
    assert [] == c.response(2)


def test_echo():
    c = Echo('G')
    c.init(delay=4)
    c.add_note(2, 10, 100, 0, True)
    c.add_note(2, 12, 100, 0, True)
    assert [] == c.response(2)
    assert [(12, 100, 0, True), (10, 100, 0, True)] == c.response(6)
    assert [(12, 100, 0, False), (10, 100, 0, False)] == c.response(8)


def test_lastchord():
    random.seed(1)
    c = LastChord('G')
    c.add_note(2, 10, 100, 0, True)
    c.add_note(2, 12, 100, 0, True)
    c.add_note(2, 20, 100, 0, True)
    assert [(48, 100, 0, True), (56, 100, 0, True),
            (58, 100, 0, True), (64, 100, 0, True)] == c.response(3)


def test_tick_tock():
    c = PlayerPiano('G')
    c.init()
    c.tick_tock()
    assert c.tick == 0
