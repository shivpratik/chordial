# Project: Chordial

*Pick a mood, get a song you can play.*

A procedural music generator that composes short tracks from a chosen mood and outputs:
1. A MIDI file and rendered audio (acoustic guitar sound)
2. A **chord sheet with strumming pattern** and **simple guitar tabs**, so a guitarist can play the generated song

Name chosen: Chordial (check GitHub and PyPI availability; the package name could be `chordial` or `chordial-music` if taken).

## About the developer

- Plays guitar at a basic level (knows common open chords like C, G, D, Am, Em, F).
- New to formal music theory; learning it alongside the project.
- Portfolio project: code quality, tests, documentation, a live demo, and clear commit history all matter.
- The developer will test generated progressions by playing them on guitar.

## How the generator works (layered approach)

1. **Mood → settings:** each mood maps to scale, tempo range, chord progressions, rhythm feel, and strumming patterns.
2. **Harmony first:** generate the chord progression.
3. **Melody:** chord tones on strong beats, other scale notes allowed on weak beats; prefer stepwise motion over big leaps.
4. **Bass and rhythm:** bass on chord roots, simple drum pattern.
5. **Structure:** create a 1–2 bar motif and repeat it with small variations (biggest quality improvement).

## Initial mood table

| Mood        | Scale          | Tempo (BPM) | Progression   | Rhythm feel           |
|-------------|----------------|-------------|---------------|-----------------------|
| Happy       | Major          | 110–130     | I–V–vi–IV     | Short, bouncy notes   |
| Melancholic | Natural minor  | 60–80       | i–VI–III–VII  | Long, sustained notes |
| Tense       | Harmonic minor | 90–120      | i–iv–V        | Repeated, off-beat    |
| Calm        | Pentatonic     | 70–90       | I–IV          | Sparse, gentle        |

Mood definitions live in `src/chordial/data/moods.yaml` so new moods can be added without code changes.

## Guitar output features

- **Chord sheet:** key, tempo, strumming pattern (e.g. `D - D U - U D U`), and bars of chord names.
- **Beginner mode:** prefer open chords (C, G, D, A, E, Am, Em, Dm); avoid barre chords; transpose to a guitar-friendly key when needed.
- **Strumming patterns** chosen per mood.
- **Tabs:** convert melody notes to string/fret positions in standard tuning (E A D G B E), minimizing hand movement along the neck. Document this algorithm; it's a key talking point.

## Build plan

### Weeks 1–2 — Core generator (CLI)
- Music theory module: scales, diatonic chords, Roman numeral progressions, transposition.
- Mood config + chord progression generator.
- Melody generator using chord-tone rules.
- Output a MIDI file from the command line.

### Week 3 — Fuller sound + guitar output
- Bass, drums, motif repetition.
- Chord sheet and strumming pattern output.
- Render MIDI to audio with FluidSynth and a free SoundFont (acoustic guitar = General MIDI program 26, which is `program=25` in pretty_midi's 0-based numbering).

### Week 4 — App and deploy
- Streamlit app: mood, tempo, length, beginner mode, regenerate button, and a **seed** input for reproducible tracks.
- Show audio player, chord sheet, and tabs; allow MIDI download.
- Deploy on Hugging Face Spaces.

### Later / stretch
- Tab generation for melodies (if not done in week 3).
- Markov chain melodies trained on public-domain MIDI (e.g. Bach chorales).
- **Raga mode:** ragas defined by allowed notes, arohana/avarohana patterns, characteristic phrases; approximate gamakas with pitch bends.

## Evaluation (makes the project stand out)

- Mood-guessing test: friends listen to ~10 generated tracks and guess the intended mood; report accuracy in the README.
- Developer plays several generated songs on guitar; note which progressions/strums felt natural or awkward and why.

## Structure

Installable package under `src/chordial/` (see `docs/decisions.md` for why).

```
chordial/
├── CLAUDE.md  README.md  LICENSE  pyproject.toml  uv.lock
├── src/chordial/
│   ├── data/moods.yaml  # mood definitions (packaged with the code)
│   ├── models.py        # Note, Chord, Key, Song dataclasses
│   ├── theory.py        # scales, chords, Roman numerals, transposition
│   ├── moods.py         # load + validate moods.yaml
│   ├── harmony.py       # chord progressions
│   ├── melody.py        # melody (+ motif generation in week 3)
│   ├── generate.py      # generate_song(): the single entry point
│   ├── render.py        # MIDI writing (+ FluidSynth audio in week 3)
│   ├── cli.py
│   ├── rhythm.py        # week 3: bass, drums, strumming patterns
│   ├── guitar.py        # week 3: chord shapes, chord sheets, tabs
│   └── app.py           # week 4: Streamlit
├── examples/            # sample generated tracks, sheets, tabs
├── docs/decisions.md
└── tests/
```

## Commands

- `uv sync`: install dependencies
- `uv run pytest`: run tests (`--cov=chordial` for coverage)
- `uv run ruff check . && uv run ruff format .`: lint and format
- `uv run chordial generate --mood happy --seed 42 -o out/happy.mid`

Local setup note: `~/Documents` is synced by iCloud, which sets the macOS `hidden` flag on files
inside `.venv`. Python 3.12 then skips the editable install's `.pth` file ("No module named
chordial"). The fix used here: the venv lives in `venv.nosync/` (iCloud ignores `*.nosync`) and
`.venv` is a symlink to it. To recreate: `rm -rf .venv venv.nosync && uv venv venv.nosync &&
ln -s venv.nosync .venv && uv sync`.

## Tech stack

- Python 3.10+ (developed on 3.12 via uv)
- pretty_midi (MIDI), PyYAML (config), pytest + ruff (dev)
- Later: FluidSynth + a free General MIDI SoundFont (audio), Streamlit (app)

## Working style for Claude

- Explain music theory concepts briefly in comments and docstrings, relating them to guitar where possible (e.g. "I–V–vi–IV in C = C, G, Am, F").
- Keep code simple and modular; the developer is building skills.
- All randomness flows through one `random.Random(seed)` passed down from `generate_song`; never use the global `random` module.
- Musical time is measured in beats everywhere; only `render.py` converts to seconds.
- Write tests for theory logic (scales, chord construction, transposition) and tab position selection.
- Keep a short decision log in `docs/decisions.md` for README and interview talking points.
