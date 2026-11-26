#!/usr/bin/env python3
"""Bump semver de un archivo de skill (Markdown) o de estado (JSON).

Uso:
    python scripts/bump_version.py skills/01_SKILL_PRODUCT_ANALYST.md --bump patch
    python scripts/bump_version.py data/state_memory.json --bump minor

Imprime SOLO la nueva versión (sin la 'v') para que pueda ser capturada por scripts.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

VERSION_RE = re.compile(r"(?<![\d.])(\d+)\.(\d+)\.(\d+)(?![\d.])")


def bump(version: str, part: str) -> str:
    major, minor, patch = (int(piece) for piece in version.split("."))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def update_text(path: Path, part: str) -> str:
    text = path.read_text(encoding="utf-8-sig")
    match = VERSION_RE.search(text)
    if not match:
        raise SystemExit(f"ERROR: version no encontrada en {path}")
    old = match.group(0)
    new = bump(old, part)
    path.write_text(text.replace(old, new), encoding="utf-8")
    return new


def update_json(path: Path, part: str) -> str:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    key = "project_version" if "project_version" in data else "version"
    old = str(data[key])
    data[key] = bump(old, part)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return data[key]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Archivo a versionar")
    parser.add_argument("--bump", choices=("patch", "minor", "major"), default="patch")
    args = parser.parse_args()
    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"ERROR: archivo no encontrado: {path}")
    result = update_json(path, args.bump) if path.suffix.lower() == ".json" \
        else update_text(path, args.bump)
    print(result)


if __name__ == "__main__":
    main()
