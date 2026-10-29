#!/usr/bin/env python3
"""OpenAI image generation, audio transcription and daily cost queries. Python 3.9+."""
from __future__ import annotations

import argparse
import base64
import datetime as dt
from decimal import Decimal
import json
import mimetypes
import os
from pathlib import Path
import re
import select
import shlex
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import wave
from zoneinfo import ZoneInfo

API_BASE = "https://api.openai.com/v1"
MODELS = [
    {"task": "image", "id": "gpt-image-2.5-sunburst", "default": True, "purpose": "Highest image quality"},
    {"task": "image", "id": "gpt-image-2.5-flare", "default": False, "purpose": "Fast everyday image generation"},
    {"task": "transcribe", "id": "gpt-transcribe", "default": True, "purpose": "Accurate audio-file transcription"},
]
SECRETS = set()


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        for secret in SECRETS:
            value = value.replace(secret, "[REDACTED]")
        return re.sub(r"sk-[A-Za-z0-9_*.-]{6,}", "[REDACTED]", value)
    return value


class MediaError(Exception):
    def __init__(self, message, **details):
        super().__init__(message)
        self.details = details


def literal_env(path, names):
    path = Path(path).expanduser()
    if not path.is_file():
        raise MediaError("Credential file was not found.", path=str(path))
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*(?:export\s+)?([A-Z_][A-Z_0-9]*)\s*=\s*(.*?)\s*$", line)
        if not match or match[1] not in names:
            continue
        try:
            parts = shlex.split(match[2], comments=True)
        except ValueError:
            raise MediaError("Unmatched quotes in credential assignment.", variable=match[1])
        if len(parts) == 1 and parts[0]:
            if "$" in parts[0] or "`" in parts[0]:
                raise MediaError("Credential file must use literal values.", variable=match[1])
            values[match[1]] = parts[0]
    return values


