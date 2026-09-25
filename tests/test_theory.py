import pytest

from chordial.models import Key
from chordial.theory import (
    chord_from_roman,
    chord_quality,
    diatonic_triad,
    key_name,
    midi_to_name,
    note_name,
    parse_key,
    parse_note,
    parse_roman,
    scale_midi_notes,
    scale_pitch_classes,
    transpose_key,
    transpose_pc,
)

C_MAJOR = Key(0, "major")
A_MINOR = Key(9, "natural_minor")


def names(numerals: str, key: Key) -> list[str]:
    return [chord_from_roman(n, key).name for n in numerals.split()]


def spelled_scale(key: Key) -> list[str]:
    return [note_name(pc, key) for pc in scale_pitch_classes(key)]


# --- Notes -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "pc"), [("C", 0), ("C#", 1), ("Db", 1), ("F#", 6), ("Bb", 10), ("B", 11), ("Cb", 11)]
)
def test_parse_note(name, pc):
    assert parse_note(name) == pc


def test_parse_note_rejects_garbage():
    with pytest.raises(ValueError):
        parse_note("H")


def test_midi_to_name():
    assert midi_to_name(60) == "C4"  # middle C
    assert midi_to_name(64) == "E4"  # open high-E string
    assert midi_to_name(40) == "E2"  # open low-E string


def test_transpose_pc_wraps_around_octave():
    assert transpose_pc(11, 2) == 1  # B up a whole step = C#
    assert transpose_pc(0, -1) == 11  # C down a half step = B
    assert transpose_pc(4, 12) == 4  # an octave changes nothing


def test_transpose_key_moves_the_whole_progression():
    d_major = transpose_key(C_MAJOR, 2)
    assert d_major == Key(2, "major")
    assert names("I V vi IV", d_major) == ["D", "A", "Bm", "G"]


# --- Scales ------------------------------------------------------------------------------------


def test_major_and_minor_scales():
    assert spelled_scale(C_MAJOR) == ["C", "D", "E", "F", "G", "A", "B"]
    assert spelled_scale(A_MINOR) == ["A", "B", "C", "D", "E", "F", "G"]


def test_relative_minor_shares_notes_with_major():
    assert set(scale_pitch_classes(A_MINOR)) == set(scale_pitch_classes(C_MAJOR))


def test_harmonic_minor_raises_the_seventh():
    assert spelled_scale(Key(9, "harmonic_minor")) == ["A", "B", "C", "D", "E", "F", "G#"]


def test_pentatonic_drops_fourth_and_seventh():
    assert spelled_scale(Key(7, "major_pentatonic")) == ["G", "A", "B", "D", "E"]
    assert spelled_scale(Key(9, "minor_pentatonic")) == ["A", "C", "D", "E", "G"]


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        (Key(5, "major"), ["F", "G", "A", "Bb", "C", "D", "E"]),  # flats, not A#
        (Key(11, "major"), ["B", "C#", "D#", "E", "F#", "G#", "A#"]),
        (Key(2, "harmonic_minor"), ["D", "E", "F", "G", "A", "Bb", "C#"]),  # C#, not Db
    ],
)
def test_scales_spell_each_letter_once(key, expected):
    assert spelled_scale(key) == expected


def test_scale_midi_notes_in_range():
    assert scale_midi_notes(C_MAJOR, 60, 72) == [60, 62, 64, 65, 67, 69, 71, 72]


def test_unknown_scale():
    with pytest.raises(ValueError, match="Unknown scale"):
        scale_pitch_classes(Key(0, "lydian_bebop"))


# --- Chords ------------------------------------------------------------------------------------


def test_diatonic_triads_of_c_major():
    chords = []
    for degree in range(1, 8):
        root, quality = diatonic_triad(C_MAJOR, degree)
        chords.append((note_name(root, C_MAJOR), quality))
    assert chords == [
        ("C", "maj"),
        ("D", "min"),
        ("E", "min"),
        ("F", "maj"),
        ("G", "maj"),
        ("A", "min"),
        ("B", "dim"),
    ]


def test_chord_quality():
    assert chord_quality((0, 4, 7)) == "maj"
    assert chord_quality((9, 0, 4)) == "min"
    assert chord_quality((11, 2, 5)) == "dim"
    with pytest.raises(ValueError):
        chord_quality((0, 2, 7))  # a sus2 chord, not a triad we know


def test_cannot_stack_thirds_on_pentatonic():
    with pytest.raises(ValueError, match="7-note"):
        diatonic_triad(Key(0, "major_pentatonic"), 1)


def test_chord_pitch_classes():
    am = chord_from_roman("vi", C_MAJOR)
    assert am.pitch_classes == (9, 0, 4)  # A C E


# --- Roman numerals ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("numeral", "expected"),
    [
        ("I", (1, "maj")),
        ("vi", (6, "min")),
        ("IV", (4, "maj")),
        ("vii°", (7, "dim")),
        ("viio", (7, "dim")),
        ("III+", (3, "aug")),
    ],
)
def test_parse_roman(numeral, expected):
    assert parse_roman(numeral) == expected


@pytest.mark.parametrize("bad", ["", "IIII", "Iv", "X", "bVI"])
def test_parse_roman_rejects_invalid(bad):
    with pytest.raises(ValueError):
        parse_roman(bad)


def test_four_chord_progression_in_c_and_g():
    assert names("I V vi IV", C_MAJOR) == ["C", "G", "Am", "F"]
    assert names("I V vi IV", Key(7, "major")) == ["G", "D", "Em", "C"]


def test_melancholic_progression_in_a_minor():
    assert names("i VI III VII", A_MINOR) == ["Am", "F", "C", "G"]


def test_harmonic_minor_makes_v_major():
    assert names("i iv V", Key(9, "harmonic_minor")) == ["Am", "Dm", "E"]


def test_wrong_case_numeral_is_rejected():
    # In natural minor the chord on degree 5 is minor (Em in A minor), so "V" is a mistake.
    with pytest.raises(ValueError, match="expects a maj chord"):
        chord_from_roman("V", A_MINOR)


def test_diminished_numeral():
    assert chord_from_roman("vii°", C_MAJOR).name == "Bdim"


# --- Keys --------------------------------------------------------------------------------------


def test_parse_key():
    assert parse_key("G") == Key(7, "major")
    assert parse_key("Am") == Key(9, "natural_minor")
    assert parse_key("F#m") == Key(6, "natural_minor")
    assert parse_key("Bb") == Key(10, "major")
    with pytest.raises(ValueError):
        parse_key("Amaj7")


def test_key_name():
    assert key_name(Key(7, "major")) == "G major"
    assert key_name(A_MINOR) == "A minor"
    assert key_name(Key(10, "major")) == "Bb major"
    assert key_name(Key(8, "natural_minor")) == "G# minor"
