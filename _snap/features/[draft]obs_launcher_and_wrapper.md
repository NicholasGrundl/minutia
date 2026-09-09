# Design Document: Local Screen & Audio Recorder CLI (MVP)

## 1. Overview

The Recorder CLI is a local-first command-line tool that orchestrates OBS Studio to record screen and audio capture. It controls recording operations programmatically over OBS WebSocket v5 and provides a live Terminal User Interface (TUI) for session management (start, pause, resume, stop). The generated media files are routed into a dedicated CLI workspace directory to serve as inputs for downstream audio transcription and note generation.

---

## 2. Goals & Non-Goals

### In Scope (MVP)

* Automatic detection and launch of the local OBS Studio process (minimized/background mode).
* Programmatic WebSocket connection via `obsws-python` over port `4455`.
* Dynamic configuration of the output directory to point to the CLI workspace (`~/.reccli/recordings/`).
* Interactive foreground TUI (`Rich` + `readchar`) displaying active duration, current status, and key controls.
* Handling recording lifecycle: **Start**, **Pause**, **Resume**, and **Stop/Finalize**.
* Clean exit handling (`SIGINT` / `Ctrl+C`) to ensure recording files are safely finalized without corruption.

### Out of Scope (MVP)

* Automated scene, source, or canvas layout creation (relies on manual user pre-configuration in OBS).
* Direct transcription execution (Whisper integration is handled in subsequent pipeline stages).
* Background daemon mode with multi-command dispatch (`reccli pause`, `reccli stop`).

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Terminal Shell                         │
│  [reccli record]                                            │
│        │                                                    │
│        ▼                                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    CLI Controller                     │  │
│  │  - Lifecycle State Machine                            │  │
│  │  - Keyboard Event Poller (Space, Enter, Ctrl+C)       │  │
│  │  - Rich Live Display (Timer, State Badge, File Info)   │  │
│  └──────────┬───────────────────────────────▲────────────┘  │
└─────────────┼───────────────────────────────┼───────────────┘
              │                               │
        Subprocess Exec                 Localhost:4455
        (if not active)                 WebSocket RPC
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        OBS Studio                           │
│  - Display Capture (Pre-configured)                         │
│  - Desktop Audio & Mic Capture (Pre-configured)             │
│  - Dynamic Output Path: ~/.reccli/recordings/               │
└─────────────────────────────────────────────────────────────┘

```

---

## 4. Lifecycle & State Machine

```
      [Launch CLI]
           │
           ▼
     [CONNECTING] ──(OBS Not Running)──► Spawn Subprocess & Poll
           │
     (WS Connected)
           │
           ▼
      [RECORDING] ◄──────(Space)──────┐
           │                          │
        (Space)                    (Resume)
           │                          │
           ▼                          │
       [PAUSED] ──────────────────────┘
           │
      (Enter / 'q')
           │
           ▼
       [STOPPED] ──► Output Path Captured ──► Ready for Processing

```

### State Definitions

* **`CONNECTING`**: Checks TCP port `4455`. If closed, launches the OBS binary and polls with exponential backoff until the WebSocket handshake succeeds.
* **`RECORDING`**: Sends `StartRecord` to OBS. Timer ticks upward; elapsed time is rendered in the TUI.
* **`PAUSED`**: Sends `PauseRecord` to OBS. Timer stops incrementing; UI updates state badge.
* **`STOPPED`**: Sends `StopRecord` to OBS. Receives the final absolute filesystem path to the generated recording and performs teardown.

---

## 5. Directory Structure & Key Files

```text
reccli/
├── pyproject.toml            # Poetry/pip project spec (dependencies: rich, readchar, obsws-python)
├── reccli/
│   ├── __init__.py
│   ├── main.py               # Entrypoint (Typer or Click)
│   ├── config.py             # Default paths, port settings, auth tokens
│   ├── obs/
│   │   ├── __init__.py
│   │   ├── client.py         # obsws-python wrapper and error handling
│   │   ├── process.py        # OS-specific binary locator and subprocess supervisor
│   │   └── state.py          # State machine enumerations
│   ├── ui/
│   │   └── tui.py            # Rich Live terminal renderer
│   └── storage/
│       └── workspace.py      # Directory bootstrap and artifact indexing

```

---

## 6. Terminal User Interface (TUI) Specification

The interface is driven by `rich.live.Live` with non-blocking key polling via `readchar`.

### Layout Mockup

```
╭──────────────────────────────────────────────────────────────╮
│  REC-CLI v0.1.0 • OBS Studio Controller                      │
│                                                              │
│  STATUS: ● RECORDING              ELAPSED: 00:04:21          │
│  OUTPUT: ~/.reccli/recordings/2026-09-09_07-53-53.mkv        │
│                                                              │
│  CONTROLS:                                                   │
│  [SPACE] Pause/Resume    [ENTER / Q] Stop & Save    [CTRL+C] Abort │
╰──────────────────────────────────────────────────────────────╯

```

### Control Bindings

| Key | Action | Target State | API Call |
| --- | --- | --- | --- |
| Space | Toggle Pause / Resume | `PAUSED` / `RECORDING` | `client.pause_record()` / `client.resume_record()` |
| Enter / q | Finalize Session | `STOPPED` | `client.stop_record()` |
| Ctrl + c | Emergency Abort | `STOPPED` (Exit) | Safe `client.stop_record()` execution prior to exit |

---

## 7. OBS Process & Communication Details

### Binary Detection

The subprocess supervisor detects common platform installations:

* **Windows**: `C:\Program Files\obs-studio\bin\64bit\obs64.exe` *(Crucial: must set `cwd="C:\\Program Files\\obs-studio\\bin\\64bit"` to prevent DLL load failures)*
* **macOS**: `/Applications/OBS.app/Contents/MacOS/OBS`
* **Linux**: `/usr/bin/obs` or binary resolved via `shutil.which("obs")`

### Launch Flags

When spawned via the CLI, OBS Studio runs detached:

```bash
obs --minimize-to-tray --disable-updater

```

### WebSocket Calls

* **Set Directory**: `client.set_record_directory(path="~/.reccli/recordings")` executed immediately post-connection.
* **Recording Operations**: `start_record()`, `pause_record()`, `resume_record()`, `stop_record()`.
* **Teardown**: The tool checks whether it spawned OBS or connected to an existing session. If spawned by the tool, it sends a SIGTERM or `client.broadcast_custom_event()` to close cleanly on exit if `--kill-obs` was passed.

---

## 8. Failure Modes & Edge Case Handling

1. **Abrupt Process Termination (`SIGINT`)**: A Python `signal.signal` handler intercepts `SIGINT`/`SIGTERM` to issue `stop_record()` before terminating, preventing unfinalized container streams.
2. **Container File Safety**: Documentation and CLI preflight will recommend **MKV** or **fragmented MP4** in OBS settings to avoid corrupted headers caused by sudden OS crashes.
3. **Slow OBS Initialization**: The client uses a 15-second polling loop with a 500ms sleep interval to wait for the OBS WebSocket thread to start accepting connections.