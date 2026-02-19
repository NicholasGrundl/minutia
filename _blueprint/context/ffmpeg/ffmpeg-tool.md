# FFmpeg CLI Reference

## Synopsis
`ffmpeg [global_options] {[input_file_options] -i input_url} ... {[output_file_options] output_url} ...`

## Description
`ffmpeg` is a very fast video and audio converter that can also grab from a live audio/video source. It can also convert between arbitrary sample rates and resize video on the fly with a high-quality polyphase filter.

## Stream Selection
By default, `ffmpeg` includes only one stream of each type (video, audio, subtitle) present in the inputs and adds them to each output file.
- `-map [-]input_file_id[:stream_specifier][,sync_file_id[:stream_specifier]] | [linklabel]`
- `-map_metadata[:metadata_spec_out] infile[:metadata_spec_in]`

## Main Options
- `-f fmt (input/output)`: Force input or output file format.
- `-i url (input)`: Input file URL.
- `-y (global)`: Overwrite output files without asking.
- `-n (global)`: Do not overwrite output files.
- `-c[:stream_specifier] codec (input/output,per-stream)`: Select an encoder (when used before an output file) or a decoder (when used before an input file).
- `-t duration (input/output)`: Stop writing the output or reading the input after its duration reaches duration.
- `-to position (input/output)`: Stop writing the output or reading the input at position.
- `-ss position (input/output)`: Seek to position.
- `-re (input)`: Read input at native frame rate.

## Video Options
- `-vframes number (output)`: Set the number of video frames to output.
- `-r[:stream_specifier] fps (input/output,per-stream)`: Set frame rate.
- `-s[:stream_specifier] size (input/output,per-stream)`: Set frame size.
- `-vn (input/output)`: As an input option, blocks all video streams. As an output option, disables video recording.
- `-vcodec codec (output)`: Set the video codec.

## Audio Options
- `-aframes number (output)`: Set the number of audio frames to output.
- `-ar[:stream_specifier] freq (input/output,per-stream)`: Set the audio sampling frequency.
- `-ac[:stream_specifier] channels (input/output,per-stream)`: Set the number of audio channels.
- `-an (input/output)`: Disable audio recording.
- `-acodec codec (input/output)`: Set the audio codec.
