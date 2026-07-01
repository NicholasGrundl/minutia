# Meeting Recorder - Design Document

## Overview

### Purpose and Scope

Meeting Recorder is a Python-based command-line tool designed to capture simultaneous audio streams from both microphone input and desktop system audio during virtual meetings. The primary purpose is to enable automated transcription and summarization of meetings by maintaining separate audio channels for the user (microphone) and other meeting participants (desktop audio). This separation allows downstream transcription systems to attribute speech to specific speakers, creating more accurate and useful meeting transcripts.

The tool prioritizes cross-platform compatibility, focusing initially on Windows (native) and macOS, with best-effort support for Windows Subsystem for Linux (WSL). The design emphasizes ease of installation via pip, one-time setup with clear documentation, and robust recording that gracefully handles failures without data loss.

### Core Technologies

The package leverages several key Python libraries and system-level audio technologies to achieve its goals:

**Python Libraries**: sounddevice (cross-platform audio I/O via PortAudio), PyAudioWPatch (Windows WASAPI loopback support), numpy (audio processing and level calculations), Typer (CLI framework with type hints), Rich (terminal UI with live updates), platformdirs (cross-platform config directory management), PyYAML (configuration file management)

**Audio System Technologies**: WASAPI Loopback (Windows system audio capture), BlackHole virtual audio driver (macOS system audio routing), PulseAudio/PipeWire (Linux and WSL audio forwarding)

**Optional Extensions**: ipywidgets (Jupyter notebook interface), bqplot or plotly (waveform visualization in notebooks)

### Table of Contents

1. Overview
2. Architecture and Design Decisions
   - Recording Strategy
   - Platform Abstraction
   - Configuration Management
   - Output Format
   - Error Handling and Robustness
3. Project Structure
   - Directory Layout
   - Module Responsibilities
4. Platform-Specific Implementation
   - Windows Native
   - macOS
   - Windows Subsystem for Linux
5. User Interface Design
   - Command-Line Interface
   - Setup Wizard
   - Recording Display
   - Configuration Management Commands
6. Audio Processing Details
   - Device Detection and Enumeration
   - Level Metering
   - Timestamp Synchronization
   - File Writing Strategy
7. Configuration System
   - Configuration Schema
   - Default Behavior
   - Device Fingerprinting
8. Development and Testing Strategy
   - Phased Implementation Plan
   - Testing Approach
   - Platform Testing Access
9. Documentation Requirements
   - Installation Guides
   - Platform-Specific Setup
   - Troubleshooting
10. Remaining Gaps

## Architecture and Design Decisions

This section outlines the fundamental architectural choices that shape the implementation of Meeting Recorder. Each decision represents a trade-off between competing concerns such as simplicity, reliability, performance, and cross-platform compatibility.

### Recording Strategy

The core recording mechanism uses threading with callback-based audio capture rather than multiprocessing or asyncio. This decision stems from the nature of audio I/O operations and Python's Global Interpreter Lock (GIL). Audio capture occurs in separate C-level threads managed by the sounddevice library, which means the actual audio sampling happens outside of Python's GIL constraints. The Python code primarily coordinates file writing and state management, both of which are I/O-bound operations where the GIL is released during system calls.

Each audio stream (microphone and desktop) operates with its own callback function that fires when audio data is available. These callbacks perform minimal work: copying the audio buffer and placing it into a thread-safe queue. Separate writer threads drain these queues and write data to disk. This producer-consumer pattern ensures that audio callbacks complete quickly and don't risk buffer overruns, while file I/O happens asynchronously without blocking capture.

The threading model provides shared memory between recording streams, simplifying coordination of start/stop operations and allowing real-time level metering to update a single display. The alternative multiprocessing approach would require complex inter-process communication and wouldn't provide meaningful performance benefits for this workload.

### Platform Abstraction

Cross-platform support is achieved through a router pattern with platform-specific implementation modules. A base abstract class defines the interface that all platform modules must implement, including methods for device enumeration, system audio detection, and stream initialization. The platform detector module identifies the current operating system and instantiates the appropriate platform implementation at runtime.

This abstraction allows the core recording logic to remain platform-agnostic while delegating OS-specific audio system interactions to specialized modules. Each platform module encapsulates the unique APIs and quirks of its target system: WASAPI loopback on Windows, BlackHole driver interaction on macOS, and PulseAudio monitor sources on Linux/WSL.

The trade-off is additional code complexity and the need to maintain multiple implementations. However, this is preferable to a monolithic approach that would result in tangled conditional logic throughout the codebase. The abstraction also positions the project well for future platform additions or API changes.

### Configuration Management

Configuration is managed through YAML files stored in platform-appropriate directories determined by the platformdirs library. This approach provides human-readable, version-controllable configuration while respecting OS conventions (e.g., ~/.config on Linux, ~/Library/Application Support on macOS, AppData on Windows).

The configuration system maintains a single canonical config per machine rather than supporting multiple profiles. This simplifies the user experience and reduces the cognitive load of profile management. Smart defaults minimize the configuration surface: the system attempts to automatically detect reasonable device selections and only requires explicit configuration when multiple viable options exist.

Device selection in the configuration uses a fingerprinting approach rather than storing fragile device names. Each device is identified by a hash of its stable properties, and the system matches these fingerprints to available devices at startup. This makes configuration more robust to device name changes or index reassignment while still allowing the system to detect when devices genuinely change.

### Output Format

Recording sessions produce separate WAV files for each audio stream (microphone and desktop) alongside a JSON metadata file. WAV format is chosen for its simplicity, universal compatibility, and lack of patent encumbrance. The uncompressed format does result in large files for long meetings, but this is acceptable given modern storage capacity and can be addressed post-MVP with optional compression.

Separate files for each stream (rather than a single multi-channel file) simplify downstream processing and allow independent manipulation of each audio source. The metadata file records essential information including device names, sample rates, recording start/stop timestamps, platform details, and package version. This metadata proves crucial for debugging issues and provides context for transcription systems.

Files are written to a session directory with ISO 8601 timestamps in the name for unambiguous sorting and identification. The directory structure looks like:

```
meeting_2024-10-09_143052/
  ├── mic.wav
  ├── desktop.wav
  └── metadata.json
```

### Error Handling and Robustness

The system prioritizes data preservation over perfection. When errors occur during recording, the principle is always to save whatever has been captured rather than discarding partial recordings. Graceful shutdown on Ctrl+C properly closes files and writes all buffered audio before exiting.

For the MVP, crash recovery follows a simplified approach: if a stream fails, the system logs the failure with timestamps, saves whatever audio was captured, and optionally attempts to restart that stream to a new file. This is more reliable than attempting seamless recovery with synthesized silence, which introduces complexity and potential for additional bugs. Post-MVP enhancements can explore more sophisticated recovery strategies once the basic recording pipeline is proven stable.

