#!/usr/bin/env python3
"""Restore the exact saved Forge experiment archives and execution files.

Run from any directory: python3 tools/match/restore_hourly_artifacts.py
All transport chunks, reconstructed archives and extracted members are checked.
Existing differing files are never overwritten.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import zipfile


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"Archive path escapes destination: {relative}")
    return target


def write_verified(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Existing file differs; preserve and investigate: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as target:
        target.write(data)


def main() -> None:
    root = Path(__file__).resolve().parents[2] / "validation/hourly"
    manifest = json.loads((root / "ARTIFACTS.json").read_text())
    for archive in manifest["archives"]:
        blocks = []
        for part in archive["parts"]:
            data = base64.b64decode(safe_path(root, part["path"]).read_text().strip(), validate=True)
            if len(data) != part["decoded_bytes"] or sha(data) != part["sha256"]:
                raise ValueError(f"Transport chunk mismatch: {part['path']}")
            blocks.append(data)
        data = b"".join(blocks)
        if len(data) != archive["bytes"] or sha(data) != archive["sha256"]:
            raise ValueError(f"Archive mismatch: {archive['path']}")
        write_verified(safe_path(root, archive["path"]), data)
        destination = safe_path(root, archive["extract_root"])
        expected = {member["path"]: member for member in archive["members"]}
        with zipfile.ZipFile(io.BytesIO(data)) as source:
            if len(source.namelist()) != len(expected) or set(source.namelist()) != set(expected):
                raise ValueError("Unexpected or duplicate archive members")
            for name, entry in expected.items():
                member = source.read(name)
                if len(member) != entry["bytes"] or sha(member) != entry["sha256"]:
                    raise ValueError(f"Archive member mismatch: {name}")
                path = safe_path(destination, name)
                write_verified(path, member)
                if name.startswith("bin/"):
                    path.chmod(path.stat().st_mode | 0o111)
        print(f"Verified and restored {archive['path']}: {len(expected)} files")
    # The selected 10,000-position book is a frozen permutation of the tracked
    # source book. Reconstruct it exactly if the archive has not restored it.
    for protocol_path in root.glob("*/matches/tt-tag-sprt/protocol.json"):
        protocol = json.loads(protocol_path.read_text())
        selected = protocol_path.parent / "selected.epd"
        if selected.exists():
            if sha(selected.read_bytes()) != protocol["selected_sha256"]:
                raise ValueError("Existing selected opening file differs")
            continue
        repository = root.parents[1]
        original = repository / protocol["opening_source"]["relative_path"]
        if sha(original.read_bytes()) != protocol["opening_source"]["sha256"]:
            raise ValueError("Original opening book differs")
        positions = [" ".join(line.split()[:4]) for line in original.read_text().splitlines() if line.strip()]
        positions.sort(key=lambda fen: hashlib.sha256(f"{protocol['seed']}\n{fen}".encode("ascii")).digest())
        data = ("\n".join(positions) + "\n").encode("ascii")
        if sha(data) != protocol["selected_sha256"]:
            raise ValueError("Reconstructed opening permutation differs")
        write_verified(selected, data)
        print(f"Verified and restored {selected.relative_to(root)}")


if __name__ == "__main__":
    main()
