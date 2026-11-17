#!/usr/bin/env python3
"""sweep_missing_quit.py OUTDIR : find every committed UCI input file in any seat's folder that sends `go` and
then ends (or sends `quit`) without the harness being able to wait.

19-F12: a terminator (quit or EOF) sent while a search is RUNNING makes the engine publish a fabricated
`bestmove` — the position's first generated move — with zero `info` lines. Seat 27's committed
`input_19f59_depth24.uci` ends right after `go depth 24` with no `quit`, i.e. EOF, and that is exactly how its
`f6e5` arose.

This sweep reads every committed file under forge-combo29/swarm/*/ whose name looks like a UCI input/stream, and
flags any whose LAST `go` line has only `quit` (or nothing) after it — i.e. no command that would let the harness
wait for `bestmove`. A file is SAFE if the last `go` is followed by at least one non-`quit` line (a position/
isready probe the driver can block on), or if the file contains no `go` at all.

It reports; it does not conclude about any seat's results. A flagged file only proves that *piping that file
wholesale* would abort the search — a driver may of course read the file and then wait.
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1]
REPO = "/agent/repos/dwqww"
os.makedirs(OUT, exist_ok=True)

# every seat branch
branches = subprocess.run('git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*"',
                          shell=True, cwd=REPO, capture_output=True, text=True).stdout
seats = sorted({m.group(1) for m in re.finditer(r"swarm-(\d+)$", branches, re.M)})

NAME = re.compile(r"(input|stream|cmds?|commands?|stdin|\.uci$)", re.I)
rows = []
for s in seats:
    subprocess.run("git fetch -q --depth 1 origin for-fable-and-opus/swarm-%s" % s,
                   shell=True, cwd=REPO, capture_output=True)
    files = subprocess.run('git ls-tree -r --name-only FETCH_HEAD -- "forge-combo29/swarm/%s/"' % s,
                           shell=True, cwd=REPO, capture_output=True, text=True).stdout.split("\n")
    for f in files:
        if not f or not NAME.search(f):
            continue
        body = subprocess.run('git show "FETCH_HEAD:%s"' % f, shell=True, cwd=REPO,
                              capture_output=True).stdout.decode("utf-8", "replace")
        if not body or "go " not in body:
            continue
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        goes = [i for i, l in enumerate(lines) if l.startswith("go ")]
        if not goes:
            continue
        last = goes[-1]
        after = lines[last + 1:]
        non_quit_after = [l for l in after if l != "quit"]
        ends_after_go = len(after) == 0
        only_quit_after = len(after) > 0 and not non_quit_after
        if ends_after_go or only_quit_after:
            rows.append((s, f, lines[last], "ENDS right after go" if ends_after_go else "only quit after go"))

with open(os.path.join(OUT, "RESULT.txt"), "w") as fh:
    fh.write("# committed UCI input files whose LAST `go` has no command after it but quit/EOF\n\n")
    fh.write("19-F12: piping such a file aborts the search and the engine publishes a fabricated bestmove\n")
    fh.write("with zero info lines. A flag here does NOT prove a seat's numbers are wrong - a driver may\n")
    fh.write("read the file and then wait for bestmove - but it is the pattern that produced seat 27's f6e5.\n\n")
    if not rows:
        fh.write("no flagged files.\n")
    else:
        fh.write("| seat | file | last go line | how it ends |\n|---|---|---|---|\n")
        for r in rows:
            fh.write("| %s | `%s` | `%s` | %s |\n" % r)
    fh.write("\nseats scanned: %d\n" % len(seats))
print(open(os.path.join(OUT, "RESULT.txt")).read())