The system includes health checking capabilities to detect issues before recording begins. A pre-flight test performs a short capture to verify devices are functional and not producing dead silence. The status command provides diagnostic information about the current configuration and detected capabilities.

## Project Structure

The project follows modern Python packaging conventions with a clear separation between source code, tests, documentation, and auxiliary scripts. This section details the organization and responsibilities of each component.

### Directory Layout

```
meeting-recorder/
├── README.md
├── LICENSE
├── pyproject.toml
├── docs/
│   ├── installation/
│   │   ├── windows.md
│   │   ├── macos.md
│   │   ├── linux.md
│   │   └── wsl.md
│   ├── troubleshooting.md
│   └── development.md
├── src/
│   └── meeting_recorder/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── recorder.py
│       │   ├── stream.py
│       │   ├── writer.py
│       │   ├── config.py
│       │   └── metadata.py
│       ├── platform/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── detector.py
│       │   ├── windows.py
│       │   ├── macos.py
│       │   ├── linux.py
│       │   └── wsl.py
│       ├── audio/
│       │   ├── __init__.py
│       │   ├── devices.py
│       │   ├── levels.py
│       │   └── utils.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── setup.py
│       │   ├── record.py
│       │   ├── config.py
│       │   └── display.py
│       └── ui/
│           └── jupyter/
│               ├── __init__.py
│               └── widget.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── scripts/
    ├── wsl_pulseaudio_setup.sh
    └── dev_setup.sh
```

### Module Responsibilities

The source code is organized into logical groupings that separate concerns and facilitate maintenance.

#### Core Module

The core module contains the fundamental recording logic that is platform-agnostic. The recorder.py file implements the main RecordingSession class that coordinates simultaneous capture from multiple streams, manages the lifecycle of recording, and handles graceful shutdown. The stream.py file defines the Stream class representing a single audio input stream with its callback mechanism and queue-based buffering. The writer.py file provides thread-safe file writing that drains audio queues and writes WAV files without blocking capture threads.

The config.py file manages configuration loading, saving, validation, and merging of defaults with user preferences. The metadata.py file generates and writes JSON metadata files containing session information, device details, and timestamps.

#### Platform Module

The platform module encapsulates all operating system-specific audio system interactions. The base.py file defines abstract base classes that specify the interface all platform implementations must provide, including device enumeration, system audio availability checking, and stream creation. The detector.py file identifies the current platform (Windows, macOS, Linux, WSL) and instantiates the appropriate platform implementation.

Platform-specific modules (windows.py, macos.py, linux.py, wsl.py) implement the base interface for their respective platforms. These modules handle the unique APIs and configuration required for each system: PyAudioWPatch and WASAPI on Windows, BlackHole detection and guidance on macOS, PulseAudio monitor sources on Linux, and PulseAudio forwarding setup on WSL.

#### Audio Module

The audio module provides utilities for working with audio data and devices. The devices.py file wraps sounddevice device enumeration with helper functions for filtering, matching device fingerprints, and presenting user-friendly device information. The levels.py file implements audio level calculation (RMS and peak), dB conversion, and threshold detection for visual metering. The utils.py file contains general audio utility functions for sample rate handling, buffer size calculation, and format conversions.

#### CLI Module

The CLI module implements the command-line interface using Typer and Rich. The app.py file defines the main Typer application with command routing and global options. The setup.py file implements the interactive setup wizard that guides users through initial configuration with device selection, test recording, and config generation. The record.py file contains the record command implementation including recording session management, display updates, and signal handling.

The config.py file provides configuration management commands (show, edit, validate, test) and the display.py file implements Rich-based UI components including level meters, status displays, progress indicators, and panels.

#### UI Module (Optional)

The UI module contains optional interfaces beyond the core CLI. The jupyter subpackage implements ipywidgets-based recording controls for use in Jupyter notebooks, with device dropdowns, file path selection, start/stop buttons, and live waveform displays.

**RESOLVED: Jupyter UI Distribution Strategy**

The Jupyter interface will be implemented as an **optional dependency** using the `meeting-recorder[jupyter]` package extra. This approach:
- Keeps the core package lightweight for CLI-only users
- Follows Python packaging best practices for optional features
- Defers other UI approaches (web interface, system tray) to future version 2.0

**Implementation:** Phase 9 or later, after core CLI functionality is stable.

## Platform-Specific Implementation

Each supported platform has unique characteristics that require tailored approaches to system audio capture. This section details the specific strategies and challenges for each target platform.

### Windows Native

Windows native implementation uses the Windows Audio Session API (WASAPI) loopback feature to capture system audio. WASAPI loopback allows applications to capture the mixed audio output that is sent to the default playback device, which includes all application audio except the recording application itself. This is exactly the desired behavior for meeting recording: capturing other participants' audio without creating feedback loops.

The implementation relies on PyAudioWPatch, a fork of PyAudio that includes Windows-specific patches for WASAPI support. Device enumeration must specifically identify loopback devices, which appear as separate entries from standard input devices. The setup wizard guides users to select the appropriate loopback device corresponding to their default audio output.

One challenge is that loopback devices in WASAPI are tied to specific audio endpoints. If a user switches output devices (e.g., from speakers to headphones), the loopback device also changes. The system should detect this condition and either prompt for reconfiguration or automatically adapt if the new device can be reliably identified.

Windows also offers an older "Stereo Mix" feature on some hardware, which can serve as a fallback. However, Stereo Mix is often disabled by default and availability varies by audio driver and hardware manufacturer. The platform module should detect both WASAPI loopback and Stereo Mix, preferring the former for its superior reliability and quality.

**RESOLVED: Windows Permissions and Compatibility**

**Permissions:** WASAPI loopback capture does **not require elevation** for standard loopback devices. The system assumes no elevation is needed but will document cases where specific drivers or hardware may require elevated permissions.

**Windows Compatibility:** The system will support both Windows 10 and Windows 11 with identical WASAPI behavior assumed. Any version-specific differences will be documented during testing phases.

### macOS

macOS does not provide built-in system audio capture capabilities due to security and privacy design decisions by Apple. Applications cannot directly access the mixed audio output without installing additional software. The standard approach is to use a virtual audio driver like BlackHole, which creates a virtual audio device that applications can route through.

The setup process requires users to: download and install BlackHole from its official source, configure their audio output to route through BlackHole using the Audio MIDI Setup utility or a multi-output device, and select BlackHole as the desktop audio input device in Meeting Recorder's configuration. This is a one-time setup, but it requires clear documentation and potentially in-app guidance.

The platform module for macOS focuses on detection rather than direct integration. It checks whether BlackHole (or similar virtual drivers like Loopback or Soundflower) is installed and available. If not detected, it provides clear instructions with links to installation resources. Once BlackHole is set up, the recording process is straightforward: it appears as a standard input device to sounddevice.

