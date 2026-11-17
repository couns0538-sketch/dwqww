#!/usr/bin/env python3
"""Parse UCI output without trusting its shape.

Every script here reads engine output by position ("the token after `nodes`", "field 1 of the
bestmove line"). That is fine until a line is truncated, and then the failure is not an
exception at the point of the bug: a short `info` line yields a WRONG NUMBER, and a bail's
empty `pv` yields a wrong verdict. In a seat whose whole job is counting, that is a Critical
class of defect, so the parsing lives here with a decision for each malformed case.

`require` is used rather than `assert` (see checks.py): a malformed line must fail loudly under
`python -O` too.
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from checks import require


def info_record(line):
    """Parse one `info depth ...` line into a dict. Missing fields stay None.

    Returns None for any line that is not an info-depth line, so callers can filter a stream
    without a second string test.
    """
    parts = line.split()
    if len(parts) < 2 or parts[0] != "info" or parts[1] != "depth":
        return None
    rec = {"depth": None, "seldepth": None, "score": None, "nodes": None,
           "hashfull": None, "time": None, "pv": []}

    def value_after(token):
        """The token after `token`, or None when the token is absent or last."""
        if token not in parts:
            return None
        i = parts.index(token) + 1
        return parts[i] if i < len(parts) else None

    for key in ("depth", "seldepth", "nodes", "hashfull", "time"):
        raw = value_after(key)
        if raw is not None:
            try:
                rec[key] = int(raw)
            except ValueError:
                rec[key] = None
    score_kind = value_after("score")
    score_val = value_after(score_kind) if score_kind is not None else None
    if score_kind is not None and score_val is not None:
        rec["score"] = f"{score_kind} {score_val}"
    if "pv" in parts:
        rec["pv"] = parts[parts.index("pv") + 1:]
    return rec


def bestmove(line):
    """The move from a `bestmove` line, or None when the line carries no move.

    A `bestmove` with no argument is what a truncated or aborted stream looks like, so callers
    that care must test for None rather than assume a move arrived (brief trap 1).
    """
    parts = line.split()
    require(parts and parts[0] == "bestmove", f"not a bestmove line: {line!r}")
    return parts[1] if len(parts) > 1 else None


def is_bail(record, best):
    """The drawn-root bail: 0 nodes, empty pv, and a REAL move.

    A terminal root also reports 0 nodes and an empty pv, with bestmove `0000` and score
    `mate 0`, because there are no legal moves. Conflating the two turned 89 bails into 185
    once, which is why this predicate lives in one place and names both conditions.
    """
    return (record is not None and record["nodes"] == 0 and not record["pv"]
            and best not in (None, "0000"))
