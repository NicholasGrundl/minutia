# Known Issues & Bugs

## Video Extraction - FFmpeg File Overwrite Issue

**Status**: Identified, needs fix  
**Priority**: Medium  
**Affects**: `src/minutia/steps/video_extraction.py`

### Problem
The ffmpeg-python library fails when trying to extract audio tracks if output files already exist. The `extract_audio_track()` function doesn't include the overwrite flag, causing the entire extraction process to fail with:

```
ffmpeg._run.Error: ffmpeg error (see stderr output for detail)
```

### Root Cause
In `video_extraction.py:26`, the ffmpeg output command lacks the overwrite parameter:
```python
output = ffmpeg.output(audio, str(output_file))  # Missing overwrite flag
```

### Solution
Add overwrite flag to the ffmpeg output command:
```python
output = ffmpeg.output(audio, str(output_file), **{"y": None})  # Enable overwrite
```

### Test Cases Needed
- [ ] Test extraction when output directory is empty
- [ ] Test extraction when output files already exist (should overwrite)
- [ ] Test extraction when re-running after partial failure
- [ ] Test extraction with read-only output files (should fail gracefully)

### Notes
- This issue was discovered while running `CreateNewFixtureSet.ipynb`
- The CLI pipeline should handle this more gracefully than the notebook
- Consider adding a `--no-overwrite` flag for safety in the CLI
- Manual ffmpeg command works fine: `ffmpeg -i input.mkv -map 0:a:0 output.wav -y`