One consideration is whether to recommend specific multi-output device configurations versus simpler routing approaches. The trade-off is between user convenience (simpler) and audio quality/latency (more complex configurations can optimize these). Initial documentation should present the simplest working approach.

**RESOLVED: macOS Security Requirements and Virtual Driver Strategy**

**Security Requirements:** BlackHole installation may require granting microphone access to the terminal/Python process on Big Sur and later. A system restart may also be required after BlackHole installation.

**Virtual Driver Strategy:** The system will **standardize on BlackHole** as the recommended virtual audio driver. This simplifies documentation and support while providing a reliable, actively-maintained solution.

**Documentation:** Installation guides will include detailed BlackHole setup instructions with security permission steps clearly outlined.

### Windows Subsystem for Linux

WSL presents a unique challenge because it is a Linux environment running atop Windows, but without direct access to Windows audio hardware. Audio in WSL works through forwarding mechanisms that vary by WSL version and Windows build. The most common approach is PulseAudio forwarding, where a PulseAudio server runs on the Windows host and WSL clients connect to it.

Recent versions of WSL2 include WSLg (Windows Subsystem for Linux GUI), which bundles a PulseAudio server and handles audio forwarding automatically for many applications. However, this primarily targets audio output rather than input, and system audio capture specifically may require additional configuration.

The implementation strategy for WSL involves: detecting that the code is running in a WSL environment (checking for /proc/sys/fs/binfmt_misc/WSLInterop or similar), verifying PulseAudio connectivity to the Windows host, enumerating available audio sources through PulseAudio including the Windows system audio device if forwarded, and providing setup documentation for configuring PulseAudio forwarding if not automatically available.

The key challenge is the variability in WSL configurations. Some users may have older WSL1 installations, custom PulseAudio setups, or network configurations that affect audio forwarding. The platform module should gracefully handle these variations and provide diagnostic information to help users troubleshoot their specific setup.

As a fallback strategy, the system could detect WSL and suggest running the native Windows version of Meeting Recorder on the host system, with output files written to a shared directory accessible from both environments. This would allow development to occur in WSL while recording happens in the Windows environment with full audio access.

**RESOLVED: WSL Support Scope and Fallback Strategy**

**Minimum Support:** WSL2 with WSLg is the minimum supported version. WSL1 support will not be pursued due to audio complexity.

**Contingency Plan:** Phase 6 complexity will be tightly scoped. If PulseAudio forwarding proves too unreliable during testing, the phase will be marked as "best-effort/experimental" and development resources will pivot to polish or other features.

**Fallback Documentation:** Native Windows execution with shared directory access will be documented as the highly reliable alternative for WSL users.

## User Interface Design

The command-line interface serves as the primary interaction point for users. It balances simplicity for common tasks with flexibility for advanced configuration.

### Command-Line Interface

The CLI is built using Typer for command structure and argument parsing, with Rich providing enhanced terminal output. The main commands follow a natural workflow:

**meeting-recorder setup**: Launches an interactive wizard for first-time configuration. This command walks users through platform detection, device enumeration and selection, test recording to verify functionality, and configuration file creation. The wizard uses smart defaults to minimize user input while ensuring all critical settings are configured.

**meeting-recorder record**: Starts a recording session using the current configuration. This is the primary command users interact with regularly. Optional flags allow overriding config settings for one-off variations (e.g., different output directory).

**meeting-recorder status**: Displays health check information including detected platform, device availability, configuration validity, and recommendations for fixing any issues. This command is crucial for diagnosing problems without requiring users to parse log files.

**meeting-recorder config**: Provides subcommands for configuration management including show (display current config), edit (open config file in editor), validate (check config for errors), and test (perform a short test recording).

All commands support a --verbose flag that enables detailed logging output, which is essential for troubleshooting user issues remotely.

### Setup Wizard

The setup wizard provides a guided experience for first-time configuration. It runs automatically if no configuration exists when the user attempts to record, but can also be invoked explicitly with the setup command.

The wizard flow consists of: platform detection and capability checking, explaining any platform-specific requirements (e.g., BlackHole on macOS), enumerating available audio devices with clear descriptions, prompting for microphone device selection with smart default (system default microphone), prompting for desktop audio device selection (loopback device on Windows, BlackHole on macOS, monitor source on Linux), running a three-second test recording to verify both devices work, checking that test recordings contain audio (not silent), presenting the generated configuration for review, and saving configuration to the appropriate platform directory.

The wizard uses Rich panels and prompts to present information clearly. Device selection menus display device names along with additional context like sample rate and channel count. If system audio capture is not available (e.g., BlackHole not installed on macOS), the wizard provides clear instructions with links and offers to proceed with microphone-only configuration as a fallback.

**RESOLVED: Setup Wizard Text and Documentation Policy**

**Text Guidelines:** Wizard prompts will use **clear, user-friendly, non-condescending language**. Text will be professional and helpful without being overly technical.

**Documentation Links:** The wizard will **display URLs only** and will not automatically open browsers. This respects the terminal environment and user preference for handling links.

### Recording Display

During active recording, the CLI displays a live-updating interface using Rich's Live display functionality. The interface is divided into sections:

**Audio level meters**: Two horizontal bar graphs showing real-time audio levels for microphone and desktop audio. Bars use color coding: yellow for too-quiet audio (below -40 dB), green for ideal levels (-20 to -6 dB), and red for clipping risk (above -3 dB). The bars update at 10 Hz by default, configurable for different refresh rates.

**Recording status**: Displays elapsed time in MM:SS format, current file sizes for both audio files, output directory path, and clear instruction for stopping ("Press Ctrl+C to stop and save").

**Warnings and alerts**: If audio levels are consistently too low or clipping is detected, persistent warnings appear to alert the user. If a stream encounters an error, an alert appears with basic diagnostic information.

The display layout is compact, fitting comfortably in a standard terminal window without requiring scrolling. All elements update smoothly without flicker, using Rich's efficient rendering. When recording stops (via Ctrl+C or other signals), the display shows a final summary including total duration, final file sizes, output location, and confirmation that files were saved successfully.

### Configuration Management Commands

Beyond the setup wizard, users may need to inspect or modify their configuration. The config subcommands provide these capabilities:

**meeting-recorder config show**: Displays the current configuration in a formatted, human-readable manner using Rich syntax highlighting. Includes the config file location and timestamp of last modification.

**meeting-recorder config edit**: Opens the configuration file in the user's default editor (respecting $EDITOR environment variable, falling back to platform defaults like notepad on Windows, nano on Linux). After editing, automatically validates the modified config and reports any errors.

**meeting-recorder config validate**: Checks the current configuration for validity including required fields, device fingerprint matching to available devices, output directory existence and writability, and sample rate compatibility. Reports specific errors with suggestions for fixes.

