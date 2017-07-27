import os.path
import os

import pytest

from player import *

def test_player():
	c = PlayerPiano('G')
	c.add_note(2,10,100,0,True)
	c.add_note(2,12,100,0,True)
	assert [] == c.response(2)

def test_echo():
	c = Echo('G')
	c.init(delay=4)
	c.add_note(2,10,100,0,True)
	c.add_note(2,12,100,0,True)
	assert [] == c.response(2)
	assert [(12, 100, 0, True), (10, 100, 0, True)] == c.response(6)
	assert [(12, 100, 0, False), (10, 100, 0, False)] == c.response(8)