def shell_value(name):
    """Load an exported value through a private FD; never print shell startup output."""
    shell = shutil.which("zsh")
    if os.name != "posix" or not shell or not (Path.home() / ".zshrc").is_file():
        return None
    reader, writer = os.pipe()
    try:
        command = 'print -rn -- "${' + name + ':-}" >&' + str(writer)
        try:
            subprocess.run([shell, "-ic", command], pass_fds=(writer,), stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
        finally:
            os.close(writer)
            writer = None
        if not select.select([reader], [], [], 0)[0]:
            return None
        return os.read(reader, 16384).decode("utf-8").strip() or None
    finally:
        os.close(reader)
        if writer is not None:
            os.close(writer)


def credential(args, admin=False):
    names = ("OPENAI_ADMIN_KEY", "OPENAI_ADMIN_API_KEY") if admin else ("OPENAI_API_KEY",)
    if args.env_file:
        values = literal_env(args.env_file, names)
        key = next((values[name] for name in names if values.get(name)), None)
        source = "explicit_env_file"
    else:
        key = next((os.environ[name].strip() for name in names if os.environ.get(name, "").strip()), None)
        source = "process_environment"
        if not key and not args.no_shell_env:
            key = next((value for name in names if (value := shell_value(name))), None)
            source = "zshrc"
    if not key:
        raise MediaError("Configure the exported key locally, or pass --env-file.", required_variable=names[0])
    if "\n" in key or "\r" in key:
        raise MediaError("Credential contains a newline.", required_variable=names[0])
    SECRETS.add(key)
    return key, source


class Client:
    def __init__(self, key, timeout=300, transport="auto", base_url=API_BASE):
        self.key, self.timeout, self.base_url = key, timeout, base_url.rstrip("/")
        self.transport = "curl" if transport == "auto" and shutil.which("curl") else transport
        if self.transport == "auto":
            self.transport = "urllib"
        SECRETS.add(key)

    def _urllib(self, method, url, body, content_type):
        headers = {"Authorization": "Bearer " + self.key, "Accept": "application/json"}
        if content_type:
            headers["Content-Type"] = content_type
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=self.timeout) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as error:
            return error.code, dict(error.headers), error.read()
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise MediaError("Network request failed.", detail=redact(str(error)))

    def _curl(self, method, url, body, content_type):
        if not shutil.which("curl"):
            raise MediaError("curl is unavailable; use --transport urllib.")
        with tempfile.TemporaryDirectory(prefix="openai-media-") as directory:
            headers_path = Path(directory) / "headers"
            config = 'header = ' + json.dumps("Authorization: Bearer " + self.key) + '\nheader = "Accept: application/json"\n'
            if content_type:
                config += 'header = ' + json.dumps("Content-Type: " + content_type) + "\n"
            command = ["curl", "--disable", "--silent", "--show-error", "--http1.1", "--connect-timeout", "15",
                       "--max-time", str(self.timeout), "--request", method, "--url", url,
                       "--config", "-", "--dump-header", str(headers_path), "--write-out", "\n%{http_code}"]
            if body is not None:
                body_path = Path(directory) / "body"
                body_path.write_bytes(body)
                body_path.chmod(0o600)
                command.extend(["--data-binary", "@" + str(body_path)])
            try:
                response = subprocess.run(command, input=config.encode(), capture_output=True,
                                          timeout=self.timeout + 10, check=False)
            except (OSError, subprocess.TimeoutExpired) as error:
                raise MediaError("Network request failed.", detail=redact(str(error)))
            if response.returncode:
                raise MediaError("Network request failed.", curl_exit_code=response.returncode,
                                 detail=redact(response.stderr.decode("utf-8", errors="replace")))
            raw, separator, status = response.stdout.rpartition(b"\n")
            if not separator or not status.isdigit():
                raise MediaError("HTTP status was not returned.")
            headers = {}
            for line in headers_path.read_text(errors="replace").splitlines():
                if ":" in line:
                    name, value = line.split(":", 1)
                    headers[name.lower()] = value.strip()
            return int(status), headers, raw

    def request(self, method, endpoint, payload=None, body=None, content_type=None, params=()):
        url = self.base_url + "/" + endpoint.lstrip("/")
        if params:
            url += "?" + urllib.parse.urlencode(params)
        if payload is not None:
            body, content_type = json.dumps(payload, ensure_ascii=False).encode(), "application/json"
        started = time.monotonic()
        attempts = 2 if method == "GET" else 1
        for attempt in range(attempts):
            try:
                sender = self._curl if self.transport == "curl" else self._urllib
                status, headers, raw = sender(method, url, body, content_type)
                break
            except MediaError:
                if attempt + 1 == attempts:
                    raise
        headers = {key.lower(): value for key, value in headers.items()}
        request_id = headers.get("x-request-id")
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise MediaError("API returned non-JSON data.", http_status=status, request_id=request_id)
        if not 200 <= status < 300:
            error = data.get("error", data) if isinstance(data, dict) else data
            raise MediaError("OpenAI API request was rejected.", http_status=status, request_id=request_id, api_error=redact(error))
        if not isinstance(data, dict):
            raise MediaError("Unexpected API response shape.", request_id=request_id)
        return data, {"http_status": status, "request_id": request_id,
                      "elapsed_seconds": round(time.monotonic() - started, 3),
                      "organization_id": headers.get("openai-organization"), "project_id": headers.get("openai-project")}


def ensure_new(paths):
    for path in paths:
        if path.exists() or path.is_symlink():
            raise MediaError("Output already exists; choose a new filename before calling the API.", path=str(path))
        parent = path.parent
        while not parent.exists() and not parent.is_symlink():
            parent = parent.parent
        if not parent.is_dir() or not os.access(parent, os.W_OK):
            raise MediaError("Output parent is not a writable directory.", path=str(parent))


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(value)


def save_json(path, value):
    write_new(path, (json.dumps(redact(value), ensure_ascii=False, indent=2) + "\n").encode())


def metadata(path):
    return path.with_name(path.stem + ".metadata.json")


def validate_size(size):
    if size == "auto":
        return
    match = re.fullmatch(r"([1-9][0-9]*)x([1-9][0-9]*)", size)
    if not match:
        raise MediaError("Size must be auto or WIDTHxHEIGHT.")
    width, height = map(int, match.groups())
    if (width % 16 or height % 16 or max(width, height) > 3840
            or max(width, height) / min(width, height) > 3
            or not 655360 <= width * height <= 8294400):
        raise MediaError("Size is outside the current GPT Image limits.", size=size)


def make_record(task, model, request, response, http, source, outputs):
    return {"ok": True, "task": task, "model": model,
            "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "credentials_source": source, "request": request, "response": response,
            "usage": response.get("usage"), "outputs": [str(path) for path in outputs], **http}


