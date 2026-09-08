> **Status (2026-09-08): this doc is now the vision/index, not a buildable spec.** Its bullets
> were split into scoped `[draft]` stubs during the EXECUTIVE_SUMMARY §5 scope-creep containment,
> each built later on its own branch off `main`:
> [`video-filestore`](./%5Bdraft%5Dvideo-filestore.md) ·
> [`sql-job-tracking`](./%5Bdraft%5Dsql-job-tracking.md) ·
> [`background-process-cli`](./%5Bdraft%5Dbackground-process-cli.md) ·
> [`local-llm-summarization`](./%5Bdraft%5Dlocal-llm-summarization.md) ·
> [`evals-harness`](./%5Bdraft%5Devals-harness.md). See [`../ROADMAP.md`](../ROADMAP.md) §C.

# Goal

Convert my current flow into a cli tool thats proper and easy to use.
- filestore for videos...
- SQL db for jobs and transcripts etc
- cli uses process's so long steps run in background?

polish and refactor the codebase to prepare for:
- local llm summarization and use
- evals and testing transcription and summarization alternatives

# Current Flow

0. Obtain a video recording of meeting
- has minimally master audio track
- has ideally mic and desktop audio tracks

1. transcribe audio to text w/ speaker diarization and timestamps
- whisper currently
- uses ffmpeg to obtain audio tracks

2. Augment transcription with metadata and any notes
- add speakers and meeting context 
- add any additional artifacts discussed or provided

3. summarize meeting
- choose a summarization prompt
- summarize transcript
- rename file
- export as markdown

