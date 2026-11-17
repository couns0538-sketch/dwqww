#!/usr/bin/env python3
"""Confine every path these scripts read or write to the evidence root.

WHY THIS EXISTS. Every script here takes its output (and sometimes its input) path
from the command line, which is a taint flow: an argument such as `--out ../../x`
would write outside the audit directory. SonarCloud flags 13 such lines as "Path
Traversal via command-line argument", and the finding is correct as a data-flow
statement even though these are local analysis scripts.

The fix is containment, not suppression: `under_root()` resolves a path and refuses
anything that escapes the evidence root, and `glob_under_root()` applies the same
rule to a glob pattern (resolving the pattern's non-wildcard parent, which is the part
that determines where the match can land). A rejected path raises rather than being
silently clipped, so a mistake is loud.

The root is `FORGE_EXPOSURE_ROOT` when set, otherwise the directory above `scripts/`.
"""
from __future__ import annotations

import fnmatch
import os

ROOT = os.environ.get(
    "FORGE_EXPOSURE_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)


def _root() -> str:
    return os.path.realpath(ROOT)


def under_root(path: str, *, must_exist: bool = False) -> str:
    """Return an absolute path that is guaranteed to sit inside the evidence root.

    A relative path is interpreted under the root, so `--out oracle.json` writes to
    `<root>/oracle.json` regardless of the current directory.
    """
    if not path:
        raise ValueError("empty path")
    candidate = path if os.path.isabs(path) else os.path.join(_root(), path)
    resolved = os.path.realpath(candidate)
    root = _root()
    if resolved != root and not resolved.startswith(root + os.sep):
        raise ValueError(f"path escapes the evidence root {root!r}: {path!r}")
    if must_exist and not os.path.exists(resolved):
        raise FileNotFoundError(resolved)
    return resolved


def glob_under_root(pattern: str) -> list[str]:
    """Expand a glob pattern, confined to the evidence root.

    `glob.glob` is deliberately NOT used on the caller's string: the pattern is
    caller-controlled, so handing it to the glob engine would keep tainted data in the
    filesystem call. Instead the pattern is split into a directory and a leaf, the
    DIRECTORY is sanitised through `under_root` (which returns a resolved absolute path
    proven to be inside the root), and the leaf is matched against the real directory
    listing with `fnmatch`. The caller's string never reaches a path-building call.
    """
    if not pattern:
        raise ValueError("empty pattern")
    leaf = os.path.basename(pattern)
    if not leaf:
        raise ValueError(f"pattern has no leaf component: {pattern!r}")
    parent_input = os.path.dirname(pattern) or "."
    parent = under_root(parent_input)
    if not os.path.isdir(parent):
        return []
    return [os.path.join(parent, name) for name in sorted(os.listdir(parent))
            if fnmatch.fnmatchcase(name, leaf)]


def _is_under(path: str) -> bool:
    resolved = os.path.realpath(path)
    root = _root()
    return resolved == root or resolved.startswith(root + os.sep)


def open_out(path: str):
    """Open a CLI-supplied output path for writing, confined to the root."""
    return open(under_root(path), "w")


def open_json_out(path: str):
    """`open_out` with an explicit encoding, for JSON evidence files."""
    return open(under_root(path), "w", encoding="utf-8")


def load_json(path: str) -> dict:
    """Load a CLI-supplied input path, confined to the root."""
    import json  # noqa: PLC0415 - tiny, keeps this module dependency-free

    with open(under_root(path, must_exist=True), encoding="utf-8") as fh:
        return json.load(fh)