def image(args):
    prompt = Path(args.prompt_file).expanduser().read_text() if args.prompt_file else args.prompt
    if not prompt or not prompt.strip():
        raise MediaError("Image prompt is empty.")
    if not args.model.startswith("gpt-image-"):
        raise MediaError("This helper supports GPT Image models.")
    validate_size(args.size)
    if not 1 <= args.n <= 10:
        raise MediaError("Image count must be between 1 and 10.")
    path = Path(args.out).expanduser().absolute()
    extensions = {"png": {".png"}, "jpeg": {".jpg", ".jpeg"}, "webp": {".webp"}}
    if path.suffix.lower() not in extensions[args.output_format]:
        raise MediaError("Output extension must match --output-format.")
    outputs = [path] if args.n == 1 else [path.with_name(path.stem + "-" + str(i) + path.suffix) for i in range(1, args.n + 1)]
    sidecar = metadata(path)
    ensure_new(outputs + [sidecar])
    payload = {"model": args.model, "prompt": prompt.strip(), "n": args.n, "size": args.size,
               "quality": args.quality, "output_format": args.output_format}
    if args.dry_run:
        return {"ok": True, "dry_run": True, "endpoint": "/images/generations", "request": payload,
                "outputs": [str(path) for path in outputs], "metadata_path": str(sidecar)}
    key, source = credential(args)
    response, http = Client(key, args.timeout, args.transport).request("POST", "images/generations", payload=payload)
    items = response.get("data", [])
    if len(items) != len(outputs):
        raise MediaError("Image count differs from request; do not retry automatically.", request_id=http["request_id"])
    decoded, summaries = [], []
    for item in items:
        if not item.get("b64_json"):
            raise MediaError("API returned no base64 image; do not fetch an unknown URL.", request_id=http["request_id"])
        try:
            raw = base64.b64decode(item["b64_json"], validate=True)
        except (ValueError, TypeError):
            raise MediaError("API returned invalid image encoding.", request_id=http["request_id"])
        valid = {"png": raw.startswith(b"\x89PNG\r\n\x1a\n"), "jpeg": raw.startswith(b"\xff\xd8"),
                 "webp": raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"}
        if not valid[args.output_format]:
            raise MediaError("Returned image format differs from requested format.", request_id=http["request_id"])
        summary = {name: value for name, value in item.items() if name not in ("b64_json", "url")}
        summary["bytes"] = len(raw)
        if args.output_format == "png" and len(raw) >= 24:
            summary["width"], summary["height"] = struct.unpack(">II", raw[16:24])
        decoded.append(raw)
        summaries.append(summary)
    response = {name: value for name, value in response.items() if name != "data"}
    response["data"] = summaries
    record = make_record("image", args.model, payload, response, http, source, outputs)
    for output, raw in zip(outputs, decoded):
        write_new(output, raw)
    save_json(sidecar, record)
    return {name: value for name, value in record.items() if name not in ("request", "response")} | {"metadata_path": str(sidecar)}


def audio_duration(path):
    try:
        with wave.open(str(path), "rb") as audio:
            return audio.getnframes() / audio.getframerate()
    except (wave.Error, EOFError):
        pass
    if shutil.which("ffprobe"):
        try:
            result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                     "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True,
                                    timeout=15, check=False)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    return None


def multipart(fields, path):
    boundary = "openai-media-" + uuid.uuid4().hex
    chunks = []
    for name, value in fields:
        chunks.append(("--" + boundary + '\r\nContent-Disposition: form-data; name="' + name
                       + '"\r\n\r\n' + str(value) + "\r\n").encode())
    filename = re.sub(r'["\r\n\\]', "_", path.name)
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    chunks.append(("--" + boundary + '\r\nContent-Disposition: form-data; name="file"; filename="'
                   + filename + '"\r\nContent-Type: ' + mime + "\r\n\r\n").encode())
    chunks.extend([path.read_bytes(), ("\r\n--" + boundary + "--\r\n").encode()])
    return b"".join(chunks), "multipart/form-data; boundary=" + boundary


