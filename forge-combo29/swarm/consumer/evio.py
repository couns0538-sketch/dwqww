"""Read an evidence JSON file, transparently handling `.gz`.

The two 100-game records are stored gzipped (8.3 MB raw, 0.9 MB compressed) so the branch
stays reviewable.  Every script that reads them goes through this helper, so a reader never
has to remember which files are compressed.
"""
from __future__ import annotations

import gzip
import io
import json


def load_json(path: str):
    """Open `path`, or `path + '.gz'` if only the compressed form exists."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        with open(path + ".gz", "rb") as f:
            raw = gzip.decompress(f.read())
    else:
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
    return json.loads(raw)


def text_stream(path: str) -> io.TextIOBase:
    """Open a text file, or its `.gz` sibling."""
    try:
        return open(path)
    except FileNotFoundError:
        return io.TextIOWrapper(gzip.open(path + ".gz", "rb"))
