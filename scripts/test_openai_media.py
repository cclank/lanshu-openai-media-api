#!/usr/bin/env python3
"""Offline protocol and credential-handling checks; never call OpenAI."""
import base64
import contextlib
from email import policy
from email.parser import BytesParser
import http.server
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest import mock
import urllib.parse
import wave

import openai_media as api

FAKE_KEY = "test-key-for-local-protocol-checks"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aCj8AAAAASUVORK5CYII=")


class Handler(http.server.BaseHTTPRequestHandler):
    requests = []
    mode = None

    def log_message(self, *args):
        pass

    def respond(self, status, body, extra=None):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("x-request-id", "req_local_fixture")
        for name, value in (extra or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.requests.append((self.path, dict(self.headers), body))
        if self.mode == "error":
            return self.respond(403, {"error": "Missing scopes: api.usage.read " + FAKE_KEY})
        if self.path.endswith("/images/generations"):
            return self.respond(200, {"data": [{"b64_json": base64.b64encode(PNG).decode()}],
                                      "usage": {"input_tokens": 3, "output_tokens": 5}})
        return self.respond(200, {"text": "" if self.mode == "empty" else "测试 OpenAI 语音转写。", "languages": ["zh"],
                                  "usage": {"type": "duration", "seconds": 0.25}})

    def do_GET(self):
        self.requests.append((self.path, dict(self.headers), b""))
        if self.mode == "redirect":
            return self.respond(302, {}, {"Location": "/stolen"})
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        amount = 0.00588 if query.get("page") else 0.00051
        suffix = "image, output" if query.get("page") else "text, input"
        row = {"project_id": "proj_local", "api_key_id": "key_local",
               "line_item": "gpt-image-2.5-sunburst " + suffix,
               "amount": {"currency": "usd", "value": amount}}
        start = int(query["start_time"][0]) // 86400 * 86400
        return self.respond(200, {"data": [{"start_time": start, "end_time": start + 86400,
                                             "results": [row, dict(row, api_key_id="different_key")]}],
                                  "has_more": not bool(query.get("page")),
                                  "next_page": "page2" if not query.get("page") else None})


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port) + "/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="openai-media-test-")
        self.folder = Path(self.directory.name)
        Handler.requests, Handler.mode = [], None
        self.real_client = api.Client

    def tearDown(self):
        self.directory.cleanup()

    def client(self, *args, **kwargs):
        return self.real_client(FAKE_KEY, timeout=5, transport="curl" if shutil.which("curl") else "urllib", base_url=self.base)

    def invoke(self, arguments):
        with mock.patch.object(api, "credential", return_value=(FAKE_KEY, "test")), mock.patch.object(api, "Client", side_effect=self.client):
            args = api.parser().parse_args(arguments)
            return {"image": api.image, "transcribe": api.transcribe, "costs": api.costs}[args.command](args)

    def audio(self):
        path = self.folder / "测试录音.wav"
        with wave.open(str(path), "wb") as stream:
            stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            stream.writeframes(b"\0\0" * 4000)
        return path

    def test_image_keeps_usage_and_request_id_without_base64_or_key(self):
        output = self.folder / "image.png"
        result = self.invoke(["image", "--prompt", "一只猫", "--out", str(output)])
        self.assertEqual(output.read_bytes(), PNG)
        record = json.loads(Path(result["metadata_path"]).read_text())
        self.assertEqual(record["usage"]["output_tokens"], 5)
        self.assertEqual(record["request_id"], "req_local_fixture")
        self.assertNotIn("b64_json", json.dumps(record))
        self.assertNotIn(FAKE_KEY, json.dumps(record))
        self.assertEqual(len(Handler.requests), 1)

    def test_existing_metadata_aborts_before_credentials_or_paid_request(self):
        output = self.folder / "image.png"
        api.metadata(output).write_text("existing")
        with mock.patch.object(api, "credential") as keys:
            with self.assertRaises(api.MediaError):
                api.image(api.parser().parse_args(["image", "--prompt", "cat", "--out", str(output)]))
            keys.assert_not_called()
        self.assertEqual(Handler.requests, [])

    def test_transcription_multipart_preserves_audio_and_language_hints(self):
        source, output = self.audio(), self.folder / "transcript.txt"
        result = self.invoke(["transcribe", "--input", str(source), "--out", str(output),
                              "--languages", "zh", "--languages", "en", "--keyword", "OpenAI"])
        self.assertIn("语音转写", output.read_text())
        request = Handler.requests[0]
        content_type = request[1]["Content-Type"]
        message = BytesParser(policy=policy.default).parsebytes(("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + request[2])
        fields = [(part.get_param("name", header="content-disposition"), part.get_payload(decode=True)) for part in message.iter_parts()]
        self.assertEqual([value for name, value in fields if name == "languages[]"], [b"zh", b"en"])
        self.assertNotIn("language", [name for name, _ in fields])
        self.assertEqual(next(value for name, value in fields if name == "file"), source.read_bytes())
        record = json.loads(Path(result["metadata_path"]).read_text())
        self.assertEqual(record["request"]["audio_duration_seconds"], 0.25)
        self.assertEqual(record["usage"]["seconds"], 0.25)

    def test_dry_run_neither_reads_credentials_nor_writes_files(self):
        with mock.patch.object(api, "credential") as keys:
            args = api.parser().parse_args(["image", "--prompt", "cat", "--out", str(self.folder / "new" / "image.png"), "--dry-run"])
            self.assertTrue(api.image(args)["dry_run"])
            keys.assert_not_called()
        self.assertFalse((self.folder / "new").exists())
        self.assertEqual(Handler.requests, [])

    def test_empty_transcript_is_explicit_and_not_retried(self):
        Handler.mode = "empty"
        result = self.invoke(["transcribe", "--input", str(self.audio()), "--out", str(self.folder / "empty.txt")])
        self.assertTrue(result["empty_transcript"])
        self.assertEqual(result["text"], "")
        self.assertEqual(len(Handler.requests), 1)

    def test_string_error_is_reported_and_secret_is_redacted(self):
        Handler.mode = "error"
        client = self.client()
        with self.assertRaises(api.MediaError) as caught:
            client.request("POST", "images/generations", payload={"model": "test"})
        self.assertEqual(caught.exception.details["http_status"], 403)
        self.assertIn("api.usage.read", caught.exception.details["api_error"])
        self.assertNotIn(FAKE_KEY, json.dumps(caught.exception.details))
        self.assertEqual(len(Handler.requests), 1)

    def test_post_network_failure_is_not_retried_but_get_can_retry(self):
        client = self.client()
        with mock.patch.object(client, "_curl", side_effect=api.MediaError("Disconnected")) as send:
            client.transport = "curl"
            with self.assertRaises(api.MediaError):
                client.request("POST", "images/generations", payload={})
            self.assertEqual(send.call_count, 1)
        with mock.patch.object(client, "_curl", side_effect=[api.MediaError("Disconnected"), (200, {}, b"{}")]) as send:
            client.request("GET", "models")
            self.assertEqual(send.call_count, 2)

    def test_redirect_does_not_forward_credentials(self):
        Handler.mode = "redirect"
        for transport in (["curl", "urllib"] if shutil.which("curl") else ["urllib"]):
            with self.assertRaises(api.MediaError) as caught:
                self.real_client(FAKE_KEY, timeout=5, transport=transport, base_url=self.base).request("GET", "models")
            self.assertEqual(caught.exception.details["http_status"], 302)
        self.assertFalse(any(path.startswith("/stolen") for path, _, _ in Handler.requests))

    def test_costs_sum_paginated_records_for_only_selected_key(self):
        result = self.invoke(["costs", "--date", "2026-10-29", "--timezone", "Asia/Taipei",
                              "--project-id", "proj_local", "--api-key-id", "key_local", "--model", "gpt-image-2.5-sunburst"])
        self.assertEqual(result["totals_by_currency"], {"usd": "0.00639"})
        self.assertFalse(result["single_request_attribution"])
        self.assertFalse(result["date_window_exact"])
        self.assertEqual(len(result["billing_lines"]), 2)
        self.assertEqual(len(Handler.requests), 2)

    def test_cost_model_filter_does_not_match_a_similarly_named_family(self):
        result = self.invoke(["costs", "--date", "2026-10-29", "--project-id", "proj_local",
                              "--api-key-id", "key_local", "--model", "gpt-image-2"])
        self.assertFalse(result["has_cost_records"])
        self.assertEqual(result["totals_by_currency"], {})

    def test_literal_env_does_not_execute_shell_commands(self):
        path, sentinel = self.folder / "credentials", self.folder / "should-not-exist"
        path.write_text('export OPENAI_API_KEY="$(touch ' + str(sentinel) + ')"\n')
        with self.assertRaises(api.MediaError):
            api.literal_env(path, ("OPENAI_API_KEY",))
        self.assertFalse(sentinel.exists())

    @unittest.skipUnless(os.name == "posix" and shutil.which("zsh"), "zsh is optional")
    def test_zsh_export_uses_private_pipe_and_discards_startup_output(self):
        (self.folder / ".zshrc").write_text('print "startup noise"\nexport OPENAI_ADMIN_KEY="' + FAKE_KEY + '"\n')
        capture = io.StringIO()
        with mock.patch.object(api.Path, "home", return_value=self.folder), mock.patch.dict(os.environ, {"ZDOTDIR": str(self.folder)}), contextlib.redirect_stdout(capture):
            self.assertEqual(api.shell_value("OPENAI_ADMIN_KEY"), FAKE_KEY)
        self.assertEqual(capture.getvalue(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
