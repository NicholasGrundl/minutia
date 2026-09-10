---
state: draft
changelog:
  "2026-09-10": "Parked stub — captured from live-dogfooding observations after the
    cli-wizard-redesign wizard shipped its first working end-to-end run. Follow-up polish to the
    wizard TUI (progress + log surfacing), deferred out of the redesign so that feature can close."
---

# wizard-tui-progress-and-logs (parked)

## Executive Overview

Follow-up polish to the wizard TUI built in `cli-wizard-redesign`. The first working end-to-end
guided run proved the concept (staged progress + a live loguru tail + telemetry header), but
dogfooding a real ~28-min meeting on a local `medium.en` model surfaced rough edges in **how progress
and logs are shown**. This feature unifies progress reporting across the pipeline and turns the
wizard's log area into a proper scrollable history.

**Why:** the wizard works but reads as crude during the slow stages — the user can't always tell what
is happening, long log lines are clipped, and history scrolls out of reach. These are all
presentation/observability gaps, not pipeline-correctness issues.

**Where this sits:** strictly downstream of `cli-wizard-redesign` (the TUI, flows, and the
`_LoggingProgress` whisper hook already exist). This is the "make the live run legible" pass.

## Task Checklist

- [ ] **Long file paths in logs get clipped.** Log lines (and the wizard's log-tail rendering)
      truncate long absolute paths at the frame width, so the useful tail of the path is lost.
      Options: middle-ellipsize paths (keep the filename + leading anchor), shorten to
      `~`/cwd-relative, or wrap. Decide per surface (loguru file vs the TUI tail).
- [ ] **Unify the progress updater, then connect it to the TUI.** Whisper progress now goes through
      an ad-hoc `_LoggingProgress` that logs audio-position lines (`steps/audio_transcription.py`);
      that was the quick win. The real design: a **single progress abstraction** every slow step
      reports through (extract / transcribe / merge / summarize), which the TUI consumes directly to
      drive the bar + a per-stage detail line — instead of the wizard inferring progress from log
      text. Periodic, throttled updates; works for both the wizard and `run pipeline` (plain logs).
- [ ] **Retire / relocate the `EN` language tag.** The header's upper-right `EN · ● <stage>` line —
      the language tag is moot right now (not driving anything) and, if kept, belongs **with the
      waveform line**, not as its own telemetry row. Simplify the telemetry panel: drop the standalone
      language tag; if a language indicator returns later, associate it with the waveform (the icon).
- [ ] **Scrollable full-history log subwindow.** Today the wizard shows only a tail (last ~8 lines)
      and only within a single `run_staged_progress` call, so history is lost across phases. Replace
      the tail with a **scrollable log pane** that retains **all** loguru output across **all** phases
      of the run, so the user can scroll up to review everything that happened (model load,
      per-track transcribe progress, merge, summarize) — one continuous history for the whole run,
      not per-stage snippets.

## Details

### Observations (verbatim, from live dogfooding 2026-09-10)

> - filepaths in the logs are super long and get cut off
> - progress of the whisper model is not shown... takes a long time and id like to get some periodic
>   updates. we will need to unify the progress updater then connect to the TUI
> - the EN in the upper right is sorta moot, not needed at the moment and anyhow its better sent and
>   associated with the waveform line i think
> - we should keep all the loguru outputs into a scrollable subwindow in the TUI so we can see and
>   watch ALL the history across all phases by scrolling upwards

### Notes / context

- The `_LoggingProgress` whisper hook (swaps whisper's stderr tqdm for loguru audio-position lines)
  landed in `cli-wizard-redesign` as a stopgap — the "unify the progress updater" task is meant to
  replace it with a first-class progress channel shared by all steps.
- The current log tail is a `deque(maxlen=8)` fed by a temporary loguru sink inside
  `run_staged_progress` (`cli/wizard/tui.py`); it is created/removed per staged-progress call, which
  is exactly why history doesn't survive across phases. A scrollable pane implies a run-scoped sink +
  a scroll-capable rich renderable (or a Live region with a scroll offset + key handling).
- Keep cold-start discipline: none of this should pull heavy imports into the cheap command surfaces.

### Effort

Medium. Task-2 (unified progress) and task-4 (scrollable history) are the substantive ones and are
related (both want a run-scoped stream the TUI owns); tasks 1 and 3 are small polish.
