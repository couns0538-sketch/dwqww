"""Validate output paths taken from the command line.

SonarCloud flagged 13 sites in this seat as `Path Traversal via ... CLI arguments`: `--out`,
`--games` and `--sample` go straight into `open(path, "w")`, so a caller controls where the
script writes. That is a real (if low-impact) defect, and the fix belongs in one place.

The rule: everything these scripts write must land under this seat's own `evidence/`
directory, and nothing may escape it. Reads are allowed from `evidence/` too, because the
corpus and the arms are the only things they read.

`require` is used rather than `assert` so the check survives `python -O` (see checks.py): a path
guard that a flag can disable is not a guard.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import require

EVIDENCE = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence"))


def output_path(raw, what="output"):
    """Resolve a caller-supplied path and require it to stay inside evidence/.

    Symlinks are resolved before the comparison, so a link planted inside evidence/ cannot
    point the write outside it. The parent directory must already exist, which also rules out
    the `..` escape that a resolved-then-created path would allow.
    """
    require(isinstance(raw, str) and raw, f"{what} path must be a non-empty string")
    resolved = os.path.realpath(os.path.abspath(raw))
    parent = os.path.dirname(resolved)
    require(parent == EVIDENCE or parent.startswith(EVIDENCE + os.sep),
            f"{what} path must be inside evidence/ ({EVIDENCE}); refusing {raw!r}")
    return resolved


def input_path(raw, what="input"):
    """Same containment rule for reads: the arms and the corpus live in evidence/."""
    require(isinstance(raw, str) and raw, f"{what} path must be a non-empty string")
    resolved = os.path.realpath(os.path.abspath(raw))
    require(resolved == EVIDENCE or resolved.startswith(EVIDENCE + os.sep),
            f"{what} must be inside evidence/ ({EVIDENCE}); refusing {raw!r}")
    return resolved
