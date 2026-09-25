"""Load and validate mood definitions from ``data/moods.yaml``.

A mood bundles every musical choice the generator makes: scale, keys, tempo range, chord
progressions and melody rhythms. Validation resolves every progression in every allowed key up
front, so a typo in the YAML fails at load time with a clear message instead of mid-generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import yaml

from chordial.models import Key
from chordial.theory import chord_from_roman, parse_key, scale_intervals

BEATS_PER_BAR = 4


class MoodConfigError(ValueError):
    """Raised when moods.yaml contains something the generator can't use."""


@dataclass(frozen=True)
class Progression:
    numerals: tuple[str, ...]
    weight: float = 1.0


@dataclass(frozen=True)
class Mood:
    name: str
    description: str
    scale: str
    harmony_scale: str
    keys: tuple[Key, ...]
    tempo: tuple[int, int]
    progressions: tuple[Progression, ...]
    rhythms: tuple[tuple[float, ...], ...]
    repeat_weight: float = 0.4


def load_moods(path: str | Path | None = None) -> dict[str, Mood]:
    """Load moods from ``path``, or from the packaged ``moods.yaml`` if no path is given."""
    if path is None:
        text = resources.files("chordial").joinpath("data/moods.yaml").read_text(encoding="utf-8")
    else:
        text = Path(path).read_text(encoding="utf-8")

    raw = yaml.safe_load(text)
    if not isinstance(raw, dict) or not raw:
        raise MoodConfigError("Mood file must be a mapping of mood names to settings")
    return {name: _parse_mood(name, settings) for name, settings in raw.items()}


def _parse_mood(name: str, raw: dict) -> Mood:
    try:
        scale = raw["scale"]
        harmony_scale = raw.get("harmony_scale", scale)
        mood = Mood(
            name=name,
            description=raw.get("description", ""),
            scale=scale,
            harmony_scale=harmony_scale,
            keys=tuple(_parse_mood_key(k, harmony_scale) for k in raw["keys"]),
            tempo=(int(raw["tempo"][0]), int(raw["tempo"][1])),
            progressions=tuple(
                Progression(tuple(p["numerals"]), float(p.get("weight", 1.0)))
                for p in raw["progressions"]
            ),
            rhythms=tuple(tuple(float(d) for d in r) for r in raw["rhythms"]),
            repeat_weight=float(raw.get("repeat_weight", 0.4)),
        )
        validate(mood)
    except MoodConfigError as e:
        raise MoodConfigError(f"Mood {name!r}: {e}") from None
    except (KeyError, TypeError, IndexError, ValueError) as e:
        detail = f"missing field {e}" if isinstance(e, KeyError) else str(e)
        raise MoodConfigError(f"Mood {name!r}: {detail}") from None
    return mood


def _parse_mood_key(name: str, harmony_scale: str) -> Key:
    """Parse ``"Am"`` or ``"G"`` into a Key whose mode is the mood's harmony scale."""
    key = parse_key(name)
    if key.is_minor != ("minor" in harmony_scale):
        raise MoodConfigError(
            f"key {name!r} doesn't match harmony scale {harmony_scale!r} "
            "(minor keys are written like 'Am')"
        )
    return Key(key.tonic, harmony_scale)


def validate(mood: Mood) -> None:
    """Check that a mood can actually be generated. Raises MoodConfigError if not."""
    scale_intervals(mood.scale)
    if len(scale_intervals(mood.harmony_scale)) != 7:
        raise MoodConfigError(
            f"harmony_scale {mood.harmony_scale!r} needs 7 notes to build chords; "
            "set harmony_scale to its parent scale (e.g. major)"
        )
    if not mood.keys:
        raise MoodConfigError("needs at least one key")
    low, high = mood.tempo
    if not 20 <= low <= high <= 300:
        raise MoodConfigError(f"tempo range {mood.tempo} should be [min, max] between 20 and 300")
    if not mood.progressions:
        raise MoodConfigError("needs at least one progression")
    for prog in mood.progressions:
        if not prog.numerals or prog.weight <= 0:
            raise MoodConfigError(f"progression {list(prog.numerals)} is empty or has weight <= 0")
        for key in mood.keys:
            for numeral in prog.numerals:
                chord_from_roman(numeral, key)  # raises ValueError with a helpful message
    if not mood.rhythms:
        raise MoodConfigError("needs at least one rhythm")
    for rhythm in mood.rhythms:
        if sum(abs(d) for d in rhythm) != BEATS_PER_BAR or 0 in rhythm:
            raise MoodConfigError(f"rhythm {list(rhythm)} must add up to {BEATS_PER_BAR} beats")
        if all(d < 0 for d in rhythm):
            raise MoodConfigError(f"rhythm {list(rhythm)} is all rests")
