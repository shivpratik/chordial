"""Small data types shared by every module.

Time is measured in **beats** (a quarter note = 1 beat in 4/4), not seconds, so the music logic
never depends on tempo. Only ``render.py`` converts beats to seconds.

Pitches come in two forms:

- **pitch class** (0-11): a note name without an octave. C=0, C#=1, D=2 ... B=11.
- **MIDI number**: a note with an octave. 60 = middle C (C4), 64 = E4 (the open high-E string).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Semitone intervals above the root for each chord quality.
# A major triad is root + major 3rd (4 semitones) + perfect 5th (7): C-E-G.
# A minor triad lowers the 3rd by one semitone (3): A-C-E.
CHORD_INTERVALS: dict[str, tuple[int, ...]] = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
}

# How each quality is written after the root in a chord name: C, Am, Bdim, Caug.
CHORD_SUFFIX: dict[str, str] = {"maj": "", "min": "m", "dim": "dim", "aug": "aug"}


@dataclass(frozen=True)
class Note:
    """One melody or chord note. ``start`` and ``duration`` are in beats."""

    pitch: int
    start: float
    duration: float
    velocity: int = 90

    @property
    def end(self) -> float:
        return self.start + self.duration


@dataclass(frozen=True)
class Key:
    """A tonic pitch class plus a scale name, e.g. ``Key(9, "natural_minor")`` = A minor."""

    tonic: int
    mode: str

    @property
    def is_minor(self) -> bool:
        return "minor" in self.mode


@dataclass(frozen=True)
class Chord:
    """A triad. ``root`` is a pitch class; ``name`` is spelled using the key it came from."""

    root: int
    quality: str
    roman: str
    name: str

    @property
    def pitch_classes(self) -> tuple[int, ...]:
        """The chord's notes as pitch classes, e.g. Am -> (9, 0, 4) = A, C, E."""
        return tuple((self.root + i) % 12 for i in CHORD_INTERVALS[self.quality])


@dataclass
class Song:
    """Everything generated for one track.

    ``key`` is the harmony key (chords are built from it); ``scale`` is the scale the melody uses,
    which can differ, e.g. a major pentatonic melody over major-key chords.
    """

    mood: str
    key: Key
    scale: str
    tempo: int
    seed: int
    chords: list[Chord]
    melody: list[Note] = field(default_factory=list)
    beats_per_bar: int = 4

    @property
    def bars(self) -> int:
        return len(self.chords)
