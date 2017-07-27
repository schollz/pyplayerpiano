import threading
import time

from chords import *
from easylogging import *


class PlayerPiano(object):
    """The summary line for a class docstring should fit on one line.

    If the class has public attributes, they may be documented here
    in an ``Attributes`` section and follow the same formatting as a
    function's ``Args`` section. Alternatively, attributes may be documented
    inline with the attribute's declaration (see __init__ method below).

    Properties created with the ``@property`` decorator should be documented
    in the property's getter method.

    Attributes:
        attr1 (str): Description of `attr1`.
        attr2 (:obj:`int`, optional): Description of `attr2`.

    """
    
    def __init__(self, key, beats_per_measure=16, bpm=60):
        self.key = key
        self.beats_per_measure = beats_per_measure
        self.notes = []
        self.queue = {}
        self.beat_num = 0
        self.tick = -1
        self.bpm = bpm

    def start(self):
        t1 = threading.Thread(target=self.metronome)
        t1.start()

    def response(self, absolute_beat):
        """Emits midi notes
        if the conditions are right
        """
        self._generate_reply()
        notes = []
        if absolute_beat in self.queue:
            notes = self.queue[absolute_beat]
        return notes

    def add_note(self, absolute_beat, pitch, velocity, channel, on):
        """Tell the player which notes are played when
        """
        measure_beat = absolute_beat % self.beats_per_measure
        self.notes.insert(0,
                          (absolute_beat, measure_beat, pitch, velocity, channel, on))
        return True

    def _queue_note(self, absolute_beat, pitch, velocity, channel, on):
        """Add note to queue
        """
        if absolute_beat not in self.queue:
            self.queue[absolute_beat] = []
        note = (pitch, velocity, channel, on)
        if note not in self.queue[absolute_beat]:
            self.queue[absolute_beat].append(note)
            logger.debug('Queued {} @ {}'.format(note, absolute_beat))
            return True
        return False

    def _generate_reply(self):
        pass

    def init(self):
        """And extra initialization for adding parameters
        """
        pass

    def metronome(self):
        while True:
            self.tick += 1
            self.beat_num = self.tick % 16
            if self.tick % 16 == 0:
                # half note
                pass
            if (self.tick % 16) % 4 == 0:
                # quarter note
                logger.info(self.beat_num)
            elif (self.tick % 16) % 2 == 0:
                # eighth note
                pass
            elif (self.tick % 16) % 1 == 0:
                # sixteenth note
                pass
            notes = self.response(self.tick)
            logger.info("tick {}: {}".format(self.tick, notes))
            time.sleep(60 / self.bpm / 4 * 0.9975)


class Echo(PlayerPiano):
    """Echo is a simple player piano, it will
    emit the notes it recieves after X beats"""

    def init(self, delay=2, length=2):
        self.delay = delay
        self.length = length

    def _generate_reply(self):
        current_beat = -1
        for t in self.notes:
            (absolute_beat, measure_beat, pitch, velocity, channel, on) = t
            if not on:
                continue
            if current_beat == -1:
                current_beat = absolute_beat
            if absolute_beat < current_beat:
                break
            self._queue_note(absolute_beat+self.delay,
                             pitch, velocity, channel, True)
            self._queue_note(absolute_beat+self.delay+self.length,
                             pitch, velocity, channel, False)


class LastChord(PlayerPiano):
    """LastChord uses last
    2 beats of notes to figure out chord and play it back"""

    def _generate_reply(self):
        current_absolute = -1
        current_beat = -1
        measure_half = -1
        pitches = []
        for t in self.notes:
            (absolute_beat, measure_beat, pitch, velocity, channel, on) = t
            if not on:
                continue
            if current_beat == -1:
                current_absolute = absolute_beat
                current_beat = measure_beat
                measure_half = measure_beat - self.beats_per_measure/2 > 0
            if measure_beat != current_beat and measure_half != (measure_beat - self.beats_per_measure/2 > 0):
                break
            pitches.append(pitch)
        if len(set(pitches)) < 3:
            return
        notes = []
        for pitch in sorted(pitches):
            notes.append(midi_to_note(pitch))
        chord = notes_to_chord(notes)
        notes_in_chord = chord_to_notes(chord, voicing=True)
        midi_notes = get_midi_notes(notes_in_chord)
        did_queue = False
        for note in midi_notes:
            did_queue = self._queue_note(
                current_absolute+1, note, 100, 0, True)
            self._queue_note(current_absolute+3, note, 100, 0, False)
        if did_queue:
            if measure_half:
                logger.info('2: {} => {}'.format(notes, chord))
            else:
                logger.info('1: {} => {}'.format(notes, chord))

# random.seed(1)
# c = LastChord('G')
# c.init()
# c.start()
# time.sleep(2)
# c.add_note(2, 10, 100, 0, True)
# c.add_note(2, 12, 100, 0, True)
# time.sleep(2)
# c.add_note(4, 24, 100, 0, True)
# time.sleep(1)
# c.add_note(5, 55, 100, 0, True)
# time.sleep(4)
# c.add_note(9, 50, 100, 0, True)
# c.add_note(10, 65, 100, 0, True)
# c.add_note(10, 63, 100, 0, True)
