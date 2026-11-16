#!/usr/bin/env python3
"""check_s06f4.py EXE FENFILE OUT — my own check of seat 06's finding S-F4, written from its sentence alone:
"left-right flip changes the static score of 98-99% of real positions, median 20 cp on hce and 60 cp on
total, max 838 cp".

Left-right flip = python-chess board.transform(chess.flip_horizontal), i.e. files a<->h with NO colour swap.
For each position: read the engine's `eval` for the original and for the flip; count how many differ, and
the median/max of |delta| for hce and total.

Controls, both required before any number counts:
  (1) self     - the same position evaluated twice must differ by 0 (the harness can read a stable number);
  (2) sentinel - a position with a bishop moved one file, evaluated against the original, must DIFFER
                 (the harness can see a change at all).
"""
import statistics
import subprocess
import sys

import chess

BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

exe, fenfile, outpath = sys.argv[1:4]
fens = [l.strip() for l in open(fenfile) if l.strip()]
fens = [l.split(" ")[0:6] for l in [" ".join(f.split()[:6]) for f in fens]]
fens = [" ".join(f) for f in fens]

p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def send(line):
    p.stdin.write(line + "\n")
    p.stdin.flush()


def sync():
    send("isready")
    while True:
        l = p.stdout.readline()
        if l == "":
            raise EOFError("engine closed")
        l = l.rstrip("\n")
        for b in BAD:
            if b in l:
                raise RuntimeError("engine refused: %r" % l)
        if l.startswith("readyok"):
            return


send("uci")
while not p.stdout.readline().startswith("uciok"):
    pass
sync()


def evaluate(fen):
    send("position fen " + fen)
    sync()
    send("eval")
    sync()
    # the eval line came before the readyok of the sync above; re-read by asking again with a marker
    return None


# Simpler and unambiguous: one process per eval, so no line can be attributed to the wrong position.
def eval_fresh(fen):
    r = subprocess.run([exe], input="uci\nisready\nposition fen %s\nisready\neval\nisready\nquit\n" % fen,
                       capture_output=True, text=True, timeout=60)
    vals = {}
    for line in r.stdout.splitlines():
        for b in BAD:
            if b in line:
                raise RuntimeError("engine refused %r for %r" % (line, fen))
        if line.startswith("info string eval"):
            t = line.split()
            vals = {"hce": int(t[4]), "nnue": int(t[6]), "total": int(t[8])}
    if not vals:
        raise RuntimeError("no eval line for %r" % fen)
    return vals


lines = []


def emit(s):
    lines.append(s)
    print(s)


# --- control 1: a position against itself
cp = "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"
a, b = eval_fresh(cp), eval_fresh(cp)
emit("## control 1 (same position twice) must be 0")
emit("| position | hce | nnue | total | identical |")
emit("|---|---|---|---|---|")
emit("| %s | %d/%d | %d/%d | %d/%d | %s |" % (cp, a["hce"], b["hce"], a["nnue"], b["nnue"],
                                               a["total"], b["total"], a == b))

# --- control 2: sentinel, a real change must be visible
sent = "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"
sent2 = "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1B1PP/R1B1K2R w KQkq - 2 8"  # g2 pawn -> f2, a visible change
s1, s2 = eval_fresh(sent), eval_fresh(sent2)
emit("")
emit("## control 2 (a moved pawn) must DIFFER")
emit("| original total | changed total | differ |")
emit("|---|---|---|")
emit("| %d | %d | %s |" % (s1["total"], s2["total"], s1 != s2))

# --- HARD ASSERTIONS (seat 19's measurement-integrity warning).
# A control that merely prints cannot stop a NaN/zero/empty result from passing as a confirmation, so both
# controls abort the script instead of being reported. Nothing below runs unless the reader is proven live.
if a != b:
    raise SystemExit("CONTROL 1 FAILED: the same position evaluated twice gave %r vs %r; "
                     "the reader is not stable, refusing to report a result" % (a, b))
if s1 == s2:
    raise SystemExit("CONTROL 2 FAILED: a visibly different position gave the identical eval %r; "
                     "the reader cannot see a change, refusing to report a result" % (s1,))
if a["total"] == 0 and s1["total"] == 0 and s2["total"] == 0:
    raise SystemExit("CONTROL 3 FAILED: every eval total is 0; the eval line is not carrying a number")
emit("")
emit("**Both controls enforced by assertion: any failure above aborts before the result block below.**")

# --- the check itself
rows = []
skipped = 0
for fen in fens:
    try:
        board = chess.Board(fen)
    except Exception:
        skipped += 1
        continue
    try:
        flipped = board.transform(chess.flip_horizontal).fen()
    except Exception:
        skipped += 1
        continue
    try:
        o = eval_fresh(fen)
        f = eval_fresh(flipped)
    except Exception as exc:
        skipped += 1
        emit("SKIP %s (%s)" % (fen, exc))
        continue
    rows.append((fen, flipped, o, f))

n = len(rows)
dh = [abs(r[2]["hce"] - r[3]["hce"]) for r in rows]
dt = [abs(r[2]["total"] - r[3]["total"]) for r in rows]
dn = [abs(r[2]["nnue"] - r[3]["nnue"]) for r in rows]
diffh = sum(1 for d in dh if d != 0)
difft = sum(1 for d in dt if d != 0)
diffn = sum(1 for d in dn if d != 0)

emit("")
emit("## the check: seat 06 S-F4, left-right flip of G positions")
emit("| quantity | value |")
emit("|---|---|")
emit("| positions evaluated | %d (skipped %d) |" % (n, skipped))
emit("| hce differs | %d / %d = %.1f %% |" % (diffh, n, 100.0 * diffh / n))
emit("| nnue differs | %d / %d = %.1f %% |" % (diffn, n, 100.0 * diffn / n))
emit("| total differs | %d / %d = %.1f %% |" % (difft, n, 100.0 * difft / n))
emit("| median abs delta hce | %.0f cp |" % statistics.median(dh))
emit("| median abs delta total | %.0f cp |" % statistics.median(dt))
emit("| max abs delta hce | %d cp |" % max(dh))
emit("| max abs delta total | %d cp |" % max(dt))
emit("")
emit("### the largest total deltas")
emit("| fen | flipped fen | total orig | total flip | delta |")
emit("|---|---|---|---|---|")
for r in sorted(rows, key=lambda r: -abs(r[2]["total"] - r[3]["total"]))[:10]:
    emit("| %s | %s | %d | %d | %d |" % (r[0], r[1], r[2]["total"], r[3]["total"],
                                          r[2]["total"] - r[3]["total"]))

with open(outpath, "w") as fh:
    fh.write("\n".join(lines) + "\n")
send("quit")
p.wait(timeout=10)
