#!/usr/bin/env python3
"""sweep_outputs.py OUTDIR [MAXFILES] : find committed OUTPUT files that show a `bestmove` with no search.

The better test than the input-file sweep: an aborted search (19-F12) leaves `bestmove` in the output with no
`info depth` line before it. This reads every committed text file under forge-combo29/swarm/*/ and flags any
that contain `bestmove` but no `info depth` — the signature of 19-F12.

Deliberate exclusions, so the result is not noise:
  * files with fewer than 1 `bestmove` line are skipped (nothing to judge);
  * a file is only flagged if it has ZERO `info depth` lines AND at least one `bestmove`;
  * `perft` outputs are NOT flagged, because perft prints `nodes N` and never `bestmove`, so they cannot trip it;
  * files over MAXFILES bytes are skipped (whole-game logs may legitimately mix many sessions).

Report only: a flagged output is evidence that SOME search in that file was aborted. It does not by itself
prove a conclusion is wrong, and for a multi-search file it may be one bad cell among good ones.
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1]
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 400_000
os.makedirs(OUT, exist_ok=True)
REPO = "/agent/repos/dwqww"

branches = subprocess.run('git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*"',
                          shell=True, cwd=REPO, capture_output=True, text=True).stdout
seats = sorted({m.group(1) for m in re.finditer(r"swarm-(\d+)$", branches, re.M)})


def sh(cmd, binary=False):
    r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


SKIP = re.compile(r"\.(patch\.txt|py|sh|md|json|jsonl|epd|fens|csv|tsv)$", re.I)

summary = {}
flagged = []
for s in seats:
    if s == "19":
        continue                                  # my own folder is audited separately below
    sh("git fetch -q --depth 1 origin for-fable-and-opus/swarm-%s" % s)
    files = sh('git ls-tree -r --name-only FETCH_HEAD -- "forge-combo29/swarm/%s/"' % s).split("\n")
    for f in files:
        if not f or SKIP.search(f):
            continue
        raw = sh('git show "FETCH_HEAD:%s"' % f, binary=True)
        if not raw or len(raw) > MAX:
            continue
        body = raw.decode("utf-8", "replace")
        nb = len(re.findall(r"^\s*(?:bestmove|>>> bestmove)\b", body, re.M))
        if nb == 0:
            continue
        ni = len(re.findall(r"^\s*info depth", body, re.M))   # FIXED: leading whitespace counts
        summary[s] = summary.get(s, [0, 0])
        summary[s][0] += 1
        if ni == 0:
            summary[s][1] += 1
            flagged.append((s, f, nb))

# audit my own folder the same way
sh('git ls-tree -r --name-only HEAD -- "forge-combo29/swarm/19/" > /tmp/own_files.txt')
for f in open("/tmp/own_files.txt").read().split("\n"):
    if not f or SKIP.search(f):
        continue
    try:
        raw = open(os.path.join(REPO, f), "rb").read()
    except OSError:
        continue
    if not raw or len(raw) > MAX:
        continue
    body = raw.decode("utf-8", "replace")
    nb = len(re.findall(r"^\s*(?:bestmove|>>> bestmove)\b", body, re.M))
    if nb == 0:
        continue
    ni = len(re.findall(r"^\s*info depth", body, re.M))   # FIXED: leading whitespace counts
    summary["19"] = summary.get("19", [0, 0])
    summary["19"][0] += 1
    if ni == 0:
        summary["19"][1] += 1
        flagged.append(("19", f, nb))

with open(os.path.join(OUT, "RESULT.txt"), "w") as fh:
    fh.write("# committed OUTPUT files containing `bestmove` but NO `info depth` line (19-F12 signature)\n")
    fh.write("# NOTE: an earlier version of this script used ^info depth without allowing indentation, which\n")
    fh.write("# flagged 1983 files mostly falsely. This run uses ^\\s*info depth. Raw-output files only:\n")
    fh.write("# report-style *.txt that merely MENTION bestmove are still counted, so read the file list, not just\n")
    fh.write("# the counts.\n\n")
    fh.write("| seat | files with bestmove | of those, ZERO info depth |\n|---|---|---|\n")
    for s in sorted(summary, key=lambda x: -summary[x][1]):
        tot, bad = summary[s]
        if bad:
            fh.write("| %s | %d | **%d** |\n" % (s, tot, bad))
    fh.write("\n## flagged files (first 40)\n\n")
    for s, f, nb in flagged[:40]:
        fh.write("- seat %s: `%s` (%d bestmove lines, 0 info depth)\n" % (s, f, nb))
    fh.write("\nseats scanned: %d ; files flagged: %d\n" % (len(seats), len(flagged)))
print(open(os.path.join(OUT, "RESULT.txt")).read()[-2500:])
