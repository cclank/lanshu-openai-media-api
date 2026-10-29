#!/usr/bin/env python3
"""Check local documentation links, locale coverage, and skill packaging metadata."""
import importlib.util
import json
from pathlib import Path
import re
import shlex
import urllib.parse

LOCALES = ("zh-CN", "ja", "ko", "fr", "ar", "tr")


def check(root):
    root = Path(root).resolve()
    expected = [root / "README.md"] + [root / "docs" / "i18n" / ("README." + locale + ".md") for locale in LOCALES]
    problems, links, examples = [], 0, 0
    for path in expected:
        if not path.is_file():
            problems.append("Missing locale document: " + str(path.relative_to(root)))
    documents = sorted(path for path in root.rglob("*.md")
                       if not {"dist", "build", ".git", ".venv", "venv"}.intersection(path.relative_to(root).parts))
    for path in documents:
        text = path.read_text(encoding="utf-8")
        if len(re.findall(r"^```", text, re.M)) % 2:
            problems.append("Unbalanced code fence: " + str(path.relative_to(root)))
        for target in re.findall(r"\]\(([^\s)]+)(?:\s+[^)]*)?\)", text):
            parsed = urllib.parse.urlsplit(target.strip("<>"))
            if parsed.scheme or target.startswith("#"):
                continue
            relative = urllib.parse.unquote(parsed.path)
            if not relative:
                continue
            links += 1
            destination = path.parent / relative
            if not destination.exists():
                problems.append("Broken link in " + str(path.relative_to(root)) + ": " + target)
        if re.search(r"sk-(?:proj|admin|svcacct)-[A-Za-z0-9_-]{16,}", text):
            problems.append("Possible credential in " + str(path.relative_to(root)))
    arabic = root / "docs" / "i18n" / "README.ar.md"
    if arabic.is_file():
        text = arabic.read_text(encoding="utf-8")
        if 'dir="rtl"' not in text or 'dir="ltr"' not in text:
            problems.append("Arabic documentation must mark RTL prose and LTR command blocks.")
    main = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    if "img.shields.io" not in main:
        problems.append("The primary README is missing its project badges.")
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    if "name: lanshu-openai-media-api\n" not in skill:
        problems.append("Skill identifier does not match the project.")
    interface = (root / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "$lanshu-openai-media-api" not in interface:
        problems.append("Agent invocation prompt has the wrong skill identifier.")
    if not (root / "LICENSE").is_file():
        problems.append("Missing license file.")
    spec = importlib.util.spec_from_file_location("media_catalog_check", root / "scripts" / "openai_media.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for document in expected:
        if not document.is_file():
            continue
        text = document.read_text(encoding="utf-8")
        for model in module.MODELS:
            if model["id"] not in text:
                problems.append("Missing model " + model["id"] + " in " + str(document.relative_to(root)))
        for locale in LOCALES:
            if "README." + locale + ".md" not in text:
                problems.append("Missing language navigation for " + locale + " in " + str(document.relative_to(root)))
        for block in re.findall(r"```bash\n(.*?)\n```", text, re.S):
            commands = block.replace(chr(92) + "\n", "").splitlines()
            for command in commands:
                if command.startswith("python3 scripts/openai_media.py "):
                    try:
                        module.parser().parse_args(shlex.split(command)[2:])
                        examples += 1
                    except (ValueError, SystemExit):
                        problems.append("Invalid CLI example in " + str(document.relative_to(root)))
    return {"ok": not problems, "readme_languages": 1 + len(LOCALES), "markdown_files": len(documents),
            "local_links_checked": links, "cli_examples_checked": examples, "problems": problems}


if __name__ == "__main__":
    result = check(Path(__file__).resolve().parents[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)
