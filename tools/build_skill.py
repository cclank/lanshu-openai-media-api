#!/usr/bin/env python3
"""Build a portable skill folder and ZIP from the repository's source files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

NAME = "lanshu-openai-media-api"
FILES = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/api-notes.md",
    "scripts/openai_media.py",
    "scripts/test_openai_media.py",
)


def build(output_dir, force=False):
    root = Path(__file__).resolve().parents[1]
    output_dir = Path(output_dir).expanduser().resolve()
    destination = output_dir / NAME
    archive = output_dir / (NAME + ".zip")
    manifest = output_dir / (NAME + ".manifest.json")
    if destination == root or destination in root.parents:
        raise ValueError("Refusing to replace the source repository.")
    for path in (destination, archive, manifest):
        if path.is_symlink():
            raise ValueError("Refusing to replace a symlink: " + str(path))
        if (path.exists() or path.is_symlink()) and not force:
            raise ValueError("Output exists; choose another directory or pass --force: " + str(path))
    for filename in FILES:
        if not (root / filename).is_file():
            raise ValueError("Missing skill source: " + filename)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".skill-build-", dir=str(output_dir)) as temporary:
        staged = Path(temporary) / NAME
        hashes = {}
        for filename in FILES:
            source, target = root / filename, staged / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            hashes[filename] = hashlib.sha256(target.read_bytes()).hexdigest()
        staged_archive = Path(temporary) / archive.name
        with zipfile.ZipFile(staged_archive, "x", compression=zipfile.ZIP_DEFLATED) as package:
            for filename in FILES:
                package.write(staged / filename, NAME + "/" + filename)
            if package.testzip() is not None:
                raise ValueError("ZIP verification failed.")
        if destination.is_symlink():
            raise ValueError("Refusing to replace a symlink: " + str(destination))
        if destination.exists():
            shutil.rmtree(destination)
        staged.rename(destination)
        staged_archive.replace(archive)
        data = {"skill": NAME, "files": hashes, "includes_credentials": False}
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "skill_directory": str(destination), "archive": str(archive), "manifest": str(manifest)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="dist")
    parser.add_argument("--force", action="store_true", help="Replace this command's named build outputs.")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output_dir, args.force), ensure_ascii=False))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
