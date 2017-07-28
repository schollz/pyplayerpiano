import os.path
import os

import pytest

from chords import *


def test_major_scale():
    assert ['G', 'A', 'B', 'C', 'D', 'E', 'F#'] == major_scale('G')


def test_percent_in_key():
    assert 1.0 == percent_in_key(['A', 'C', 'E'], key='C')
    assert 0.75 == percent_in_key(['A', 'C', 'E', 'Bb'], key='C')


def test_notes_to_chord():
    assert "Dm" == notes_to_chord("D F A".split())
    assert "CM" == notes_to_chord("C E G".split())
    assert "C7" == notes_to_chord("C E G Bb".split())
    assert "C7" == notes_to_chord("C G Bb".split())


def test_get_chord():
    assert ['C', 'E', 'G', 'Bb'] == get_chord("1 3 5 7b")
    assert ['C', 'E', 'G', 'Bb', 'D'] == get_chord("1 3 5 7b 9")


def test_generate():
    try:
        os.remove('data/all_chords.json')
    except:
        pass
    generate_all_chords()
    assert os.path.isfile('data/all_chords.json')


def test_get_midi_notes():
    assert [48, 55] == get_midi_notes(['C', 'G'])
    assert [48, 55, 60] == get_midi_notes(['C', 'G', 'C'])
    assert [24, 31, 36] == get_midi_notes(['C', 'G', 'C'], register=2)
    assert [48, 55, 58, 64] == get_midi_notes(['C', 'G', 'Bb', 'E'])


def test_chord_to_notes():
    random.seed(1)
    assert ['C', 'E', 'G', 'Bb'] == chord_to_notes('C7')
    assert ['C', 'G', 'Bb', 'E'] == chord_to_notes('C7', voicing=True)
    assert ['Bb', 'E', 'C', 'G'] == chord_to_notes(
        'C7', voicing=True, preserve_root=False)


def test_midi_value():
    assert midi_to_note(42) == "F#"
