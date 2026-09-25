"""Music theory basics: notes, scales, chords, Roman numerals and transposition.

Everything here is a pure function with no randomness, which makes it easy to test.

Quick primer:

- An **octave** has 12 semitones. On guitar, one fret = one semitone, so the 12th fret is the
  same note as the open string, one octave higher.
- A **scale** is a pattern of steps from a starting note (the **tonic**). The major scale is
  whole-whole-half-whole-whole-whole-half: C D E F G A B.
- A **triad** is three notes stacked in thirds: pick a scale note, skip one, take the next, skip
  one, take the next. From C in C major: C (skip D) E (skip F) G = a C major chord.
- **Roman numerals** name chords by their position in the scale, so one progression works in any
  key. Upper case = major, lower case = minor: I-V-vi-IV in C = C, G, Am, F; in G = G, D, Em, C.
"""

from __future__ import annotations

import re

from chordial.models import CHORD_INTERVALS, CHORD_SUFFIX, Chord, Key

# --- Notes -------------------------------------------------------------------------------------

LETTERS = "CDEFGAB"
LETTER_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
NOTE_NAMES_SHARP = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
NOTE_NAMES_FLAT = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")

# The usual way to spell each tonic, choosing whichever spelling has the simpler key signature.
# (Db major has 5 flats; C# major would have 7 sharps.)
_MAJOR_TONIC_NAMES = ("C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
_MINOR_TONIC_NAMES = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "G#", "A", "Bb", "B")


def parse_note(name: str) -> int:
    """Return the pitch class of a note name: ``"C"`` -> 0, ``"F#"`` -> 6, ``"Bb"`` -> 10."""
    match = re.fullmatch(r"([A-Ga-g])([#b]*)", name.strip())
    if not match:
        raise ValueError(f"Not a note name: {name!r}")
    letter, accidentals = match.groups()
    return (LETTER_PC[letter.upper()] + accidentals.count("#") - accidentals.count("b")) % 12


def midi_to_name(midi: int, key: Key | None = None) -> str:
    """Name a MIDI note with its octave: 60 -> ``"C4"`` (middle C), 64 -> ``"E4"``."""
    octave = midi // 12 - 1
    return f"{note_name(midi % 12, key)}{octave}"


def transpose_pc(pc: int, semitones: int) -> int:
    """Move a pitch class up or down, wrapping around the octave: B (11) + 2 -> C# (1)."""
    return (pc + semitones) % 12


def transpose_key(key: Key, semitones: int) -> Key:
    """Move a whole key. Capo on fret 2 over C shapes = transposing C major up 2 to D major."""
    return Key(transpose_pc(key.tonic, semitones), key.mode)


# --- Scales ------------------------------------------------------------------------------------

# Semitones above the tonic for each scale.
SCALES: dict[str, tuple[int, ...]] = {
    # W-W-H-W-W-W-H. Bright and settled. C major = all the white keys.
    "major": (0, 2, 4, 5, 7, 9, 11),
    # Same notes as the major scale starting on its 6th degree: A minor = C major's notes from A.
    # The flat 3rd, 6th and 7th give it a sad, reflective sound.
    "natural_minor": (0, 2, 3, 5, 7, 8, 10),
    # Natural minor with a raised 7th (G# in A minor). The gap between the 6th and 7th sounds
    # exotic and tense, and makes the V chord major (E instead of Em), which pulls hard back to i.
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
    # Major scale without the 4th and 7th, the two notes most likely to clash. Hard to play a
    # "wrong" note, which is why it sounds calm and open.
    "major_pentatonic": (0, 2, 4, 7, 9),
    # Natural minor without the 2nd and 6th. The classic rock/blues guitar box shape.
    "minor_pentatonic": (0, 3, 5, 7, 10),
}

_MODE_DISPLAY = {
    "major": "major",
    "natural_minor": "minor",
    "harmonic_minor": "harmonic minor",
    "major_pentatonic": "major pentatonic",
    "minor_pentatonic": "minor pentatonic",
}


def scale_intervals(mode: str) -> tuple[int, ...]:
    try:
        return SCALES[mode]
    except KeyError:
        raise ValueError(f"Unknown scale {mode!r}. Known scales: {', '.join(SCALES)}") from None


def scale_pitch_classes(key: Key) -> tuple[int, ...]:
    """The pitch classes of a key's scale, starting from the tonic."""
    return tuple((key.tonic + i) % 12 for i in scale_intervals(key.mode))


def scale_midi_notes(key: Key, low: int, high: int) -> list[int]:
    """Every MIDI note between ``low`` and ``high`` (inclusive) that belongs to the key's scale."""
    pcs = set(scale_pitch_classes(key))
    return [m for m in range(low, high + 1) if m % 12 in pcs]


# --- Spelling ----------------------------------------------------------------------------------


def tonic_name(key: Key) -> str:
    names = _MINOR_TONIC_NAMES if key.is_minor else _MAJOR_TONIC_NAMES
    return names[key.tonic]


def key_name(key: Key) -> str:
    """Human-readable key: ``"G major"``, ``"A minor"``, ``"D harmonic minor"``."""
    return f"{tonic_name(key)} {_MODE_DISPLAY.get(key.mode, key.mode)}"


