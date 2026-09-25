"""Command-line interface: ``chordial moods`` and ``chordial generate``."""

from __future__ import annotations

import argparse
import sys

from chordial.generate import generate_song
from chordial.models import Song
from chordial.moods import load_moods
from chordial.render import write_midi
from chordial.theory import key_name, tonic_name

BARS_PER_LINE = 4


def chord_grid(song: Song) -> str:
    """Chords laid out as bars, four per line: ``| G    | D    | Em   | C    |``."""
    width = max(len(c.name) for c in song.chords) + 2
    lines = []
    for i in range(0, len(song.chords), BARS_PER_LINE):
        row = song.chords[i : i + BARS_PER_LINE]
        lines.append("| " + " | ".join(c.name.ljust(width) for c in row) + " |")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chordial", description="Pick a mood, get a song you can play."
    )
    parser.add_argument("--moods", metavar="PATH", help="use a custom moods.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("moods", help="list available moods")

    gen = sub.add_parser("generate", help="generate a song and write a MIDI file")
    gen.add_argument("--mood", required=True, help="mood name (see `chordial moods`)")
    gen.add_argument("--bars", type=int, default=8, help="number of bars (default 8)")
    gen.add_argument("--tempo", type=int, help="beats per minute (default: random in mood range)")
    gen.add_argument("--key", help="key such as G or Am (default: random from mood)")
    gen.add_argument("--seed", type=int, help="random seed; same seed = same song")
    gen.add_argument("-o", "--output", help="MIDI file path (default out/<mood>-<seed>.mid)")
    return parser


def _cmd_moods(moods: dict) -> None:
    for mood in moods.values():
        keys = ", ".join(tonic_name(k) + ("m" if "minor" in k.mode else "") for k in mood.keys)
        progs = "  ".join("-".join(p.numerals) for p in mood.progressions)
        print(f"{mood.name:<12} {mood.description}")
        print(f"{'':<12} scale {mood.scale} | keys {keys} | {mood.tempo[0]}-{mood.tempo[1]} BPM")
        print(f"{'':<12} progressions {progs}")


def _cmd_generate(args: argparse.Namespace, moods: dict) -> None:
    song = generate_song(
        args.mood, bars=args.bars, seed=args.seed, key=args.key, tempo=args.tempo, moods=moods
    )
    path = write_midi(song, args.output or f"out/{song.mood}-{song.seed}.mid")
    print(f"Chordial — {song.mood} · {key_name(song.key)} · {song.tempo} BPM · seed {song.seed}")
    print(chord_grid(song))
    print(f"Wrote {path}")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        moods = load_moods(args.moods)
        if args.command == "moods":
            _cmd_moods(moods)
        else:
            _cmd_generate(args, moods)
    except (ValueError, OSError) as e:  # MoodConfigError is a ValueError
        print(f"chordial: error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