**meeting-recorder config test**: Performs a three-second test recording using the current configuration, verifies that output files are created and contain audio, displays basic statistics (file sizes, audio levels), and confirms configuration is working correctly.

These commands allow users to diagnose and fix configuration issues without re-running the full setup wizard.

## Audio Processing Details

This section covers the technical details of audio capture, processing, and storage that underpin the recording functionality.

### Device Detection and Enumeration

Audio device detection builds on sounddevice's query_devices() function, which returns information about all available audio devices including input devices, output devices, and loopback/monitor devices. The wrapper layer in audio/devices.py adds several enhancements:

**Device filtering**: Separates input devices from output and loopback devices, filters to only devices with appropriate channel counts (mono or stereo for microphone, typically stereo for desktop audio), and identifies platform-specific special device types (WASAPI loopback on Windows, monitor sources on Linux).

**Device fingerprinting**: Generates stable identifiers for devices based on properties less likely to change than simple names or indices. The fingerprint might combine device name, host API, max input channels, and default sample rate. This allows configuration to survive device index reassignment that can occur when USB devices are plugged/unplugged in different orders.

**User-friendly presentation**: Formats device information for display to users with clear descriptions that include the device name, host API (e.g., "Windows WASAPI", "Core Audio"), sample rate and channel configuration, and indication if it's the system default device.

The enumeration process also detects when expected devices from the configuration are not currently available and provides helpful messages suggesting possible causes (device unplugged, disabled in system settings, wrong platform).

### Level Metering

Audio level metering serves two purposes: providing visual feedback during recording and detecting audio issues like clipping or dead silence. The implementation in audio/levels.py calculates levels from audio buffers using two methods:

**RMS (Root Mean Square)**: Measures the perceived loudness of audio by calculating the square root of the mean of the squared samples. This is converted to decibels (dB) for standard audio level representation. RMS is the default metering mode because it corresponds well to how humans perceive loudness and is appropriate for speech audio.

**Peak**: Identifies the maximum absolute amplitude in the buffer. Peak metering is more sensitive to transient sounds and better for detecting clipping. When converted to dB, peak levels indicate how close audio is to digital full scale (0 dB).

Level calculations occur in the audio callback threads with minimal overhead. Each callback calculates the level for its buffer and places the result in a small, bounded queue (maxsize=2) to prevent memory growth if the display thread falls behind. The display thread reads from these queues and updates the visual meters.

Thresholds for color coding are: below -40 dB is yellow (too quiet), -40 to -20 dB is transitioning to green, -20 to -6 dB is green (ideal), -6 to -3 dB is transitioning to red, above -3 dB is red (clipping risk). These thresholds are configurable in the settings for users with different needs.

**RESOLVED: Automatic Gain Control Strategy**

**Decision:** **Defer AGC and level normalization to Post-MVP.** Automatic gain control complicates transcription and introduces potential quality issues.

**Alternative Approach:** Focus on providing excellent visual level metering and clear warnings to help users manually adjust levels. This maintains audio fidelity while giving users the information they need.

### Timestamp Synchronization

Accurate timestamp synchronization between microphone and desktop audio streams is essential for the transcription system to correctly align who said what. The approach relies on system time rather than attempting sample-accurate synchronization, which is sufficient given the latency tolerance of the transcription use case.

Each stream records a start timestamp when capture begins using high-resolution system time (time.perf_counter() for relative timing, datetime.now() for absolute timestamps). The audio callback includes timing information from the audio subsystem, but the implementation primarily relies on system clock synchronization. Both streams start capture as close together in time as possible, launched from the same coordinating thread.

Metadata files record the start and stop timestamps for each stream along with the sample rate, allowing post-processing tools to calculate exact sample positions for any given time. If streams drift over long recordings (which can happen due to slight sample rate mismatches), the metadata provides enough information to detect and correct this drift.

For crash recovery or restart scenarios, the system records the wall-clock time when recording was interrupted and when it resumed. New audio files are created with their own start timestamps, and the metadata tracks these gaps so that transcription systems can handle discontinuities appropriately.

**RESOLVED: Timestamp Drift Strategy**

The system will **not implement periodic re-synchronization** during recording. Instead, it uses a simplified approach:

1. **High-Resolution Start/Stop Timestamps:** Use system clock (time.perf_counter() and datetime.now()) for precise start/stop timing
2. **Acceptable Drift Tolerance:** 50ms per hour is the maximum acceptable drift before post-processing correction is recommended
3. **Post-Processing Detection:** Drift detection and correction is deferred to post-processing based on known sample rates and timestamps
4. **Metadata Recording:** All necessary timing information is captured in metadata for downstream drift correction

This approach prioritizes recording reliability over real-time drift correction, which can introduce additional failure modes.

### File Writing Strategy

Audio data flows from capture callbacks to disk through a queuing and writing architecture designed to prevent data loss. Each stream has its own queue and writer thread, operating independently to maximize reliability.

The writer thread opens a WAV file at the start of recording and keeps the file handle open throughout the session. As audio buffers arrive in the queue, they are written sequentially to the file. The wave module handles WAV file structure, updating headers as needed. Critical operations like file handle opening and closing are protected with try-except blocks to ensure graceful error handling.

Buffer sizes and queue depths are tuned to balance memory usage against dropout protection. Larger queues can absorb temporary slowdowns in disk I/O, but consume more memory. The default configuration uses queue sizes of 100 buffers, which at typical buffer sizes (1024 samples at 48kHz = ~21ms per buffer) represents about 2 seconds of audio buffering.

When recording stops (either normally or via interrupt), the system ensures all queued audio is written before closing files. Writer threads drain their queues completely, and the main thread waits for writers to finish before exiting. This guarantees that all captured audio is saved even if the user interrupts recording.

For robustness, the system flushes file buffers periodically (every few seconds) rather than relying solely on close-time flushing. This means that even if the process is killed ungracefully, only the most recent few seconds of audio might be lost rather than the entire recording.

**RESOLVED: Buffer Size Strategy**

**Default Configuration:** Start with buffer_size: 1024 frames and queue_depth: 100 buffers as specified in the configuration schema.

**Testing Strategy:** Include buffer optimization as a specific testing focus in Phase 2/3. Test these values across varied hardware and adjust if needed.

**Adaptive Adjustment:** Automatic buffer size adjustment is **deferred to Post-MVP** to maintain simplicity during initial implementation.

## Configuration System

The configuration system balances ease of use with flexibility, allowing users to customize behavior while providing sensible defaults.

### Configuration Schema

Configuration files use YAML format for human readability and are structured with the following schema:

