"""Chord progression generation: the harmony layer, generated first so the melody can follow it."""

from __future__ import annotations

import random

from chordial.models import Chord, Key
from chordial.moods import Mood
from chordial.theory import chord_from_roman, diatonic_triad


def choose_key(mood: Mood, rng: random.Random) -> Key:
    return rng.choice(mood.keys)


def choose_tempo(mood: Mood, rng: random.Random) -> int:
    low, high = mood.tempo
    return rng.randint(low, high)


def tonic_numeral(key: Key) -> str:
    """The Roman numeral for the home chord: ``I`` in major keys, ``i`` in minor keys."""
    _, quality = diatonic_triad(key, 1)
    return "I" if quality == "maj" else "i"


def generate_progression(mood: Mood, key: Key, bars: int, rng: random.Random) -> list[Chord]:
    """Pick one of the mood's progressions and repeat it to fill ``bars``, one chord per bar.

    If the progression doesn't divide evenly into the number of bars, the last bar is replaced
    with the tonic chord. Ending on "home" is called a **cadence**. It makes the song sound
    finished rather than cut off mid-phrase.
    """
    if bars < 1:
        raise ValueError(f"bars must be at least 1, got {bars}")
    weights = [p.weight for p in mood.progressions]
    progression = rng.choices(mood.progressions, weights=weights)[0].numerals

    numerals = [progression[i % len(progression)] for i in range(bars)]
    if bars % len(progression) != 0:
        numerals[-1] = tonic_numeral(key)
    return [chord_from_roman(n, key) for n in numerals]
