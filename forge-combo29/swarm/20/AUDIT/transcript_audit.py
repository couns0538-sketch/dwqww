#!/usr/bin/env python3
"""transcript_audit.py — seat 20: find committed ENGINE TRANSCRIPTS that contain a bestmove but NO search.

Seat 19's sweep of all 49 seat branches found 251 such files (mine: 222). The defect: a harness that pipes
`position`/`go`/`quit` together lets `quit` win, so the engine answers with its first generated move and the file looks
like evidence while containing no search at all.

This is the local version so the check is mechanical rather than remembered. It distinguishes:
  * ENGINE TRANSCRIPT  — contains 'id name' or an 'option name' line, i.e. real engine stdout. A bestmove here with
    zero `info depth` lines is a VIOLATION (unless the file is explicitly listed as an intentional unsearched-path
    capture, which this tool takes from a labelled allowlist file).
  * SCRIPT SUMMARY     — my own script's table output (no 'id name'/'option name'), where zero info-depth is normal.
    Reported separately so it is visible but not counted as a violation.

usage: transcript_audit.py [root]      exit 0 = no violations, 1 = violations found
"""
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files that DELIBERATELY capture unsearched answers (the job3 work was about that path). Listed, not guessed.
ALLOW = {
    "job3/out/",            # labelled in job3/DISCARDED_HARNESS.md — discarded harness, cited by nothing
}

TEXT_EXT = (".txt", ".out", ".log", ".tsv", ".jsonl")
SKIP = ("stamps", "PREDICTION", "REPORT_", "FINDINGS", "STATUS", "SEAT", "HONESTY", "METHOD", "AUDIT")

violations, summaries, transcripts = [], [], 0
for dirpath, _dirnames, filenames in os.walk(root):
    rel_dir = os.path.relpath(dirpath, root)
    for fn in filenames:
        if not fn.endswith(TEXT_EXT):
            continue
        if any(s in fn for s in SKIP) or fn.endswith(".meta"):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.normpath(os.path.join(rel_dir, fn))
        try:
            body = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if not re.search(r"^bestmove", body, re.M):
            continue
        has_depth = "info depth" in body
        is_engine = bool(re.search(r"^id name|^option name ", body, re.M))
        if is_engine:
            transcripts += 1
            if not has_depth:
                if any(rel.startswith(a) for a in ALLOW):
                    summaries.append((rel, "allowlisted (labelled discarded harness)"))
                else:
                    violations.append(rel)
        else:
            summaries.append((rel, "script summary (no engine banner)"))

print(f"scanned under {root}")
print(f"engine transcripts containing a bestmove: {transcripts}")
print()
print("== VIOLATIONS: engine transcript with a bestmove and NO info-depth line")
if not violations:
    print("  none")
for v in violations:
    print(f"  {v}")
print()
print("== allowlisted / script summaries (zero info-depth is expected here)")
for rel, why in summaries:
    print(f"  {rel}: {why}")

print()
if violations:
    print(f"FAIL: {len(violations)} transcript(s) show a bestmove with no search — the driver piped quit into a search.")
    sys.exit(1)
if transcripts == 0:
    # S-F68 lesson: a check that found nothing to inspect must NOT report CLEAN — that is a silent pass.
    print("FAIL: scanned ZERO engine transcripts — nothing was actually checked, so this is not a clean result.")
    sys.exit(1)
print(f"CLEAN: no engine transcript has a bestmove without a search ({transcripts} transcripts inspected).")
sys.exit(0)