```yaml
version: "1.0"
platform: "windows"  # Auto-detected, stored for validation

devices:
  microphone:
    fingerprint: "abc123..."  # Stable device identifier
    name: "USB Microphone"    # Human-readable, for display
    native_sample_rate: 44100  # Device's native rate
  desktop:
    fingerprint: "def456..."
    name: "WASAPI Loopback"
    native_sample_rate: 48000  # Device's native rate

recording:
  output_directory: "~/Meetings"
  target_sample_rate: 48000    # All recordings resampled to this rate
  resample_quality: "high"     # Options: "fast", "medium", "high"
  buffer_size: 1024            # Frames per buffer
  queue_depth: 100             # Buffer queue size for each stream
  
metering:
  mode: "rms"  # or "peak"
  update_rate: 10  # Hz
  thresholds:
    too_quiet: -40  # dB
    ideal_min: -20
    ideal_max: -6
    clipping: -3

advanced:
  verbose_logging: false
  flush_interval: 5  # seconds
  drift_tolerance: 50  # Max acceptable ms drift per hour

# Metadata fields captured automatically during recording
metadata:
  session_fields:
    - "recording_start_time"     # ISO 8601 timestamp
    - "recording_end_time"       # ISO 8601 timestamp  
    - "session_duration_seconds" # Total duration
    - "platform_info"           # OS details
    - "package_version"          # meeting-recorder version
    - "python_version"           # Python interpreter version
  device_fields:
    - "device_fingerprints"      # Stable device identifiers
    - "device_display_names"     # Human-readable device names
    - "native_sample_rates"      # Device's original sample rates
    - "channel_counts"           # Number of channels per device
    - "audio_apis"              # Platform audio API used
  recording_fields:
    - "target_sample_rate"       # Final sample rate used
    - "buffer_configuration"     # Buffer sizes and queue depths
    - "file_paths"              # Relative paths to audio files
    - "file_sizes_bytes"        # Final file sizes
    - "peak_levels_db"          # Maximum audio levels recorded
```

**Configuration Schema Finalization:**

The schema above represents the complete configuration format for v1.0. All `__meta` placeholders have been resolved with concrete decisions. The configuration includes both user-configurable settings and automatic metadata capture specifications.

**Version Migration Strategy:** Simple schema version checking on startup. Incompatible versions halt with error message directing users to manual config editing. Automated migration is post-MVP to maintain simplicity.

### Default Behavior

In the absence of explicit configuration, the system uses the following defaults:

**Devices**: System default input device for microphone. First available loopback/monitor device for desktop audio (platform-specific detection).

**Sample rate**: 48000 Hz target sample rate with automatic resampling from device native rates (standard for professional audio, optimal for transcription).

**Buffer size**: 1024 frames (provides ~21ms buffers at 48kHz, balancing latency and stability).

**Output directory**: Platform-specific user documents folder (e.g., ~/Documents/Meetings on macOS/Linux, Documents\Meetings on Windows).

**Metering**: RMS mode with 10 Hz update rate and standard thresholds.

Defaults are chosen to work well for the primary use case (meeting recording) on most systems without requiring user adjustment. Users with specific needs can override through configuration.

### Device Fingerprinting

Device fingerprinting creates stable identifiers that survive certain system changes while still detecting when devices genuinely change. The fingerprint algorithm combines several device properties:

**Name**: The device name as reported by the audio API, normalized to remove variable portions like "USB Audio Device #2" → "USB Audio Device".

**Host API**: The audio API being used (e.g., "Windows WASAPI", "Core Audio").

**Channel count**: Maximum input channels for the device.

**Sample rate**: Default sample rate.

These properties are concatenated and hashed to create a short identifier (e.g., first 16 characters of SHA256 hash). The fingerprint aims to be stable across reboots and device reconnections while changing if the user switches to a fundamentally different device.

On startup, the system enumerates available devices and attempts to match stored fingerprints. If a match is found, that device is used. If no match is found, the user is prompted to rerun device selection. The system can also detect "close matches" (e.g., same device but different sample rate) and offer to update the configuration rather than requiring full reconfiguration.

**RESOLVED: Device Fingerprinting Testing Strategy**

**Testing Plan:** The fingerprinting algorithm will be validated during Phase 2/3 across different platforms and device types, including edge cases with identical devices.

**Robustness Approach:** The system will implement fallback heuristics for edge cases like multiple identical USB devices, potentially incorporating connection port information where available.

**Refinement:** The algorithm will be refined based on real-world testing, with the current approach serving as the starting point.

## Development and Testing Strategy

The development approach emphasizes rapid iteration to a working prototype followed by refinement and expansion. Testing is lightweight initially but becomes more rigorous as the codebase stabilizes.

### Phased Implementation Plan

Development proceeds in phases, each building on the previous and delivering a testable increment of functionality.

**Phase 0 - Foundation (Week 1)**: Establish project structure with pyproject.toml and directory layout. Implement platform detection logic. Create abstract base classes for platform modules. Implement basic configuration loading and saving with platformdirs. Create device enumeration wrapper around sounddevice. Validation: Can detect platform, list devices, create and load a config file.

**Phase 1 - Single Stream Recording (Week 2)**: Implement core recording session for one stream. Create stream class with callback and queue. Implement thread-safe WAV file writer. Build basic CLI using Typer to trigger recording. Generate metadata files. Validation: Can record microphone-only to WAV file on Windows native.

**Phase 2 - Dual Stream Recording (Week 2-3)**: Extend recorder to manage two simultaneous streams. Implement Windows platform module with WASAPI loopback. Coordinate parallel streams with synchronized start. Write separate WAV files for each stream. Validation: Can record mic + desktop audio simultaneously on Windows.

**Phase 3 - Rich Display (Week 3)**: Implement audio level calculation (RMS). Create Rich display components (level meters, status panel). Build live updating display with threading. Implement graceful Ctrl+C handling. Add progress indicators for duration and file size. Validation: Recording interface looks professional and updates smoothly.

**Phase 4 - Setup Wizard (Week 4)**: Build interactive device selection with Rich prompts. Implement test recording functionality. Add platform-specific guidance (e.g., WASAPI instructions). Generate configuration with smart defaults. Implement config validation. Create status command for health checking. Validation: New user can complete setup in under 5 minutes.

**Phase 5 - macOS Support (Week 5)**: Implement macOS platform module. Add BlackHole detection logic. Create macOS-specific setup documentation. Test on actual macOS hardware. Handle Core Audio device enumeration quirks. Validation: Full recording workflow works on macOS with BlackHole installed.

**Phase 6 - WSL Support (Week 6-7)**: Implement WSL detection in platform module. Create PulseAudio forwarding detection and configuration. Build WSL-specific setup script for PulseAudio. Test on WSL2 with and without WSLg. Document limitations and requirements. Consider fallback recommendations if audio forwarding is not available. Validation: Recording works on WSL with proper PulseAudio setup, or provides clear guidance.

