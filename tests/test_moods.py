import textwrap

import pytest

from chordial.moods import MoodConfigError, load_moods

VALID = """
happy:
  scale: major
  keys: [C]
  tempo: [110, 130]
  progressions:
    - {numerals: [I, V, vi, IV]}
  rhythms:
    - [1, 1, 1, 1]
"""


def write(tmp_path, text):
    path = tmp_path / "moods.yaml"
    path.write_text(textwrap.dedent(text))
    return path


def test_packaged_moods_load_and_validate():
    moods = load_moods()
    assert {"happy", "melancholic", "tense", "calm"} <= set(moods)


def test_calm_uses_major_harmony_under_pentatonic_melody():
    calm = load_moods()["calm"]
    assert calm.scale == "major_pentatonic"
    assert calm.harmony_scale == "major"


def test_harmony_scale_defaults_to_scale(tmp_path):
    mood = load_moods(write(tmp_path, VALID))["happy"]
    assert mood.harmony_scale == "major"
    assert mood.repeat_weight == 0.4


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("[I, V, vi, IV]", "[I, V, VI, IV]", "expects a maj chord"),
        ("[1, 1, 1, 1]", "[1, 1, 1]", "must add up to 4"),
        ("[1, 1, 1, 1]", "[-4]", "all rests"),
        ("keys: [C]", "keys: [Am]", "doesn't match harmony scale"),
        ("scale: major", "scale: major_pentatonic", "needs 7 notes"),
        ("scale: major", "scale: happy_scale", "Unknown scale"),
        ("tempo: [110, 130]", "tempo: [130, 110]", "tempo range"),
        ("  tempo: [110, 130]\n", "", "missing field 'tempo'"),
    ],
)
def test_invalid_moods_give_readable_errors(tmp_path, old, new, message):
    text = textwrap.dedent(VALID)
    assert old in text
    with pytest.raises(MoodConfigError, match=message) as err:
        load_moods(write(tmp_path, text.replace(old, new)))
    assert "Mood 'happy'" in str(err.value)


def test_empty_file(tmp_path):
    with pytest.raises(MoodConfigError):
        load_moods(write(tmp_path, ""))
