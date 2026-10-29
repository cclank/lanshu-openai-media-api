# API notes

Documentation checked: **2026-10-29**. Prices below are dated references, not a replacement for returned usage or billing records.

## Images

- Endpoint: `POST https://api.openai.com/v1/images/generations`.
- Sunburst emphasizes quality; Flare emphasizes speed for everyday images.
- Both support low, medium, high, xhigh, max, and auto quality.
- PNG, JPEG, and WebP responses are decoded from `data[].b64_json`. Other response metadata and the HTTP `x-request-id` are retained.
- Common sizes: 1024x1024, 1536x1024, and 1024x1536. Custom sizes use multiples of 16, an edge limit of 3840, aspect ratios from 1:3 to 3:1, and 655,360–8,294,400 pixels. Check current documentation for experimental high resolutions.
- GPT Image 2.5 token consumption cannot be inferred from the GPT Image 2 calculator or the resulting image's file size.
- Standard pricing reference: $5 per million text input tokens, $8 per million image input tokens, and $30 per million image output tokens.

## File transcription

- Endpoint: `POST https://api.openai.com/v1/audio/transcriptions` using multipart/form-data.
- GPT-Transcribe accepts file, model, and optional prompt, languages[], and keywords[].
- Each keyword is a relevant terminology hint, without a newline, `<`, or `>`.
- Common inputs include MP3, M4A, WAV, and WebM. Follow the current documented upload limits and actual API errors.
- Pricing reference: $0.0045 per minute, or an estimated $0.00225 for 30 seconds. API billing uses currency; no universal points conversion exists.
- Live microphone transcription is outside this CLI. Older Whisper and GPT-4o Transcribe variants are not in the curated catalog; check their protocol and retirement schedule when explicitly requested.

## Cost queries

- Endpoint: `GET /v1/organization/costs`. The credential needs usage-reading access; official examples use an organization admin key.
- `403 Missing scopes: api.usage.read` describes insufficient usage-reading permissions, not image permissions or an account balance.
- UTC daily buckets support project and API key filters plus line_item grouping. Match models against returned line items.
- A local calendar day can overlap multiple UTC buckets. Inspect returned_daily_buckets and date_window_exact; do not invent a prorated local-day total.
- Key names resolve through `GET /v1/organization/projects/{project_id}/api_keys`; ambiguous names require an explicit key ID.
- Empty or incomplete records do not establish a zero charge. Daily totals cannot establish a per-request amount when several requests or concurrent callers are involved. Never repeat a generation to recover a past bill.

## Official sources

- [Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst)
- [Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare)
- [Image generation API](https://developers.openai.com/api/reference/resources/images/methods/generate)
- [GPT-Transcribe](https://developers.openai.com/api/docs/models/gpt-transcribe)
- [Speech transcription guide](https://developers.openai.com/api/docs/guides/speech-to-text)
- [Pricing](https://developers.openai.com/api/docs/pricing)
- [Costs API](https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage/methods/costs)
