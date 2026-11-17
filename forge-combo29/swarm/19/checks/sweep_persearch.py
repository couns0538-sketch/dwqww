#!/usr/bin/env python3
"""sweep_persearch.py OUTDIR [MAXFILES] : find ABORTED searches inside logs that also contain good ones.

19-C14's limit: it only flagged files with ZERO `info depth` lines, so a log with nine good searches and one
aborted was invisible. This walks each file's engine output line by line and counts SEARCH BLOCKS, where a block
ends at a `bestmove` line, and classifies each block:

    GOOD     at least one `info depth` line before its `bestmove`
    ABORTED  no `info depth` line at all before its `bestmove`

It reports the number of aborted blocks per file, so a file with 9 good and 1 aborted shows up as 1 instead of
being invisible.

Caveats stated in the output, because they matter:
  * a "block" is delimited only by `bestmove`, so a log that interleaves several engines or sessions in one file
    may split blocks wrongly — the counts are a triage list, not a measurement;
  * a deliberate zero-node answer (a checkmated root, `searchmoves` with no legal move, insufficient material)
    legitimately produces `bestmove` with no `info depth`, so **some aborted-looking blocks are correct
    behaviour**. The report says which files carry those shapes.
"""
import os
import re
import subprocess
import sys

OUT = sys.argv[1]
MAX = int(sys.argv[2]) if len(sys.argv) > 2 else 400_000
os.makedirs(OUT, exist_ok=True)
REPO = "/agent/repos/dwqww"
SKIP = re.compile(r"\.(patch\.txt|py|sh|md|json|jsonl|epd|fens|csv|tsv)$", re.I)

branches = subprocess.run('git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*"',
                          shell=True, cwd=REPO, capture_output=True, text=True).stdout
seats = sorted({m.group(1) for m in re.finditer(r"swarm-(\d+)$", branches, re.M)})

BESTMOVE = re.compile(r"^\s*(?:>>>\s*)?bestmove\b")
INFO = re.compile(r"^\s*info depth")


BOOK = re.compile(r"info string book move")


def scan_text(body):
    """Returns (good, aborted_after_book, aborted_terminal, aborted_other).

    Refinement over the first version, which could not tell the causes apart:
      * a block containing `info string book move` is a BOOK answer, not an abort -> counted separately;
      * an abort whose block is the LAST block of the file (nothing but quit/EOF after) is the 19-F12 shape
        -> aborted_terminal;
      * an abort in the middle of a file, followed by more commands, is neither -> aborted_other.
    """
    lines = body.splitlines()
    good = book = terminal = other = 0
    seen_info = seen_book = False
    last_bestmove_index = max((i for i, l in enumerate(lines) if BESTMOVE.match(l)), default=-1)
    for i, line in enumerate(lines):
        if INFO.match(line):
            seen_info = True
        elif BOOK.search(line):
            seen_book = True
        elif BESTMOVE.match(line):
            if seen_info:
                good += 1
            elif seen_book:
                book += 1
            elif i == last_bestmove_index:
                terminal += 1
            else:
                other += 1
            seen_info = seen_book = False
    return good, book, terminal, other


per_seat = {}
files_detail = []


def consider(seat, path, body):
    good, book, terminal, other = scan_text(body)
    aborted = terminal + other
    if good + aborted == 0:
        return
    rec = per_seat.setdefault(seat, [0, 0, 0])      # files, files-with-aborted, total aborted blocks
    rec[0] += 1
    if aborted:
        rec[1] += 1
        rec[2] += aborted
        files_detail.append((seat, path, good, aborted))


def sh(cmd, binary=False):
    r = subprocess.run(cmd, shell=True, cwd=REPO, capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


for s in seats:
    if s == "19":
        continue
    sh("git fetch -q --depth 1 origin for-fable-and-opus/swarm-%s" % s)
    for f in sh('git ls-tree -r --name-only FETCH_HEAD -- "forge-combo29/swarm/%s/"' % s).split("\n"):
        if not f or SKIP.search(f):
            continue
        raw = sh('git show "FETCH_HEAD:%s"' % f, binary=True)
        if not raw or len(raw) > MAX:
            continue
        consider(s, f, raw.decode("utf-8", "replace"))

for f in sh('git ls-tree -r --name-only HEAD -- "forge-combo29/swarm/19/"').split("\n"):
    if not f or SKIP.search(f):
        continue
    try:
        raw = open(os.path.join(REPO, f), "rb").read()
    except OSError:
        continue
    if not raw or len(raw) > MAX:
        continue
    consider("19", f, raw.decode("utf-8", "replace"))

with open(os.path.join(OUT, "RESULT.txt"), "w") as fh:
    fh.write("# PER-SEARCH scan: aborted searches inside files that also contain good ones\n\n")
    fh.write("A block = the engine output between bestmoves. GOOD = it contained an `info depth` line.\n")
    fh.write("Caveat: a deliberate zero-node answer (checkmated root, no legal `searchmoves`, insufficient\n")
    fh.write("material) legitimately has no `info depth`, so some 'aborted' blocks are correct behaviour.\n\n")
    fh.write("| seat | files with search blocks | files with >=1 aborted block | total aborted blocks |\n")
    fh.write("|---|---|---|---|\n")
    for s in sorted(per_seat, key=lambda x: -per_seat[x][2]):
        f, fa, a = per_seat[s]
        if a:
            fh.write("| %s | %d | **%d** | **%d** |\n" % (s, f, fa, a))
    fh.write("\n## files with a MIX of good and aborted (the shape 19-C14 could not see), first 40\n\n")
    mixed = [d for d in files_detail if d[2] > 0]
    mixed.sort(key=lambda d: -d[3])
    for seat, path, good, ab in mixed[:40]:
        fh.write("- seat %s: `%s` — %d good, **%d aborted**\n" % (seat, path, good, ab))
    fh.write("\nfiles with any aborted block: %d of %d scanned\n" % (len(files_detail), sum(v[0] for v in per_seat.values())))
print(open(os.path.join(OUT, "RESULT.txt")).read()[:2500])
