# Decision log

Short notes on design choices: what was decided, and why.

## 1. Installable package in `src/chordial/`

The original sketch had flat `src/theory.py`-style modules. A real package (`src/chordial/`) with
`pyproject.toml` means `import chordial.theory` works the same from tests, the CLI, the Streamlit
app and a `pip install`, without path hacks. The `src/` layout also ensures tests run against the
installed package, not whatever happens to be in the working directory.

## 2. Mood config lives inside the package

`moods.yaml` is at `src/chordial/data/moods.yaml` and is loaded with `importlib.resources`, so it
ships with the package (important for Hugging Face Spaces and PyPI). `--moods PATH` lets you
experiment with a custom file without touching the code.

## 3. Time is measured in beats, not seconds

Every `Note` stores `start` and `duration` in beats. Music logic ("is this a strong beat?", "does
this bar add up to 4?") is then independent of tempo, and only `render.py` converts beats to
seconds (`seconds = beats * 60 / bpm`).

## 4. Progressions are Roman numerals, validated by case

Progressions are written as Roman numerals (`I V vi IV`) so one progression works in every key:
in C it's C–G–Am–F, in G it's G–D–Em–C. Chords are built by stacking thirds on the scale, and the
numeral's case (upper = major, lower = minor) is *checked* against the result. This catches config
mistakes early, e.g. writing `V` in natural minor, where the fifth chord is actually minor (`v`).

## 5. `harmony_scale` separate from the melody `scale`

You can't build chords by stacking thirds on a 5-note pentatonic scale. So the Calm mood plays its
melody on the major pentatonic but takes its chords from the parent major scale
(`harmony_scale: major`). The pentatonic has no 4th or 7th, so the melody never clashes.

## 6. Keys restricted per mood so every chord is an open chord

Each mood only offers keys where every chord of every progression is an open chord a beginner
knows (plus F). Building the progressions in every key showed how quickly barre chords appear:

- Happy: C and G only. D major's vi is Bm and A major's vi is F#m, both barre chords.
- Melancholic: Am and Em. D minor's VI is Bb.
- Tense (harmonic minor, whose V is major): Am only. E minor's V is B and D minor's iv is Gm.

`--key` can still pick any key; beginner mode in week 3 will transpose into playable keys instead
of restricting the choice.

## 7. General MIDI program numbering is off by one

GM tables list "Acoustic Guitar (steel)" as program 26 (1-based). pretty_midi uses 0-based program
numbers, so the code uses `program=25`.

## 8. One seeded RNG, passed down explicitly

`generate_song()` creates a single `random.Random(seed)` and passes it to every generator, so no
module touches the global `random` state. The same seed always produces the same song, which makes
tests deterministic and lets users share or reproduce a track. If no seed is given, one is picked
and printed.

## 9. Melodies end on the tonic when the final chord allows it

If the final chord contains the tonic (the "home" note), the last melody note is forced onto it,
as long as it's within a 5th of the previous note. A weight bonus alone only got ~30% of songs to
end home. Ending on the tonic over a chord that doesn't contain it (C over a G chord) would sound
unresolved, so the rule only applies when the chord allows it.

Open question for the guitar test: an 8-bar song repeats its progression exactly, so it ends on
the progression's last chord (e.g. IV or V) instead of the tonic chord. That loops nicely but may
sound unfinished as an ending.
