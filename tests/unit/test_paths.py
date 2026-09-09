import re

import pytest

from minutia.paths import CleanupPolicy, RunPaths, resolve_run_directory


def test_from_video_input_creates_expected_structure(tmp_path):
    video = tmp_path / "Meeting Notes.mkv"
    video.write_text("dummy", encoding="utf-8")

    base_runs = tmp_path / "runs"
    run_paths = RunPaths.from_video_input(video, base_output_dir=base_runs)

    assert run_paths.input_path == video.resolve()
    assert run_paths.run_root.parent == base_runs.resolve()
    assert re.match(r"\d{4}-\d{2}-\d{2}_meeting-notes", run_paths.run_root.name)
    assert run_paths.microphone_audio == run_paths.audio_dir / "microphone_audio.wav"
    assert run_paths.desktop_audio == run_paths.audio_dir / "desktop_audio.wav"
    assert run_paths.merged_transcript == run_paths.run_root / "merged_transcript.json"
    assert run_paths.summary_file == run_paths.run_root / "summary.txt"

    run_paths.ensure_directories()
    assert run_paths.audio_dir.exists()
    assert run_paths.transcripts_dir.exists()


def test_from_audio_inputs_uses_parent_name(tmp_path):
    audio_parent = tmp_path / "meeting_audio"
    audio_parent.mkdir()
    mic = audio_parent / "mic.wav"
    desk = audio_parent / "desk.wav"
    mic.write_text("mic", encoding="utf-8")
    desk.write_text("desk", encoding="utf-8")

    run_paths = RunPaths.from_audio_inputs(mic, desk, base_output_dir=tmp_path / "runs")
    assert run_paths.run_root.parent == (tmp_path / "runs").resolve()
    assert "meeting_audio" in run_paths.run_root.name
    assert run_paths.input_path == mic.resolve()


def test_resolve_run_directory_handles_collisions(tmp_path):
    base_dir = tmp_path / "runs"
    base_dir.mkdir()
    first = resolve_run_directory("2025-01-01_test", base_dir)
    first.mkdir()
    second = resolve_run_directory("2025-01-01_test", base_dir)
    assert second.name == "2025-01-01_test_2"


def test_cleanup_keep_final_removes_audio(tmp_path):
    video = tmp_path / "Meeting.mkv"
    video.write_text("dummy", encoding="utf-8")
    run_paths = RunPaths.from_video_input(video, base_output_dir=tmp_path / "runs")
    run_paths.ensure_directories()

    run_paths.microphone_audio.write_text("audio", encoding="utf-8")
    run_paths.desktop_audio.write_text("audio", encoding="utf-8")

    run_paths.cleanup(CleanupPolicy.KEEP_FINAL)
    assert not run_paths.microphone_audio.exists()
    assert not run_paths.desktop_audio.exists()
    if run_paths.audio_dir.exists():
        assert not any(run_paths.audio_dir.iterdir())


def test_cleanup_on_error_removes_run_directory(tmp_path):
    video = tmp_path / "Meeting.mkv"
    video.write_text("dummy", encoding="utf-8")
    run_paths = RunPaths.from_video_input(video, base_output_dir=tmp_path / "runs")
    run_paths.ensure_directories()

    assert run_paths.run_root.exists()
    run_paths.cleanup(CleanupPolicy.CLEANUP_ON_ERROR)
    assert not run_paths.run_root.exists()


def test_resolve_run_directory_exhaustion(tmp_path):
    with pytest.raises(RuntimeError):
        resolve_run_directory("existing", tmp_path, max_attempts=0)