def _spell_seven_note_scale(key: Key) -> list[str]:
    """Spell a 7-note scale so each letter A-G appears exactly once.

    That's how sheet music spells scales: D harmonic minor is D E F G A Bb C#, never "Db", because
    the 7th degree must use the letter C.
    """
    tonic = tonic_name(key)
    start = LETTERS.index(tonic[0])
    names = []
    for i, interval in enumerate(scale_intervals(key.mode)):
        letter = LETTERS[(start + i) % 7]
        target = (key.tonic + interval) % 12
        offset = (target - LETTER_PC[letter]) % 12
        if offset > 6:
            offset -= 12
        names.append(letter + ("#" * offset if offset > 0 else "b" * -offset))
    return names


def _reference_mode(key: Key) -> str:
    """A 7-note scale to spell notes with. Pentatonic scales borrow from their parent scale."""
    if len(scale_intervals(key.mode)) == 7:
        return key.mode
    return "natural_minor" if key.is_minor else "major"


def note_name(pc: int, key: Key | None = None) -> str:
    """Name a pitch class, spelled to suit the key (Bb in F major, A# in B major).

    With no key, sharps are used.
    """
    if key is None:
        return NOTE_NAMES_SHARP[pc % 12]
    ref = Key(key.tonic, _reference_mode(key))
    spelled = _spell_seven_note_scale(ref)
    for name in spelled:
        if parse_note(name) == pc % 12:
            return name
    # A note outside the scale: follow the key's general direction (sharps or flats).
    uses_flats = any(n.endswith("b") for n in spelled)
    return (NOTE_NAMES_FLAT if uses_flats else NOTE_NAMES_SHARP)[pc % 12]


# --- Chords ------------------------------------------------------------------------------------


def chord_quality(pitch_classes: tuple[int, ...]) -> str:
    """Identify a triad from its root, third and fifth: (0, 4, 7) above the root = major."""
    root = pitch_classes[0]
    intervals = tuple((pc - root) % 12 for pc in pitch_classes)
    for quality, pattern in CHORD_INTERVALS.items():
        if intervals == pattern:
            return quality
    raise ValueError(f"Not a known triad: intervals {intervals}")


def diatonic_triad(key: Key, degree: int) -> tuple[int, str]:
    """Build the triad on a scale degree (1-7) by stacking thirds. Returns ``(root, quality)``.

    Stacking thirds = take every other scale note. In C major, degree 6 is A, C, E = Am.
    """
    pcs = scale_pitch_classes(key)
    if len(pcs) != 7:
        raise ValueError(
            f"Can't stack thirds on {key.mode!r} ({len(pcs)} notes); use a 7-note harmony scale"
        )
    if not 1 <= degree <= 7:
        raise ValueError(f"Scale degree must be 1-7, got {degree}")
    i = degree - 1
    triad = (pcs[i], pcs[(i + 2) % 7], pcs[(i + 4) % 7])
    return triad[0], chord_quality(triad)


_ROMAN_DEGREES = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7}


def parse_roman(numeral: str) -> tuple[int, str]:
    """Parse a Roman numeral into ``(degree, expected_quality)``.

    Upper case = major (``V``), lower case = minor (``vi``), a trailing ``°`` or ``o`` = diminished
    (``vii°``), a trailing ``+`` = augmented (``III+``).
    """
    match = re.fullmatch(r"(I{1,3}|IV|VI{0,2}|i{1,3}|iv|vi{0,2})([°o+]?)", numeral.strip())
    if not match:
        raise ValueError(f"Not a Roman numeral chord: {numeral!r}")
    body, marker = match.groups()
    degree = _ROMAN_DEGREES[body.lower()]
    if marker in ("°", "o"):
        quality = "dim"
    elif marker == "+":
        quality = "aug"
    else:
        quality = "maj" if body.isupper() else "min"
    return degree, quality


def chord_from_roman(numeral: str, key: Key) -> Chord:
    """Build the chord a Roman numeral names in a key, checking the numeral's case is right.

    >>> chord_from_roman("vi", Key(0, "major")).name
    'Am'

    The check catches mistakes: ``V`` in A natural minor raises an error, because stacking thirds
    on E gives E-G-B = Em (``v``). Use harmonic minor if you want the major V (E-G#-B).
    """
    degree, expected = parse_roman(numeral)
    root, quality = diatonic_triad(key, degree)
    if quality != expected:
        raise ValueError(
            f"{numeral!r} expects a {expected} chord, but degree {degree} of {key_name(key)} is "
            f"{note_name(root, key)}{CHORD_SUFFIX[quality]} ({quality})"
        )
    return Chord(
        root=root,
        quality=quality,
        roman=numeral,
        name=note_name(root, key) + CHORD_SUFFIX[quality],
    )


def parse_key(name: str) -> Key:
    """Parse a key like ``"G"`` (G major) or ``"Am"`` / ``"F#m"`` (A / F# natural minor)."""
    match = re.fullmatch(r"([A-Ga-g][#b]?)(m?)", name.strip())
    if not match:
        raise ValueError(f"Not a key name: {name!r} (examples: C, G, Am, F#m)")
    tonic, minor = match.groups()
    return Key(parse_note(tonic), "natural_minor" if minor else "major")
