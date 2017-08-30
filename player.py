import threading
import time
import sys

import pygame
import pygame.midi
from pygame.locals import *

pygame.init()
pygame.midi.init()
midi_out = pygame.midi.Output(3, 0)
pygame.fastevent.init()
event_get = pygame.fastevent.get
event_post = pygame.fastevent.post
midi_in = pygame.midi.Input(1)
pygame.display.set_mode((100, 100))

from chords import *
from easylogging import *
from markov import *

MAX_STATES = 64
START_NOTE = 72


def print_device_info():
    for i in range(pygame.midi.get_count()):
        r = pygame.midi.get_device_info(i)
        (interf, name, input, output, opened) = r

        in_out = ""
        if input:
            in_out = "(input)"
        if output:
            in_out = "(output)"

        print("%2i: interface :%s:, name :%s:, opened :%s:  %s" %
              (i, interf, name, opened, in_out))


def play_note(note, velocity, on, delay):
    time.sleep(delay)
    if on:
        midi_out.note_on(note, velocity)
    else:
        midi_out.note_off(note, velocity)


def play_notes(notes, delay=0):
    """
    Array of notes:
    [(pitch, velocity, channel, on)]
    """
    ts = []
    num_notes_to_play = 0
    for i, note in enumerate(notes):
        ts.append(threading.Thread(target=play_note, args=(
            note[0], note[1], note[3], delay,)))
        if note[3]:
            num_notes_to_play += 1
    for t in ts:
        t.start()

    return num_notes_to_play > 0


print_device_info()


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
        self.states = []
        self.state = ['0'] * MAX_STATES
        self.plays = []  # an array of integers to play when the time comes
        self.queue = {}
        self.beat_num = 0
        self.tick = -1
        self.initial_tick = -1
        self.bpm = bpm
        self.silence = 0

    def start(self):
        self.t1 = threading.Thread(target=self.metronome)
        self.t1.start()
        self.t2 = threading.Thread(target=self.midi_listen)
        self.t2.start()
        self.initial_tick = self.tick

    def dump_states(self):
        logger.info("Dumping {} states".format(len(self.states)))
        with open('states.json', 'w') as f:
            f.write(json.dumps(self.states))

    def load_states(self, fname):
        self.plays = json.load(open(fname, 'r'))

    def play_preset(self):
        if self.tick >= len(self.plays) or self.tick == 0:
            return
        state_current = list("{:b}".format(
            self.plays[self.tick]).zfill(MAX_STATES))
        state_previous = list("{:b}".format(
            self.plays[self.tick - 1]).zfill(MAX_STATES))
        notes = []
        for i, s in enumerate(state_current):
            if s == state_previous[i]:
                continue
            notes.append((i + START_NOTE, 75, 0, s == "1"))
        if len(notes) > 0:
            logger.debug("Playing preset notes")
            play_notes(notes)

    def response(self, absolute_beat):
        """Emits midi notes
        if the conditions are right
        """
        self._generate_reply()
        notes = []
        if absolute_beat in self.queue:
            notes = self.queue[absolute_beat]
        return notes

    def add_note(self, pitch, velocity, channel, on):
        """Tell the player which notes are played when
        """
        measure_beat = self.tick % self.beats_per_measure
        self.notes.insert(0,
                          (self.tick, measure_beat, pitch, velocity, channel, on))
        if pitch >= START_NOTE and pitch < START_NOTE + MAX_STATES:
            note_index = pitch - START_NOTE
            if on:
                self.state[note_index] = "1"
                self.silence = 0
            else:
                self.state[note_index] = "0"
        if pitch == 21 and on:
            self.dump_states()
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
            self.tick_tock()

    def tick_tock(self):
        self.tick += 1
        self.beat_num = self.tick % 16
        self.states.append(int(''.join(self.state), 2))
        if self.tick % 16 == 0:
            # half note
            pass
        if (self.tick % 16) % 4 == 0:
            # quarter note
            logger.info(self.beat_num)
            # play_notes([(36, 20, 0, True)])
        elif (self.tick % 16) % 2 == 0:
            # eighth note
            pass
            # play_notes([(36, 20, 0, False)])
        elif (self.tick % 16) % 1 == 0:
            # sixteenth note
            pass
        notes = self.response(self.tick)
        if len(notes) > 0:
            logger.info("tick {}: {}".format(self.tick, notes))
        # Play any response notes
        play_notes(notes)
        # Play any preset notes
        self.play_preset()
        self._generate_reply()
        logger.info('silence: {}'.format(self.silence))
        self.silence += 1
        time.sleep(60 / self.bpm / 4 * 0.9975)

    def midi_listen(self):
        print("Starting midi listen")
        going = True
        while going:
            events = event_get()
            for e in events:
                print(e)
                if e.type in [QUIT]:
                    print("GOT QUIT")
                    sys.exit(1)
                    going = False
                if e.type in [KEYDOWN]:
                    print("GOT KEYDOWN")
                    going = False
                if e.type in [pygame.midi.MIDIIN]:
                    note = e.data1
                    velocity = e.data2
                    on = e.data2 > 0
                    logger.info('human {} {} {}'.format(note, velocity, on))
                    self.add_note(note, velocity, 0, on)

            if midi_in.poll():
                midi_events = midi_in.read(10)
                # convert them into pygame events.
                midi_evs = pygame.midi.midis2events(
                    midi_events, midi_in.device_id)

                for m_e in midi_evs:
                    event_post(m_e)


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
            self._queue_note(absolute_beat + self.delay,
                             pitch, int(velocity * .8), channel, True)
            self._queue_note(absolute_beat + self.delay + self.delay,
                             pitch, int(velocity * .6), channel, True)
            self._queue_note(absolute_beat + self.delay * 2 + self.length,
                             pitch, velocity, channel, False)


