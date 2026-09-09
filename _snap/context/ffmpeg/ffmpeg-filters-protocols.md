# FFmpeg Filters & Protocols Reference

## Filtergraph Syntax
A filtergraph is a directed graph of connected filters.
`[input_link_label1][input_link_label2]... filter_name=parameters [output_link_label1][output_link_label2]...`

### Common Audio Filters
- `aresample`: Resample audio.
- `atempo`: Adjust audio tempo without changing pitch.
- `volume`: Change input audio volume.
- `silencedetect`: Detect silence in audio.
- `amerge`: Merge multiple audio streams into a single multi-channel stream.

### Common Video Filters
- `scale`: Resize input video.
- `crop`: Crop input video.
- `fps`: Convert video to specified constant frame rate.
- `overlay`: Overlay one video on top of another.
- `drawtext`: Draw text string or text from a file on top of video.

## Protocols
- `file`: Read from or write to a file.
- `pipe`: Read from or write to a pipe (stdin/stdout).
- `http`/`https`: Read from or write to HTTP(S) resources.
- `rtp`/`rtsp`: Real-time transport protocols.
- `concat`: Concatenate multiple inputs.