def transcribe(args):
    path = Path(args.input).expanduser().absolute()
    if not path.is_file():
        raise MediaError("Input audio was not found.", path=str(path))
    output = Path(args.out).expanduser().absolute()
    if output.suffix.lower() != ".txt":
        raise MediaError("Use a .txt output; full API JSON is saved alongside it.")
    sidecar = metadata(output)
    ensure_new([output, sidecar])
    fields = [("model", args.model)]
    if args.prompt:
        fields.append(("prompt", args.prompt))
    if args.model == "gpt-transcribe" or args.model.startswith("gpt-transcribe-"):
        fields.extend(("languages[]", language) for language in args.languages)
        for keyword in args.keyword:
            if not keyword.strip() or any(char in keyword for char in "<>\r\n"):
                raise MediaError("Each keyword must be one nonempty line without angle brackets.")
            fields.append(("keywords[]", keyword))
    else:
        if args.keyword or len(args.languages) > 1:
            raise MediaError("Multiple language hints and keywords require GPT-Transcribe.")
        if args.languages:
            fields.append(("language", args.languages[0]))
    request = {"fields": fields, "input_path": str(path), "input_bytes": path.stat().st_size,
               "audio_duration_seconds": audio_duration(path)}
    if args.dry_run:
        return {"ok": True, "dry_run": True, "endpoint": "/audio/transcriptions", "request": request,
                "outputs": [str(output)], "metadata_path": str(sidecar)}
    key, source = credential(args)
    body, content_type = multipart(fields, path)
    response, http = Client(key, args.timeout, args.transport).request("POST", "audio/transcriptions", body=body, content_type=content_type)
    if not isinstance(response.get("text"), str):
        raise MediaError("API returned no transcript text.", request_id=http["request_id"])
    record = make_record("transcribe", args.model, request, response, http, source, [output])
    record["empty_transcript"] = not response["text"].strip()
    write_new(output, (response["text"].rstrip() + "\n").encode())
    save_json(sidecar, record)
    return {name: value for name, value in record.items() if name not in ("request", "response")} | {"metadata_path": str(sidecar), "text": response["text"]}


