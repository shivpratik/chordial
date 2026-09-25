"""``generate_song``: the single entry point used by the CLI (and later the Streamlit app)."""

from __future__ import annotations

import random

from chordial.harmony import choose_key, choose_tempo, generate_progression
from chordial.melody import generate_melody
from chordial.models import Key, Song
from chordial.moods import Mood, load_moods
from chordial.theory import parse_key


def random_seed() -> int:
    """A fresh, human-friendly seed (easy to type back in to reproduce a track)."""
    return random.SystemRandom().randrange(1_000_000)


def generate_song(
    mood: str,
    bars: int = 8,
    seed: int | None = None,
    key: str | None = None,
    tempo: int | None = None,
    moods: dict[str, Mood] | None = None,
) -> Song:
    """Compose a song for ``mood``. The same arguments and seed always give the same song.

    ``key`` (e.g. ``"G"`` or ``"Am"``) and ``tempo`` override the mood's random choices. The random
    number generator is always consumed in the same order, so overriding the key with the same
    seed gives the *same* song transposed to the new key.
    """
    moods = moods if moods is not None else load_moods()
    if mood not in moods:
        raise ValueError(f"Unknown mood {mood!r}. Choose from: {', '.join(moods)}")
    m = moods[mood]
    if seed is None:
        seed = random_seed()
    rng = random.Random(seed)

    song_key = choose_key(m, rng)
    song_tempo = choose_tempo(m, rng)
    if key is not None:
        song_key = _override_key(key, m)
    if tempo is not None:
        if not 20 <= tempo <= 300:
            raise ValueError(f"tempo must be between 20 and 300 BPM, got {tempo}")
        song_tempo = tempo

    chords = generate_progression(m, song_key, bars, rng)
    melody = generate_melody(chords, m, song_key, rng)
    return Song(
        mood=mood,
        key=song_key,
        scale=m.scale,
        tempo=song_tempo,
        seed=seed,
        chords=chords,
        melody=melody,
    )


def _override_key(name: str, mood: Mood) -> Key:
    requested = parse_key(name)
    mood_is_minor = "minor" in mood.harmony_scale
    if requested.is_minor != mood_is_minor:
        example = "Am" if mood_is_minor else "C"
        kind = "minor" if mood_is_minor else "major"
        raise ValueError(f"{mood.name} uses {kind} keys; try something like {example!r}")
    return Key(requested.tonic, mood.harmony_scale)
