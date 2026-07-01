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

