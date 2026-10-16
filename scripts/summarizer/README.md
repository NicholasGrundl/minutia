# summarizer

Summarize a Whisper transcript (merged, desktop, or microphone JSON, or plain text)
with Claude on Amazon Bedrock, using a templated system prompt in `prompts/`.
The API key and region come only from a key file, never the environment.
Run `uv run summarize_bedrock.py --help` for all options.

## Examples

Check the prompt, transcript, and key file without calling the API:

```bash
uv run summarize_bedrock.py merged_transcript.json -k .claude/settings.local.json --dry-run
```

Summarize a merged transcript (Opus 5.5, default prompt `prompts/default.md`):

```bash
uv run summarize_bedrock.py merged_transcript.json -k .claude/settings.local.json
```

Set the audience and notes (inline text, or `@file` to read from a file):

```bash
uv run summarize_bedrock.py merged_transcript.json -k .claude/settings.local.json \
  --audience "Nick, consultant leading the solver project" \
  --notes @meeting_notes.md
```

Product stakeholder/user interview, with a Product focus file plus meeting notes
(`--notes` is repeatable; each file is labeled by name in the prompt):

```bash
uv run summarize_bedrock.py merged_transcript.json -k .claude/settings.local.json \
  -p prompts/product-interview.md \
  --audience "Nick, product engineering consultant" \
  -n @product_focus.md -n @meeting_notes.md
```

Single-track input with a custom speaker label, Sonnet, and a set output path:

```bash
uv run summarize_bedrock.py desktop-whisper-medium.en_transcription.json -k .env \
  --speaker "Client" -m sonnet -o summary.md
```

Use a different prompt template and region:

```bash
uv run summarize_bedrock.py merged_transcript.json -k .env \
  -p prompts/my_prompt.md --region us-west-2
```

## Key file

`-k` takes a Claude settings JSON (`env.AWS_BEARER_TOKEN_BEDROCK`, `env.AWS_REGION`)
or a `.env` / `.txt` / `.md` file with `KEY=value` lines:

```bash
AWS_BEARER_TOKEN_BEDROCK=<your-key>
AWS_REGION=us-east-1
```

To skip `-k` on repeat runs, set `DEFAULT_KEY_FILE` (an absolute path) at the top of
`summarize_bedrock.py`. Region order: `--region`, then the key file, then `us-east-1`.