class LastChord(PlayerPiano):
    """LastChord uses last
    2 beats of notes to figure out chord and play it back"""

    def _generate_reply(self):
        current_absolute = -1
        current_beat = -1
        measure_half = -1
        pitches = []
        velocities = []
        for t in self.notes:
            (absolute_beat, measure_beat, pitch, velocity, channel, on) = t
            if not on:
                continue
            if current_beat == -1:
                current_absolute = absolute_beat
                current_beat = measure_beat
                measure_half = measure_beat - self.beats_per_measure / 2 > 0
            if measure_beat != current_beat and measure_half != (measure_beat - self.beats_per_measure / 2 > 0):
                break
            pitches.append(pitch)
            velocities.append(velocity)
        if len(set(pitches)) < 3:
            return
        start = random.randint(0, 4)
        end = random.randint(4, 16) + start
        for i in range(current_absolute + start, current_absolute + end):
            if i in self.queue:
                return
        notes = []
        for pitch in sorted(pitches):
            notes.append(midi_to_note(pitch))
        chord = notes_to_chord(notes, key=self.key)
        notes_in_chord = chord_to_notes(chord, voicing=True)
        midi_notes = get_midi_notes(notes_in_chord, register=4)
        did_queue = False
        velocities = list(sorted(velocities))
        mean_velocity = int(float(velocities[int(len(velocities) / 2)]) * .7)
        for note in midi_notes:
            did_queue = self._queue_note(
                current_absolute + start, note, int(mean_velocity), 0, True)
            self._queue_note(current_absolute + end, note,
                             mean_velocity, 0, False)
        if did_queue:
            if measure_half:
                logger.info('2: {} => {}'.format(notes, chord))
            else:
                logger.info('1: {} => {}'.format(notes, chord))


class Markov(PlayerPiano):

    def _generate_reply(self):
        if len(set(self.states)) > 10 and self.silence % 32 == 0 and self.silence > 0 and self.tick > self.initial_tick + 128:
            logger.info('Generating song')
            song = markov_song(self.states)
            self.plays = self.states + song[:32]


# c = Markov('C', bpm=360)
# c.load_states('states.json')
# c.states = c.plays
# c.init()
# c.tick = len(c.states)
# c.start()


# random.seed(1)
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


c = Echo('C', bpm=240)
c.init()
c.start()