**Phase 7 - Robustness (Week 8)**: Implement crash recovery with logging and timestamping. Add disk space monitoring and warnings. Handle device disconnection during recording. Clean up orphaned temporary files on startup. Add verbose logging mode with detailed diagnostics. Implement periodic file flushing for data safety. Validation: System handles edge cases gracefully without data loss.

**Phase 8 - Polish and Documentation (Week 9)**: Write comprehensive installation documentation for each platform. Create troubleshooting guide with common issues and solutions. Add helpful error messages throughout the application. Implement pre-flight recording tests. Polish CLI output and formatting. Create README with quick start examples. Validation: Beta tester can install and use successfully with documentation alone.

**Phase 9 - Package and Release (Week 10)**: Configure pyproject.toml for PyPI distribution. Test pip installation on clean systems for each platform. Set up project repository with CI basics (linting, type checking). Create release process documentation. Tag initial release version. Publish to PyPI. Validation: `pip install meeting-recorder` works on target platforms.

The phased approach allows for early testing of core functionality while deferring complexity like WSL support until the basic patterns are proven. Each phase delivers a testable increment that can be validated before moving forward.

### Updated Implementation Plan with Resolved Technical Decisions

**Phase 1/2 Integration Updates:**
- Implement 48000 Hz target sample rate with resampling logic from resolved sample rate strategy
- Include sample rate detection and resampling quality configuration options
- Build configuration schema v1.0 with all finalized metadata fields

**Phase 3 Enhancement:**
- Integrate prominent "🔴 RECORDING" status indicator per security requirements
- Implement terminal title updates for recording awareness
- Add optional audio confirmation beeps for recording start/stop

**Phase 4 Refinements:**
- Apply resolved setup wizard text guidelines (user-friendly, non-condescending)
- Implement URL display without auto-opening browsers
- Include legal disclaimer and consent guidance in setup process

**Phase 6 Contingency Execution:**
- Scope limited to WSL2 with WSLg minimum requirements per resolved WSL strategy
- Implement early exit to "experimental" status if complexity becomes unmanageable
- Provide clear native Windows fallback documentation

**Phase 7 Buffer Strategy:**
- Focus testing on buffer_size: 1024 and queue_depth: 100 defaults
- Validate timestamp drift tolerance of 50ms per hour
- Defer adaptive buffer adjustment to post-MVP

**Phase 8 Security Integration:**
- Include comprehensive legal disclaimer in all documentation
- Add security and privacy best practices guide
- Document consent and meeting etiquette recommendations

The updated plan maintains the original timeline while ensuring all resolved technical decisions are incorporated systematically throughout implementation.

### Testing Approach

Testing follows a pragmatic approach that prioritizes getting a working end-to-end system before investing heavily in test infrastructure. The initial focus is on manual testing and validation, with automated tests added as the design stabilizes.

**Manual testing and validation**: Each phase includes explicit validation criteria that must be verified manually before proceeding. This hands-on testing is essential for audio software where automated testing is challenging. The developer (you) will test on actual hardware across Windows, macOS, and WSL environments to catch platform-specific issues early.

**Tracer bullet methodology**: The implementation starts with the simplest path through the entire system (single stream on one platform) and progressively adds complexity. This approach reveals integration issues early and provides a working baseline to compare against when adding features. Each addition can be validated against the known-good baseline.

**Unit tests added post-MVP**: Once the core design is proven and interfaces stabilize, unit tests are added for critical logic including configuration parsing and validation, device fingerprinting algorithms, audio level calculations, metadata generation, and platform detection logic. These tests focus on pure functions and business logic rather than attempting to mock audio hardware.

**Integration tests for workflows**: After MVP, integration tests cover complete user workflows including setup wizard completing successfully, recording session creating valid files, configuration loading and device matching, and graceful shutdown saving files correctly. These tests may use recorded audio fixtures rather than real-time capture.

**Platform-specific test execution**: Full testing requires access to actual hardware on each platform. Virtual machines have limited audio capabilities and may not accurately represent real-world behavior. Testing plan includes: Windows native (primary development platform), macOS (secondary platform, requires physical hardware), WSL on Windows (testing PulseAudio forwarding). Linux native testing is deprioritized since WSL is the primary Linux use case.

**Continuous validation during development**: Throughout implementation, the working system is used for actual meeting recording to validate behavior under real-world conditions. This dogfooding approach catches issues that might not appear in short test recordings, such as memory leaks during long sessions or file system interactions over hours of recording.

The testing strategy acknowledges the reality that audio software is difficult to test automatically and that manual validation on real hardware is essential for quality. Automated tests are added where they provide clear value without impeding development velocity.

### Platform Testing Access

Testing requires access to specific hardware and software configurations for each target platform.

**Windows native**: Primary development occurs on Windows, either native or using the Windows host system when working in WSL. This provides direct access to WASAPI and allows testing of the most common use case. Multiple Windows machines or virtual machines may be used to test different audio hardware configurations.

**macOS**: Testing on macOS requires physical Apple hardware. Development includes access to a Mac for testing the macOS platform module and BlackHole integration. Testing should cover both Intel and Apple Silicon Macs if possible, though audio APIs should be consistent across architectures.

**WSL testing**: WSL testing occurs on the same Windows machines used for native testing, allowing easy comparison between native Windows behavior and WSL forwarding. Testing should include both WSL1 and WSL2 if possible, though WSL2 is the primary target. Different Windows versions (Windows 10 vs Windows 11) may have different WSL audio capabilities and should be tested.

**Linux native**: While not a primary target, basic Linux testing validates that the codebase remains portable and that the Linux platform module works. This can be done on physical Linux hardware or in virtual machines, though VM audio capabilities may be limited. The focus is on ensuring the code works on Linux without requiring extensive Linux-specific development.

Audio device testing includes built-in microphones and audio outputs, USB audio interfaces, Bluetooth headsets, and virtual audio devices (BlackHole, VoiceMeeter, etc.). Each device type may expose different quirks in the audio subsystems.

**RESOLVED: CI/CD Strategy**

**Approach:** **Focus on detailed manual testing checklists** for each release to handle platform-specific and audio hardware testing requirements.

**Traditional CI:** Use standard CI for linting, type checking, and unit tests of non-audio logic, but do not attempt to automate audio hardware testing.

**Manual Testing:** Comprehensive checklists will cover each platform and device type to ensure reliable releases.

## Documentation Requirements

Comprehensive documentation is essential for a tool that requires platform-specific setup and targets users across different technical skill levels.

### Installation Guides

Each platform requires its own installation guide that walks users through both the package installation and any platform-specific prerequisites. These guides are maintained as separate markdown files in the docs/installation directory.

**Windows installation guide** (windows.md): Covers installing Python if not already present, installing Meeting Recorder via pip, verifying that WASAPI loopback devices are available, and running the setup wizard. The guide explains how to identify loopback devices in the device list and confirms that most Windows systems should work without additional software. It includes troubleshooting steps for cases where loopback devices don't appear.

