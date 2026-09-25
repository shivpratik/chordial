# Chordial

*Pick a mood, get a song you can play.*

Chordial is a procedural music generator. Choose a mood (happy, melancholic, tense, calm) and it
composes a short track: a chord progression plus a melody that follows music theory rules, written
out as a MIDI file. Chord sheets, strumming patterns, guitar tabs, audio and a web app are on the way.

> Status: early development (core CLI generator).

## Install

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/<you>/chordial.git
cd chordial
uv sync
```

## Usage

```bash
uv run chordial moods                                     # list available moods
uv run chordial generate --mood happy --seed 42 -o out/happy.mid
```

Same seed gives the same song, so a track can be reproduced or shared.

## Development

```bash
uv run pytest --cov=chordial
uv run ruff check . && uv run ruff format .
```

Design notes live in [docs/decisions.md](docs/decisions.md).

## License

MIT
