# FFprobe Reference

## Synopsis
`ffprobe [options] [input_url]`

## Description
`ffprobe` gathers information from multimedia streams and prints it in human- and machine-readable fashion. It can be used to check the container format and the relative properties of each stream.

## Main Options
- `-f format`: Force format to use.
- `-unit`: Show the unit of the displayed values.
- `-prefix`: Use SI prefixes for the displayed values.
- `-byte_binary_prefix`: Use binary prefixes for byte values.
- `-sexagesimal`: Use sexagesimal format HH:MM:SS.MICROSECONDS for time values.
- `-pretty`: Beautify the format of the displayed values.
- `-show_format`: Show information about the container format.
- `-show_streams`: Show information about each media stream.
- `-show_packets`: Show information about each input packet.
- `-show_frames`: Show information about each input frame.
- `-show_programs`: Show information about programs and their streams.
- `-show_chapters`: Show information about chapters.

## Output Writers
- `-print_format writer_name[=writer_options]`: Set the output printing format (json, xml, csv, flat, ini).
- `-of writer_name[=writer_options]`: Alias for `-print_format`.

## Common Usage
`ffprobe -v error -show_format -show_streams -of json input.mp4`
