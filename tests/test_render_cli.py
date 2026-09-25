import pretty_midi
import pytest

from chordial import generate_song
from chordial.cli import chord_grid, main
from chordial.models import Key
from chordial.render import ACOUSTIC_GUITAR, voice_chord, write_midi
from chordial.theory import chord_from_roman

# --- generate_song -----------------------------------------------------------------------------


def test_generate_song_is_reproducible():
    assert generate_song("tense", seed=9) == generate_song("tense", seed=9)


def test_key_override_transposes_the_same_song():
    original = generate_song("melancholic", seed=3, key="Am")
    moved = generate_song("melancholic", seed=3, key="Em")
    assert moved.key == Key(4, "natural_minor")
    assert moved.tempo == original.tempo
    assert [c.roman for c in moved.chords] == [c.roman for c in original.chords]


def test_overrides_and_validation():
    song = generate_song("happy", bars=5, seed=1, tempo=100)
    assert song.tempo == 100 and song.bars == 5
    with pytest.raises(ValueError, match="minor keys"):
        generate_song("melancholic", key="C")
    with pytest.raises(ValueError, match="Unknown mood"):
        generate_song("grumpy")
    with pytest.raises(ValueError, match="tempo"):
        generate_song("happy", tempo=5)


def test_seed_is_chosen_when_missing():
    assert isinstance(generate_song("calm").seed, int)


# --- render ------------------------------------------------------------------------------------


def test_voice_chord_close_position():
    am = chord_from_roman("vi", Key(0, "major"))
    assert voice_chord(am) == [57, 60, 64]  # A3 C4 E4


def test_midi_round_trip(tmp_path):
    song = generate_song("happy", bars=4, seed=11)
    path = write_midi(song, tmp_path / "sub" / "song.mid")

    pm = pretty_midi.PrettyMIDI(str(path))
    # MIDI stores whole microseconds per beat, so the tempo comes back very slightly off.
    assert pm.get_tempo_changes()[1][0] == pytest.approx(song.tempo, rel=1e-4)
    assert [i.program for i in pm.instruments] == [ACOUSTIC_GUITAR, ACOUSTIC_GUITAR]
    melody, chords = pm.instruments
    assert len(melody.notes) == len(song.melody)
    assert len(chords.notes) == 3 * song.bars
    bar_seconds = 4 * 60 / song.tempo
    assert pm.get_end_time() == pytest.approx(song.bars * bar_seconds, rel=1e-3)


def test_midi_is_byte_identical_for_same_seed(tmp_path):
    a = write_midi(generate_song("calm", seed=5), tmp_path / "a.mid")
    b = write_midi(generate_song("calm", seed=5), tmp_path / "b.mid")
    assert a.read_bytes() == b.read_bytes()


# --- CLI ---------------------------------------------------------------------------------------


def test_chord_grid_four_bars_per_line():
    song = generate_song("happy", bars=6, seed=1)
    lines = chord_grid(song).splitlines()
    assert len(lines) == 2
    assert lines[0].count("|") == 5 and lines[1].count("|") == 3


def test_cli_generate(tmp_path, capsys):
    out = tmp_path / "x.mid"
    assert main(["generate", "--mood", "tense", "--seed", "8", "-o", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "seed 8" in printed and "A harmonic minor" in printed
    assert out.exists()


def test_cli_moods(capsys):
    assert main(["moods"]) == 0
    assert "melancholic" in capsys.readouterr().out


def test_cli_reports_errors(capsys):
    assert main(["generate", "--mood", "calm", "--key", "Am"]) == 2
    assert "major keys" in capsys.readouterr().err