def costs(args):
    if args.api_key_id and args.key_name:
        raise MediaError("Choose --api-key-id or --key-name.")
    output = Path(args.out).expanduser().absolute() if args.out else None
    if output:
        ensure_new([output])
    try:
        day, timezone = dt.date.fromisoformat(args.date), ZoneInfo(args.timezone)
    except (ValueError, KeyError):
        raise MediaError("Use an ISO date and valid IANA timezone.")
    start = dt.datetime.combine(day, dt.time(), tzinfo=timezone)
    end = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(), tzinfo=timezone)
    key, source = credential(args, admin=True)
    client = Client(key, args.timeout, args.transport)
    key_id = args.api_key_id
    if args.key_name:
        entries, after = [], None
        for _ in range(30):
            params = [("limit", 100)] + ([("after", after)] if after else [])
            data, _ = client.request("GET", "organization/projects/" + urllib.parse.quote(args.project_id, safe="") + "/api_keys", params=params)
            entries.extend(data.get("data", []))
            if not data.get("has_more"):
                break
            if not data.get("data"):
                raise MediaError("Key pagination could not advance.")
            after = data["data"][-1]["id"]
        else:
            raise MediaError("Key lookup exceeded the pagination limit.")
        matching = [item for item in entries if item.get("name") == args.key_name]
        if len(matching) != 1:
            raise MediaError("Key name must identify exactly one key; use --api-key-id.", matches=len(matching))
        key_id = matching[0]["id"]
    params = [("start_time", int(start.timestamp())), ("end_time", int(end.timestamp())),
              ("project_ids", args.project_id), ("group_by", "line_item"), ("group_by", "api_key_id"), ("limit", 3)]
    if key_id:
        params.append(("api_key_ids", key_id))
    rows, page, requests, buckets = [], None, [], []
    for _ in range(30):
        data, http = client.request("GET", "organization/costs", params=params + ([("page", page)] if page else []))
        requests.append(http)
        for bucket in data.get("data", []):
            boundary = {name: bucket.get(name) for name in ("start_time", "end_time")}
            if boundary not in buckets:
                buckets.append(boundary)
            for item in bucket.get("results", []):
                if item.get("project_id") not in (None, args.project_id):
                    continue
                if key_id and item.get("api_key_id") != key_id:
                    continue
                if args.model and not re.search(r"(?<![a-z0-9.-])" + re.escape(args.model)
                                               + r"(?=$|[ ,]|-\d{4}-\d{2}-\d{2})",
                                               item.get("line_item") or "", re.I):
                    continue
                rows.append(item)
        if not data.get("has_more"):
            break
        next_page = data.get("next_page")
        if not next_page or next_page == page:
            raise MediaError("Cost pagination could not advance.")
        page = next_page
    else:
        raise MediaError("Cost query exceeded the pagination limit.")
    totals = {}
    for row in rows:
        amount = row.get("amount") or {}
        if amount.get("value") is not None:
            currency = amount.get("currency") or "unknown"
            totals[currency] = totals.get(currency, Decimal("0")) + Decimal(str(amount["value"]))
    result = {"ok": True, "task": "costs", "date": args.date, "timezone": args.timezone,
              "project_id": args.project_id, "api_key_id": key_id, "model_filter": args.model,
              "credentials_source": source, "aggregation": "daily", "single_request_attribution": False,
              "has_cost_records": bool(rows), "totals_by_currency": {currency: str(value) for currency, value in totals.items()},
              "billing_lines": rows, "http_requests": requests,
              "requested_start_time": int(start.timestamp()), "requested_end_time": int(end.timestamp()),
              "returned_daily_buckets": buckets,
              "date_window_exact": (all(bucket["start_time"] >= start.timestamp() and bucket["end_time"] <= end.timestamp()
                                        for bucket in buckets)
                                    if buckets and all(isinstance(bucket[name], (int, float))
                                                       for bucket in buckets for name in ("start_time", "end_time")) else None)}
    if output:
        save_json(output, result)
        result["output_path"] = str(output)
    return result


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("models", help="Show the curated models; no API request.")
    def common(command):
        command.add_argument("--env-file", help="Existing credential file; overrides environment.")
        command.add_argument("--no-shell-env", action="store_true")
        command.add_argument("--timeout", type=int, default=300)
        command.add_argument("--transport", choices=("auto", "curl", "urllib"), default="auto")
    gen = commands.add_parser("image", help="Generate images through the Image API.")
    common(gen)
    prompts = gen.add_mutually_exclusive_group(required=True)
    prompts.add_argument("--prompt")
    prompts.add_argument("--prompt-file")
    gen.add_argument("--model", default="gpt-image-2.5-sunburst")
    gen.add_argument("--size", default="1024x1024")
    gen.add_argument("--quality", choices=("low", "medium", "high", "xhigh", "max", "auto"), default="medium")
    gen.add_argument("--n", type=int, default=1)
    gen.add_argument("--output-format", choices=("png", "jpeg", "webp"), default="png")
    gen.add_argument("--out", required=True)
    gen.add_argument("--dry-run", action="store_true")
    asr = commands.add_parser("transcribe", help="Transcribe an audio/video file to UTF-8 text.")
    common(asr)
    asr.add_argument("--input", required=True)
    asr.add_argument("--out", required=True)
    asr.add_argument("--model", default="gpt-transcribe")
    asr.add_argument("--languages", action="append", default=[])
    asr.add_argument("--keyword", action="append", default=[])
    asr.add_argument("--prompt")
    asr.add_argument("--dry-run", action="store_true")
    billing = commands.add_parser("costs", help="Read daily cost records using an admin key.")
    common(billing)
    billing.add_argument("--date", required=True)
    billing.add_argument("--timezone", default="UTC")
    billing.add_argument("--project-id", required=True)
    billing.add_argument("--api-key-id")
    billing.add_argument("--key-name")
    billing.add_argument("--model")
    billing.add_argument("--out")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "models":
            result = {"ok": True, "catalog_verified_on": "2026-10-29", "models": MODELS}
        else:
            if args.timeout <= 0:
                raise MediaError("Timeout must be positive.")
            result = {"image": image, "transcribe": transcribe, "costs": costs}[args.command](args)
        print(json.dumps(redact(result), ensure_ascii=False))
        return 0
    except MediaError as error:
        print(json.dumps(redact({"ok": False, "error": str(error), **error.details}), ensure_ascii=False))
        return 1
    except (OSError, ValueError) as error:
        print(json.dumps(redact({"ok": False, "error": str(error), "error_type": type(error).__name__}), ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
