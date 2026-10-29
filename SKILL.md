---
name: lanshu-openai-media-api
description: Generate text and images and transcribe audio through the OpenAI API for agent automation. Use for explicit API requests with curated models, structured usage records, and related cost queries. Not for ordinary writing or image tasks without an API requirement, or live microphone sessions.
---

# Lanshu OpenAI Media API

Run the bundled Python CLI for direct OpenAI API work. Python 3.9+ is required. curl is preferred when available; the Python standard library is the fallback. No OpenAI SDK, browser, or computer use is required.

Replace `<skill-dir>` with this file's absolute parent directory. API execution results are JSON: `ok: true` on success, `ok: false` with error details on failure. Check the exit code before using outputs.

## Curated models

| Task | Model | Selection |
| --- | --- | --- |
| Everyday text and coding | `gpt-6.1-sol` | Text default; balanced capability and cost |
| Demanding reasoning and professional work | `gpt-6-astra` | Highest intelligence |
| Writing and revision | `gpt-6.1-terra` | Fast and efficient |
| Focused, high-volume tasks | `gpt-6-luna` | Fastest and most cost-effective |
| Image generation with a focus on quality | `gpt-image-2.5-sunburst` | Image default |
| Fast everyday image generation | `gpt-image-2.5-flare` | Fast drafts |
| Audio/video file transcription | `gpt-transcribe` | ASR default |

`python3 <skill-dir>/scripts/openai_media.py models` returns this catalog; add `--task text` to list only text models. Model references were checked on 2026-10-29. Preserve an explicitly requested model. If it is retired, check official documentation and report the result rather than silently switching models.

## Credentials

- Text generation, image generation, and transcription use `OPENAI_API_KEY`.
- Cost queries use `OPENAI_ADMIN_KEY`, with `OPENAI_ADMIN_API_KEY` as an alias.
- Read the process environment first. If the export is absent, the helper can load `~/.zshrc` through a new `zsh -ic` process. Startup output is discarded; the value travels through a private memory pipe.
- `--env-file /absolute/path/existing.env` explicitly selects an existing literal-value credential file and overrides the corresponding environment variable. File contents are parsed as data, without executing them. `--no-shell-env` disables the zsh fallback.
- Keep credentials in the user's existing local environment. Never write keys into the skill, project files, logs, command arguments, or chat. The admin credential is used only for cost queries.
- A user's authorization to use an existing key continues throughout the current task. If that decision is unresolved, follow the host agent's credential authorization rules.

## Generate text

```bash
python3 <skill-dir>/scripts/openai_media.py text \
  --prompt "Summarize the benefits of automated transcription in three sentences." \
  --reasoning-effort low \
  --out /absolute/path/answer.txt
```

Defaults: `gpt-6.1-sol`, `medium` reasoning, and 4096 maximum output tokens. Choose Astra for demanding work, Terra for efficient writing, or Luna for fast focused tasks. Preserve an explicit model. Options include `--prompt-file` for UTF-8 input, `--instructions` for high-level guidance, `--reasoning-effort`, `--max-output-tokens`, and `--dry-run`.

Use `POST /v1/responses` with `store: false`. The output limit includes reasoning tokens. Sol and Astra reject `--reasoning-effort none` before a paid call; use `low` or higher. Collect all assistant `output_text` parts rather than assuming the first output item is text. The helper saves text and a sidecar with the response ID, returned model, status, usage, and HTTP request ID.

Incomplete responses, refusals, and empty text preserve their artifacts and usage, return `ok: false`, and exit with code 1. Inspect `response_status`, `incomplete_details`, `refusals`, and the saved metadata before deciding on a new authorized call; the helper does not retry automatically. No streaming, tools, or conversation-state continuation is implemented by this command.

## Generate an image

```bash
python3 <skill-dir>/scripts/openai_media.py image \
  --prompt "An orange cat on a sunny windowsill, natural photography, no text" \
  --out /absolute/path/cat.png
```

Use `--model gpt-image-2.5-flare --quality low` for fast drafts. Use `--quality high` for detailed results; `xhigh` and `max` are available when explicitly useful. Defaults: one 1024x1024 medium-quality PNG.

Options include `--prompt-file`, `--size`, `--quality`, `--n`, and `--output-format png|jpeg|webp`. Existing output images or metadata cause an error before a paid request; choose a fresh filename.

`--dry-run` displays the planned request without reading credentials, contacting the API, or creating files. After generation, inspect the actual image and display it using its absolute file path. Report the model and output locations.

## Transcribe an audio file

```bash
python3 <skill-dir>/scripts/openai_media.py transcribe \
  --input /absolute/path/recording.wav \
  --languages en \
  --out /absolute/path/transcript.txt
```

Repeat `--languages` for expected languages, such as `--languages zh --languages en`. Add relevant free-form context with `--prompt` and terminology with repeated `--keyword`. GPT-Transcribe uses plural `languages`; do not also send the legacy singular `language` field.

Outputs include UTF-8 text and the full API response metadata. `empty_transcript: true` explicitly marks an empty response; report it accurately without an automatic retry. WAV duration is available from the standard library, with optional ffprobe support for other formats. This CLI handles files, not live microphones, speaker diarization, or word timestamps.

Use files supplied by the user or already authorized for the task. Split oversized files according to current API limits and preserve ordering when combining transcripts.

## Usage, costs, and failures

Text, image, and transcription calls write `<output-stem>.metadata.json` with request parameters, HTTP status, request ID, returned usage, elapsed time, outputs, and response metadata. Credentials and image base64 are excluded.

Usage is distinct from monetary cost. For actual cost records:

```bash
python3 <skill-dir>/scripts/openai_media.py costs \
  --date 2026-10-29 --timezone UTC \
  --project-id YOUR_PROJECT_ID --key-name YOUR_KEY_NAME \
  --model gpt-image-2.5-sunburst
```

Use real project and key identifiers, and replace the example date with the relevant request date. `--api-key-id` can replace the key name; `--out /absolute/path/costs.json` saves the result.

Costs are daily UTC aggregates, even after filtering by project, key, and model. They are not receipts for individual request IDs. For non-UTC dates, returned buckets may overlap the requested local day; check `date_window_exact` and `returned_daily_buckets`. No records means costs have not been returned, not that the request was free. Read [references/api-notes.md](references/api-notes.md) for protocol and billing details.

POST requests are not automatically retried and models are not automatically changed. After a connection failure, inspect artifacts and metadata and consider that processing may already have been billed. GET requests retry a network error at most once. Preserve actual 401/403/429 errors and address their reported cause.
