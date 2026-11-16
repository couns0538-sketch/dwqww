#!/usr/bin/env python3
"""threads_check.py EXE FENS OUTDIR : is this harness actually at Threads 1, and is its score reproducible?

Seat 04 found that at Threads 4 the PC build gives four different scores (+2576, mate 13, mate 18, mate 16)
and node counts from 5.0M to 31.4M on one position, while Threads 1 gives +2207 and identical 75,311 nodes
four times. The swarm rule is now: report scores from Threads 1 only.

This script does two things:
  (a) asserts the exe's own `uci` answer advertises `Threads ... default 1`, and that no `setoption name
      Threads` is sent by any of my harnesses (checked by grep, reported in the file);
  (b) runs the SAME search four times in four fresh processes with no setoption at all, and prints the four
      scores and node counts. If they are identical, this harness is in the Threads-1 regime seat 04 describes.

It then repeats (b) with an EXPLICIT `setoption name Threads value 1` to show the two paths agree, and
finally once at Threads 4 as a positive control: if Threads 4 also produced identical results here, the
control would prove the test cannot see the difference, which would invalidate the Threads-1 claim.
"""
import os
import re
import subprocess
import sys

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

fen = [l.strip() for l in open(fens) if l.strip()][0]   # one fixed position
# a middlegame position, so the search is long enough to see score variation
POS = "position fen r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
DEPTH = 12


def one(threads, extra=()):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        proc.stdin.write(l + "\n")
        proc.stdin.flush()

    def readto(pred):
        while True:
            line = proc.stdout.readline()
            if not line:
                return False
            if pred(line):
                return True

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    opts = []
    if threads is not None:
        opts.append(("Threads", str(threads)))
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        readto(lambda l: l.startswith("readyok"))
    send(POS)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("go depth %d" % DEPTH)
    score = None
    nodes = 0
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        m = re.search(r"score (cp|mate) (-?\d+)", line)
        if m:
            score = ("cp " if m.group(1) == "cp" else "mate ") + m.group(2)
        if " nodes " in line:
            try:
                nodes = int(line.split("nodes ")[1].split()[0])
            except (IndexError, ValueError):
                pass
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
    return score, nodes


lines = []
uci = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True).stdout
tline = [l for l in uci.splitlines() if "option name Threads" in l]
lines.append("exe: %s" % os.path.abspath(exe))
lines.append("engine's Threads line: %s" % (tline[0] if tline else "NOT FOUND"))
lines.append("")

lines.append("## (b) no setoption at all, four fresh processes")
base = []
for i in range(4):
    s, n = one(None)
    base.append((s, n))
    lines.append("run %d: score %s  nodes %d" % (i + 1, s, n))
ident_base = len({(s, n) for s, n in base}) == 1
lines.append("identical across four runs: %s" % ident_base)
lines.append("")

lines.append("## explicit setoption name Threads value 1, four fresh processes")
t1 = []
for i in range(4):
    s, n = one(1)
    t1.append((s, n))
    lines.append("run %d: score %s  nodes %d" % (i + 1, s, n))
ident_t1 = len({(s, n) for s, n in t1}) == 1
lines.append("identical across four runs: %s" % ident_t1)
lines.append("same as the no-setoption runs: %s" % (set(base) == set(t1)))
lines.append("")

lines.append("## positive control: Threads 4 (seat 04 says this should vary)")
t4 = []
for i in range(4):
    s, n = one(4)
    t4.append((s, n))
    lines.append("run %d: score %s  nodes %d" % (i + 1, s, n))
ident_t4 = len({(s, n) for s, n in t4}) == 1
lines.append("identical across four runs: %s" % ident_t4)
lines.append("")

control_sees_difference = not ident_t4
lines.append("verdict rule: the Threads-1 claim is VACUOUS unless the same harness shows variation at Threads 4.")
lines.append("control sees a difference at Threads 4: %s" % control_sees_difference)
lines.append("")
if ident_base and ident_t1 and control_sees_difference:
    verdict = "CONFIRMED Threads 1 regime (reproducible scores, and the control proves the test can see variation)"
elif ident_base and ident_t1 and not control_sees_difference:
    verdict = "INCONCLUSIVE: scores identical at Threads 1 AND at Threads 4, so this position cannot show the effect"
else:
    verdict = "FAILED: scores varied at Threads 1"
lines.append("VERDICT: " + verdict)

text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print(text)
