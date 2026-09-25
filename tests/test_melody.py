import random
from collections import defaultdict
from itertools import pairwise

import pytest

from chordial.harmony import generate_progression
from chordial.melody import (
    MAX_LEAP,
    MELODY_HIGH,
    MELODY_LOW,
    _weighted_next_pitch,
    chord_tone_candidates,
    generate_melody,
)
from chordial.models import Key
from chordial.moods import load_moods
from chordial.theory import chord_from_roman, scale_midi_notes, scale_pitch_classes

MOODS = load_moods()
SEEDS = range(15)


def make_melody(mood_name, seed, bars=8):
    mood = MOODS[mood_name]
    rng = random.Random(seed)
    key = mood.keys[seed % len(mood.keys)]
    chords = generate_progression(mood, key, bars, rng)
    return mood, key, chords, generate_melody(chords, mood, key, rng)


@pytest.mark.parametrize("mood_name", list(MOODS))
@pytest.mark.parametrize("seed", SEEDS)
def test_melody_rules(mood_name, seed):
    mood, key, chords, melody = make_melody(mood_name, seed)
    scale = set(scale_pitch_classes(Key(key.tonic, mood.scale)))
    assert melody

    for note in melody:
        # Every note is in range and in the melody's scale.
        assert MELODY_LOW <= note.pitch <= MELODY_HIGH
        assert note.pitch % 12 in scale
        # Strong beats (1 and 3) land on a tone of the chord underneath.
        chord = chords[int(note.start // 4)]
        if note.start % 2 == 0:
            assert note.pitch % 12 in chord.pitch_classes, f"{note} over {chord.name}"

    # No leap bigger than a 5th between consecutive notes.
    for a, b in pairwise(melody):
        assert abs(b.pitch - a.pitch) <= MAX_LEAP


@pytest.mark.parametrize("mood_name", list(MOODS))
def test_bars_fill_exactly_with_rests(mood_name):
    mood, _, chords, melody = make_melody(mood_name, 7)
    by_bar = defaultdict(list)
    for note in melody:
        by_bar[int(note.start // 4)].append(note)
    for bar, notes in by_bar.items():
        # Notes never spill into the next bar and never overlap.
        assert notes[-1].end <= (bar + 1) * 4
        for a, b in pairwise(notes):
            assert a.end <= b.start


def test_same_seed_same_melody():
    assert make_melody("happy", 42)[3] == make_melody("happy", 42)[3]
    assert make_melody("happy", 42)[3] != make_melody("happy", 43)[3]


def test_pentatonic_skips_chord_tones_outside_scale():
    # Calm in C: the IV chord is F-A-C, but F isn't in C major pentatonic.
    scale_notes = scale_midi_notes(Key(0, "major_pentatonic"), MELODY_LOW, MELODY_HIGH)
    f_chord = chord_from_roman("IV", Key(0, "major"))
    candidates = chord_tone_candidates(f_chord, scale_notes)
    assert candidates
    assert all(p % 12 in (9, 0) for p in candidates)


def test_next_pitch_prefers_steps():
    rng = random.Random(0)
    picks = [_weighted_next_pitch([60, 62, 67], 60, rng, repeat_weight=0.0) for _ in range(500)]
    assert picks.count(62) > picks.count(67) * 2  # a step beats a leap of a 5th
    assert 60 not in picks  # repeat_weight 0 means never repeat


def test_next_pitch_falls_back_to_nearest():
    assert _weighted_next_pitch([72, 84], 60, random.Random(0), 0.4) == 72


def test_next_pitch_prefers_reachable_target():
    rng = random.Random(0)
    assert _weighted_next_pitch([62, 64, 67], 65, rng, 0.4, frozenset({7})) == 67
    # A target more than a 5th away is ignored rather than forcing a big leap.
    assert _weighted_next_pitch([62, 64, 79], 65, rng, 0.4, frozenset({7})) != 79


@pytest.mark.parametrize("mood_name", list(MOODS))
def test_ends_on_tonic_when_final_chord_contains_it(mood_name):
    for seed in range(40):
        song_bars = 7  # uneven length: the harmony ends on the tonic chord
        _, key, chords, melody = make_melody(mood_name, seed, bars=song_bars)
        assert key.tonic in chords[-1].pitch_classes
        last, before = melody[-1], melody[-2]
        if (
            min(
                abs(p - before.pitch)
                for p in range(MELODY_LOW, MELODY_HIGH + 1)
                if p % 12 == key.tonic
            )
            <= MAX_LEAP
        ):
            assert last.pitch % 12 == key.tonic