**macOS installation guide** (macos.md): Provides detailed instructions for installing Python via official installer or Homebrew, downloading and installing BlackHole virtual audio driver with step-by-step screenshots, configuring audio routing through Audio MIDI Setup or creating a multi-output device, installing Meeting Recorder via pip, and running the setup wizard. This guide requires the most detailed explanation due to the BlackHole requirement. It includes visual aids showing the Audio MIDI Setup configuration and emphasizes that this is a one-time setup.

**WSL installation guide** (wsl.md): Explains the prerequisites of having WSL2 installed (with preference for versions that include WSLg), covers installing Python within the WSL environment, documents PulseAudio forwarding setup including any required Windows-side PulseAudio server configuration, provides a setup script to automate PulseAudio configuration where possible, and includes extensive troubleshooting for common WSL audio issues. This guide acknowledges the complexity and provides clear diagnostic steps. It also includes the fallback option of running Meeting Recorder natively on Windows if WSL audio proves problematic.

**Linux installation guide** (linux.md): Covers installing Meeting Recorder via pip, verifying PulseAudio or PipeWire configuration, identifying monitor devices for system audio capture, and running the setup wizard. This guide is more straightforward than macOS or WSL but accounts for variations across distributions.

All installation guides include verification steps to confirm successful installation before attempting actual recording. They also link to the troubleshooting guide for common issues.

### Platform-Specific Setup

Beyond basic installation, some platforms require additional configuration that is documented separately.

**BlackHole configuration guide** (part of macos.md or separate): Provides detailed explanation of how BlackHole works and why it's necessary, walks through the Audio MIDI Setup configuration process with screenshots, explains multi-output device creation for users who want to hear their system audio, demonstrates how to verify BlackHole is working with a test recording, and addresses common issues like no audio routing through BlackHole or not hearing system audio after setup.

**PulseAudio forwarding for WSL** (part of wsl.md or separate): Explains the architecture of PulseAudio forwarding from Windows to WSL, provides configuration file examples for both Windows PulseAudio server and WSL client, includes a setup script that automates as much as possible, documents environment variables that need to be set, and explains how to verify PulseAudio connectivity before attempting to record.

**WASAPI troubleshooting** (part of windows.md): Addresses why loopback devices might not appear, explains the difference between WASAPI and legacy audio APIs, documents how to check if Stereo Mix is available as a fallback, and describes permission issues if they arise.

These platform-specific guides dive deep into the technical details while remaining accessible to users who may not be audio engineering experts.

### Troubleshooting

A comprehensive troubleshooting guide (troubleshooting.md) provides solutions to common issues organized by symptom.

**Device not detected issues**: Covers cases where expected devices don't appear in the device list, including connection problems, driver issues, and platform-specific detection logic. Provides diagnostic commands to list all audio devices and interpret the output.

**Silent recordings**: Addresses situations where recording completes but audio files contain silence or very low levels, including muted inputs, wrong device selected, audio routing misconfiguration, and level settings in system audio mixer.

**Crashes and errors during recording**: Provides guidance for diagnosing crashes including checking verbose logs, verifying disk space, confirming audio device stability, and identifying driver issues. Includes instructions for generating useful bug reports.

**Configuration issues**: Covers invalid configuration files, device fingerprint mismatches after system changes, and configuration migration when upgrading package versions.

**Platform-specific problems**: Separate sections for Windows WASAPI issues, macOS BlackHole problems, WSL PulseAudio connectivity, and Linux PulseAudio/PipeWire variations.

**Performance problems**: Addresses high CPU usage, memory leaks during long recordings, and buffer underruns causing audio dropouts.

Each troubleshooting entry follows a consistent format with symptom description, diagnostic steps to confirm the issue, and solution steps. Where possible, diagnostic commands are provided that users can run to gather information.

**RESOLVED: Troubleshooting Guide Development**

**Initial Content:** The troubleshooting guide will launch with coverage of predictable issues based on design analysis and platform knowledge.

**Iterative Expansion:** The guide will be expanded based on actual user issues discovered during testing and early adoption phases.

**Documentation Process:** Issues encountered during development phases will be systematically documented and added to the troubleshooting guide.

## Security and Privacy Considerations

This section addresses the security, privacy, and legal considerations that come with recording audio, especially in meeting contexts where other participants may be involved.

### Recording Indicators and User Awareness

**Visible Recording Status:** The Rich CLI display will include a **large, unmistakable "🔴 RECORDING"** status indicator that is prominently displayed at all times during active recording. This ensures users are always aware when recording is active.

**Terminal Title:** The application will update the terminal window title to include "RECORDING" status to provide additional visual confirmation, especially if the user switches away from the application.

**Audio Confirmation:** The system will provide audio confirmation (optional beep) when recording starts and stops, similar to professional recording equipment.

### Legal Compliance and Consent

**User Responsibility:** Meeting Recorder is designed for personal use where the user has appropriate authority to record. **Users are responsible for compliance with all local laws and consent requirements** for recording meetings or conversations.

**Documentation Disclaimer:** All installation guides and README files will include a prominent legal disclaimer section stating:
- Users must verify local laws regarding recording consent
- Users must obtain appropriate consent from all participants before recording
- The tool is for personal productivity and note-taking purposes
- Meeting Recorder developers assume no liability for misuse

**Meeting Platform Integration:** Users should be aware that some meeting platforms have their own recording features and policies. Using external recording tools may violate platform terms of service.

### Data Security and Privacy

**Local Storage Only:** All recordings are stored locally on the user's machine. No audio data is transmitted to external services or cloud storage by default.

**File Permissions:** Recording files are created with appropriate file permissions (user-readable only) to prevent accidental access by other system users.

**Metadata Privacy:** The metadata files contain only technical information necessary for transcription processing. No personally identifiable information beyond the user's system details is included.

**Secure Deletion:** Users should be educated on secure file deletion practices when disposing of sensitive recordings.

### Consent and Meeting Etiquette

**Best Practices Documentation:** The system documentation will include guidance on:
- How to appropriately request recording consent from meeting participants
- Professional disclosure practices for recording meetings
- Recommendations for informing participants about recording purposes
- Guidance on handling confidential or sensitive meeting content

**Notification Templates:** Documentation will provide example language for meeting invitations and verbal disclosures that users can adapt for their specific contexts.

## Remaining Gaps

This section identifies areas that require further discussion and decision-making before or during implementation. These gaps represent topics we have not yet addressed in sufficient detail.

### Sample Rate Handling and Resampling

**RESOLVED: Target Sample Rate Strategy**

The system will use a **single target sample rate of 48000 Hz** for all recordings, with automatic resampling when devices operate at different native rates. This decision is based on:

