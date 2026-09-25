"""Melody generation using chord-tone rules.

The rules, and why they work:

1. **Strong beats (1 and 3) land on chord tones.** The ear checks the melody against the chord
   on strong beats, so matching them sounds "right". Playing the note E over a C chord fits
   because E is in the chord (C-E-G).
2. **Weak beats can use any scale note.** In-between notes (passing tones) add movement and
   resolve on the next strong beat.
3. **Prefer small steps over big leaps.** Singable melodies mostly move to a neighbouring note.
   On guitar that also means less hand movement. Leaps bigger than a 5th are not allowed.
"""

from __future__ import annotations

import random

from chordial.models import Chord, Key, Note
from chordial.moods import Mood
from chordial.theory import scale_midi_notes

# Default melody range: E4 (open high-E string) up to G5 (15th fret, high E). Easy to tab later.
MELODY_LOW = 64
MELODY_HIGH = 79
MAX_LEAP = 7  # semitones: a perfect 5th
STRONG_VELOCITY = 96
WEAK_VELOCITY = 84


def _interval_weight(interval: int, repeat_weight: float) -> float:
    """How attractive a melodic jump of ``interval`` semitones is. Small steps are favoured."""
    if interval == 0:
        return repeat_weight
    if interval <= 2:  # a step: half or whole tone, e.g. C -> D
        return 1.0
    if interval <= 4:  # a third, e.g. C -> E
        return 0.6
    if interval <= MAX_LEAP:  # a 4th or 5th, e.g. C -> G
        return 0.25
    return 0.0


def _weighted_next_pitch(
    candidates: list[int],
    previous: int | None,
    rng: random.Random,
    repeat_weight: float,
    target_pcs: frozenset[int] = frozenset(),
) -> int:
    """Choose the next melody pitch from ``candidates``, weighted towards small intervals.

    With no previous note (the first note), pitches near the middle of the candidates are
    favoured. If ``target_pcs`` is given and one of those notes is within reach, the choice is
    limited to them; the generator uses this to land the final note on the tonic.
    """
    reference = previous if previous is not None else candidates[len(candidates) // 2]
    targets = [p for p in candidates if p % 12 in target_pcs and abs(p - reference) <= MAX_LEAP]
    if targets:
        candidates = targets
    weights = [
        _interval_weight(abs(p - reference), repeat_weight if previous is not None else 1.0)
        for p in candidates
    ]
    if not any(weights):
        # Nothing within a 5th (can happen at the edge of the range): take the closest note.
        return min(candidates, key=lambda p: abs(p - reference))
    return rng.choices(candidates, weights=weights)[0]


def chord_tone_candidates(chord: Chord, scale_notes: list[int]) -> list[int]:
    """Chord tones within the melody's range, keeping only notes that are also in the scale.

    A pentatonic melody over a IV chord is the case that needs this: in C, the IV chord is F-A-C,
    but F isn't in C major pentatonic, so only A and C are used.
    """
    in_scale = [p for p in scale_notes if p % 12 in chord.pitch_classes]
    if in_scale:
        return in_scale
    low, high = scale_notes[0], scale_notes[-1]
    return [p for p in range(low, high + 1) if p % 12 in chord.pitch_classes]


def generate_bar(
    chord: Chord,
    rhythm: tuple[float, ...],
    bar_start: float,
    scale_notes: list[int],
    previous: int | None,
    rng: random.Random,
    repeat_weight: float = 0.4,
    final_pcs: frozenset[int] = frozenset(),
) -> tuple[list[Note], int | None]:
    """Generate one bar of melody over ``chord`` following ``rhythm``.

    Returns the notes and the last pitch played (so the next bar can continue smoothly).
    ``final_pcs`` is only set for the last bar of the song, to steer its last note home.
    """
    notes = []
    position = 0.0
    sounding = [d for d in rhythm if d > 0]
    for duration in rhythm:
        if duration < 0:  # a rest: time passes, nothing plays
            position += -duration
            continue
        strong = position % 2 == 0  # beats 1 and 3 in 4/4 (positions 0 and 2)
        candidates = chord_tone_candidates(chord, scale_notes) if strong else scale_notes
        is_last = len(notes) == len(sounding) - 1
        pitch = _weighted_next_pitch(
            candidates, previous, rng, repeat_weight, final_pcs if is_last else frozenset()
        )
        velocity = STRONG_VELOCITY if strong else WEAK_VELOCITY
        notes.append(Note(pitch, bar_start + position, duration, velocity))
        previous = pitch
        position += duration
    return notes, previous


def generate_melody(
    chords: list[Chord],
    mood: Mood,
    key: Key,
    rng: random.Random,
    low: int = MELODY_LOW,
    high: int = MELODY_HIGH,
    beats_per_bar: int = 4,
) -> list[Note]:
    """Generate a melody over ``chords``, one bar per chord, using the mood's scale and rhythms.

    ``key`` gives the tonic. The melody's notes come from ``mood.scale`` on that tonic, which may
    differ from the chords' scale (e.g. a pentatonic melody over major-key chords).
    """
    melody_key = Key(key.tonic, mood.scale)
    scale_notes = scale_midi_notes(melody_key, low, high)
    if not scale_notes:
        raise ValueError(f"No notes of {mood.scale} between MIDI {low} and {high}")

    melody: list[Note] = []
    previous = None
    for i, chord in enumerate(chords):
        rhythm = rng.choice(mood.rhythms)
        # End on the tonic (the "home" note) when the final chord contains it. Ending on the
        # tonic over a chord without it, like C over a G chord, would sound unresolved.
        is_final_bar = i == len(chords) - 1
        ends_home = is_final_bar and key.tonic in chord.pitch_classes
        final_pcs = frozenset({key.tonic}) if ends_home else frozenset()
        notes, previous = generate_bar(
            chord,
            rhythm,
            i * beats_per_bar,
            scale_notes,
            previous,
            rng,
            mood.repeat_weight,
            final_pcs,
        )
        melody.extend(notes)
    return melody
