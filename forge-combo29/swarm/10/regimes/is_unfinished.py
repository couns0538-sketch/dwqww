#!/usr/bin/env python3
"""is_unfinished.py -- THE CHECKER. Apply it to recorded engine output to find searches that were cut off.

Rule R1 (exact, when the requested depth is known):
    a record is UNFINISHED  <=>  its LAST `info depth <N>` has N < the depth that was requested.

Measured on 112 recorded searches (4 positions x 2 builds x 7 delays x 2 reps, depth 12 requested):
    genuinely truncated records : 90   -> R1 caught ALL 90
    records identical to a finished search : 19 -> R1 raised 0 false alarms
    records with no `info` line at all : 3 -> R1 cannot see them; treat "bestmove with zero info
        lines" as UNFINISHED too (it is the <=20 ms regime, and it is the worst case: no score at all).

Rule R2 (when the requested depth was NOT recorded, e.g. old saved data):
    a record is UNFINISHED  <=>  its last depth is LESS THAN the largest depth appearing anywhere in
    the same file/run at the same settings.
    Measured: catches all 90, 0 false alarms -- but ONLY because the file also contains at least one
    completed search. If every search in the file was truncated the same way, R2 cannot fire.

What does NOT work (tested, so nobody wastes time):
    - "there is a bestmove line": 109/112 interrupted records HAVE one. Useless.
    - "the pv is short": a fail-low pv is legitimately short. Useless.
    - "nodes are 0": only in the <=20 ms regime, not the middle band.

Usage:
    is_unfinished.py FILE [--requested-depth N] [--quiet]
FILE is text containing engine output; one or more searches separated by `bestmove` lines.
Exit code 0 = every record looks finished, 1 = at least one record looks unfinished.
"""
import re
import sys


def records(text):
    """split engine output into searches, each ending at a bestmove line"""
    out = []
    cur = []
    for line in text.splitlines():
        cur.append(line)
        if line.startswith("bestmove"):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def analyse(lines, requested=None, file_max=None):
    depths = []
    for l in lines:
        m = re.match(r"info depth (\d+)", l)
        if m:
            depths.append(int(m.group(1)))
    has_bestmove = any(l.startswith("bestmove") for l in lines)
    last_depth = depths[-1] if depths else None
    verdict = None
    reason = None
    if not depths:
        if has_bestmove:
            verdict = "UNFINISHED"
            reason = "bestmove with ZERO info lines (interrupted before the first iteration)"
        else:
            verdict = "UNKNOWN"
            reason = "no bestmove and no info: not a completed search record"
    elif requested is not None:
        if last_depth < requested:
            verdict = "UNFINISHED"
            reason = "last depth %d < requested depth %d" % (last_depth, requested)
        else:
            verdict = "finished"
            reason = "reached the requested depth %d" % requested
    elif file_max is not None:
        if last_depth < file_max:
            verdict = "UNFINISHED"
            reason = "last depth %d < largest depth in this file (%d)" % (last_depth, file_max)
        else:
            verdict = "finished"
            reason = "reached this file's largest depth (%d)" % file_max
    else:
        verdict = "UNKNOWN"
        reason = "no requested depth given and no file maximum available"
    return {"last_depth": last_depth, "max_depth": max(depths) if depths else None,
            "info_lines": len(depths), "has_bestmove": has_bestmove,
            "verdict": verdict, "reason": reason}


def file_has_depth_target(text):
    """True when the file's own command echoes show a `go depth`; False when they show only
    node/clock limits; None when no `go` line was recorded at all."""
    import re as _re
    kinds = set(_re.findall(r"^\s*go (\w+)", text, _re.M))
    if not kinds:
        return None
    return "depth" in kinds


def main():
    path = sys.argv[1]
    requested = None
    if "--requested-depth" in sys.argv:
        requested = int(sys.argv[sys.argv.index("--requested-depth") + 1])
    quiet = "--quiet" in sys.argv
    text = open(path, errors="replace").read()
    depth_target = file_has_depth_target(text)
    recs = records(text)
    all_depths = [d for r in recs for d in
                  (int(m.group(1)) for m in (re.match(r"info depth (\d+)", l) for l in r) if m)]
    file_max = max(all_depths) if all_depths else None
    bad = 0
    for i, r in enumerate(recs):
        # R2 is only sound on files whose searches had a DEPTH TARGET; refuse to guess otherwise.
        use_file_max = file_max if (requested is not None or depth_target is not False) else None
        a = analyse(r, requested=requested, file_max=use_file_max)
        if a["verdict"] == "UNKNOWN" and depth_target is False:
            a["reason"] = ("file uses node/clock limits, not a depth target: R2 is INVALID here; "
                           "record the budget and test against that instead")
        if a["verdict"] == "UNFINISHED":
            bad += 1
        if not quiet:
            print("record %d: %-10s %s" % (i, a["verdict"], a["reason"]))
    print("%d record(s), %d look UNFINISHED" % (len(recs), bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