**Rationale:**
1. **Transcription Quality:** Most modern transcription systems perform optimally with consistent sample rates, and 48kHz provides high-quality speech capture without unnecessary overhead
2. **Timestamp Synchronization:** Using unified sample rates eliminates drift correction complexity and ensures accurate alignment between microphone and desktop audio streams
3. **Professional Standard:** 48kHz is the standard for professional audio and widely supported across all platforms and devices
4. **Future-Proofing:** Provides headroom for high-quality audio capture if needed for enhanced transcription models

**Implementation:**
- All recordings will be resampled to 48000 Hz if the device's native rate differs
- Resampling uses scipy.signal.resample or similar high-quality algorithm
- Configuration allows override of target sample rate for specialized use cases
- CPU overhead of resampling is acceptable given the speech audio use case

**Configuration Schema Addition:**
```yaml
recording:
  target_sample_rate: 48000  # Target rate for all recordings
  resample_quality: "high"   # Options: "fast", "medium", "high"
```

**Performance Impact:** Real-time resampling adds ~5-15% CPU overhead depending on quality setting, which is acceptable for the target use case of meeting recording.

### Buffer Size Tuning and Configuration

Buffer size affects stability versus latency (though latency doesn't matter for this use case). We need to determine: What is the optimal default buffer size for stability across different systems? Should buffer size be configurable or automatically determined? How do buffer sizes interact with sample rate choices? What is the memory footprint of different buffer size and queue depth combinations? Should the system adaptively adjust buffer sizes based on detected performance?

Testing on varied hardware will inform these decisions, but we should have a methodology for buffer size selection.

### Error Recovery and Crash Handling Details

We have outlined crash recovery conceptually but lack implementation details. Specific questions include: How exactly does the system detect that a stream has failed versus just receiving silence? What constitutes a recoverable error versus a fatal error requiring recording to stop? How many restart attempts should be made before giving up? What happens to timestamps and file naming when streams restart mid-recording? How does the metadata format represent gaps and restarts? Should the user be notified during recording when a stream fails and restarts?

These details significantly impact robustness and user experience during failures.

### Audio Format and Compression Options

We have defaulted to uncompressed WAV files. However: How large are typical meeting recordings (1 hour, 2 hours)? Does file size become a practical problem? Should we support compressed formats like FLAC or Opus for reduced storage? If compression is added, should it be real-time during capture or post-processing? How do compressed formats affect downstream transcription processing? What are the CPU implications of real-time compression?

Starting with WAV is correct for MVP, but we should understand when and how to add compression.

### Metadata Schema Completeness

The metadata JSON format needs more detailed specification including: Exact field names and types, versioning strategy for schema evolution, how to represent multi-file recordings (after crash/restart), whether to include audio fingerprints or checksums for integrity verification, platform-specific information that should be captured, and whether metadata should be extensible for user-defined fields.

The transcription system integration will inform what metadata is truly necessary.

### Multi-Monitor and Virtual Desktop Handling

Modern systems often have complex audio routing with multiple monitors, virtual desktops, and application-specific audio controls. Questions include: On Windows, how do we handle scenarios with multiple audio output devices and corresponding loopback devices? Should the system support capturing from multiple desktop audio sources simultaneously (post-MVP feature)? How do virtual desktop applications (Citrix, Remote Desktop) affect audio capture? What happens when users switch audio devices during a meeting?

These scenarios may reveal edge cases in device detection and configuration.

### Package Distribution and Dependency Management

We have not finalized packaging details including: Exact dependency specifications in pyproject.toml (pinned versions vs ranges), handling of platform-specific dependencies (PyAudioWPatch only on Windows), optional dependencies for Jupyter widgets, whether to publish wheels for specific platforms or source-only, and continuous integration setup for testing installations.

These details become important for reliable pip installation across platforms.

### Performance Benchmarking and Resource Usage

We lack specific performance targets and measurement strategies including: What is acceptable CPU usage during recording? How much RAM should the system consume for typical recordings? What disk I/O patterns occur and are they sustainable for hours-long recordings? Should we benchmark and optimize critical paths like level calculation and file writing? How does performance scale with longer recording sessions?

Establishing performance baselines helps identify regressions during development.

### Long-Running Recording Stability

Most testing will use short recordings, but the use case involves potentially multi-hour meetings. Questions include: Are there memory leaks that only appear over long durations? Do audio device drivers remain stable over hours of continuous capture? How do system sleep/wake cycles affect ongoing recordings? Should there be automatic checkpointing for very long recordings? What happens to recordings if the system runs out of disk space mid-recording?

Extended testing sessions will be necessary to validate long-running stability.

### Internationalization and Localization

The current design assumes English-language interfaces and documentation. Considerations include: Should error messages and CLI output support multiple languages? How do non-ASCII characters in device names and file paths get handled? Are there locale-specific issues with date/time formatting in filenames? Does the tool work correctly in regions with different decimal separators or number formats?

While internationalization may be post-MVP, ensuring Unicode-safe handling is important.

### Device Permission and Access Control

Different platforms have different permission models for audio access. Questions include: Does macOS require microphone permission grants to the terminal or Python interpreter? Are there Windows User Account Control (UAC) considerations? Do Linux systems require users to be in specific groups (audio group)? How should the tool handle denied permissions gracefully? Should the setup wizard include permission verification?

Permission issues can be a source of difficult-to-diagnose failures.

### Integration with Transcription Pipeline

While transcription is out of scope for the recorder itself, understanding the integration helps inform design. Considerations include: What audio format and quality does the transcription system require? Does the transcription system need specific metadata? Should the recorder provide any hooks or callbacks for integration? Will recordings be processed immediately or stored for batch processing? Are there file naming conventions that help downstream processing?

Coordinating with transcription requirements ensures the recorder produces optimal output.

### Version Compatibility and Upgrades

As the package evolves, version management becomes important including: How will configuration format changes be handled across versions? Should the tool detect and migrate old configs automatically? What is the backward compatibility policy for metadata formats? How should breaking changes be communicated to users? What is the deprecation process for old features or platforms?

Planning for evolution prevents paint-into-corner situations.

### Documentation Maintenance and Contribution

Documentation will need ongoing maintenance as platforms and dependencies evolve. Questions include: What is the process for updating docs when platform APIs change? Should there be community contribution guidelines for documentation? How will screenshots and visual aids be kept current? Should there be versioned documentation for different package releases?

Good documentation processes prevent docs from becoming stale and inaccurate.

### Alternative UI Approaches

We have focused on CLI and optional Jupyter widgets, but other interfaces might be valuable. Considerations include: Would a system tray application be useful for quick access to recording controls? Should there be a web-based UI for remote control or monitoring? Would integration with meeting software (Zoom, Teams plugins) make sense? Is there value in mobile device support for controlling recording?

These represent potential future directions that should be considered in the architecture even if not immediately implemented.
