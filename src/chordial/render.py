"""Turn a Song into a MIDI file. (Audio rendering with FluidSynth comes in week 3.)"""

from __future__ import annotations

from pathlib import Path

import pretty_midi

from chordial.models import Chord, Song

# General MIDI "Acoustic Guitar (steel)". GM tables number it 26, but pretty_midi counts from 0.
ACOUSTIC_GUITAR = 25
CHORD_LOW = 48  # C3: chord roots are placed between C3 and B3
CHORD_VELOCITY = 70


def voice_chord(chord: Chord, low: int = CHORD_LOW) -> list[int]:
    """Stack a chord's notes upwards from its root, placed in the octave starting at ``low``.

    This is "close position": all three notes within an octave, e.g. Am -> A3 C4 E4.
    Real guitar voicings (which strings and frets to use) come with the chord shapes in week 3.
    """
    root = low + (chord.root - low) % 12
    return [root + (pc - chord.root) % 12 for pc in chord.pitch_classes]


def song_to_midi(song: Song) -> pretty_midi.PrettyMIDI:
    """Build a two-track MIDI (melody and block chords, both acoustic guitar)."""
    seconds_per_beat = 60.0 / song.tempo
    pm = pretty_midi.PrettyMIDI(initial_tempo=float(song.tempo))
    pm.time_signature_changes.append(pretty_midi.TimeSignature(song.beats_per_bar, 4, 0.0))

    melody = pretty_midi.Instrument(program=ACOUSTIC_GUITAR, name="Melody")
    for note in song.melody:
        melody.notes.append(
            pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=note.start * seconds_per_beat,
                end=note.end * seconds_per_beat,
            )
        )

    chords = pretty_midi.Instrument(program=ACOUSTIC_GUITAR, name="Chords")
    for bar, chord in enumerate(song.chords):
        start = bar * song.beats_per_bar * seconds_per_beat
        end = start + song.beats_per_bar * seconds_per_beat
        for pitch in voice_chord(chord):
            chords.notes.append(pretty_midi.Note(CHORD_VELOCITY, pitch, start, end))

    pm.instruments.extend([melody, chords])
    return pm


def write_midi(song: Song, path: str | Path) -> Path:
    """Write ``song`` as a MIDI file, creating parent folders as needed. Returns the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    song_to_midi(song).write(str(path))
    return path
