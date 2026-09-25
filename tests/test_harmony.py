import random

import pytest

from chordial.harmony import choose_tempo, generate_progression, tonic_numeral
from chordial.models import Key
from chordial.moods import load_moods
from chordial.theory import scale_pitch_classes

MOODS = load_moods()


@pytest.mark.parametrize("mood_name", list(MOODS))
@pytest.mark.parametrize("bars", [1, 4, 7, 8, 16])
def test_progression_length_and_diatonic(mood_name, bars):
    mood = MOODS[mood_name]
    for key in mood.keys:
        chords = generate_progression(mood, key, bars, random.Random(0))
        assert len(chords) == bars
        in_key = set(scale_pitch_classes(key))
        for chord in chords:
            assert set(chord.pitch_classes) <= in_key, f"{chord.name} not in {key}"


def test_same_seed_same_progression():
    mood = MOODS["happy"]
    key = mood.keys[0]
    first = generate_progression(mood, key, 8, random.Random(42))
    second = generate_progression(mood, key, 8, random.Random(42))
    assert first == second


def test_uneven_length_ends_on_tonic():
    mood = MOODS["melancholic"]  # every progression is 4 chords long
    key = Key(9, "natural_minor")
    for seed in range(20):
        chords = generate_progression(mood, key, 7, random.Random(seed))
        assert chords[-1].name == "Am"
        assert chords[-1].roman == "i"


def test_even_length_repeats_progression():
    mood = MOODS["happy"]
    chords = generate_progression(mood, Key(0, "major"), 8, random.Random(1))
    assert chords[:4] == chords[4:]


def test_tonic_numeral():
    assert tonic_numeral(Key(0, "major")) == "I"
    assert tonic_numeral(Key(9, "harmonic_minor")) == "i"


def test_tempo_in_range():
    mood = MOODS["melancholic"]
    rng = random.Random(3)
    assert all(60 <= choose_tempo(mood, rng) <= 80 for _ in range(50))


def test_zero_bars_rejected():
    with pytest.raises(ValueError):
        generate_progression(MOODS["happy"], Key(0, "major"), 0, random.Random(0))
