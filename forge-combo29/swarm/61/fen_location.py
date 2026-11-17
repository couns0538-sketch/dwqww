#!/usr/bin/env python3
"""Where does `info string invalid FEN` actually land?  Measured on this build, both patterns.

Case A: `position` then `isready` (the defensive pattern) -> diagnostic in the POSITION reply.
Case B: `position` then `go` with no isready in between -> diagnostic in the GO output.
Case C: fresh session, no predecessor -> still emitted (the corrected clause).

The "position reply" region is the lines produced between the end of the UCI handshake and
either `readyok` (case A) or the first line of search output (case B).  A harness that reads
only one of the two regions misses the diagnostic in the other, which is the failure this
file exists to prevent.

`quit` is sent only AFTER `bestmove` is seen, so the engine is not cut off mid-search (a
`go` followed immediately by `quit` is one of the paths that produces zero info lines).
"""
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "./forge_base"
BAD = "9k/9/8/8/8/8/8/K7 w - - 0 1"   # nine files on rank 8: unparseable placement


def run(script, timeout=30.0):
    """Send each line, then read until bestmove (or quit is the last token), then quit."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    deadline = time.monotonic() + timeout
    for entry in script:
        send(entry)
        tag = entry.split()[0]
        if tag == "uci":
            while time.monotonic() < deadline:
                ln = p.stdout.readline()
                if ln == "":
                    raise RuntimeError("stdout closed during uci")
                lines.append(ln.rstrip("\n"))
                if ln.strip() == "uciok":
                    break
        elif tag == "isready":
            while time.monotonic() < deadline:
                ln = p.stdout.readline()
                if ln == "":
                    raise RuntimeError("stdout closed during isready")
                lines.append(ln.rstrip("\n"))
                if ln.strip() == "readyok":
                    break
        elif tag == "go":
            while time.monotonic() < deadline:
                ln = p.stdout.readline()
                if ln == "":
                    raise RuntimeError("stdout closed during go")
                lines.append(ln.rstrip("\n"))
                if ln.startswith("bestmove"):
                    break
        elif tag == "position":
            # Do not read here: whatever the position command emits belongs to the next wait.
            time.sleep(0.02)
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    return lines


def regions(lines):
    """(position-reply region, go-output region).

    The position region runs from just after `uciok` to the first of `readyok` (inclusive)
    or the first search-output line.  Everything after that is the go output.
    """
    try:
        start = lines.index("uciok") + 1
    except ValueError:
        start = 0
    for i in range(start, len(lines)):
        ln = lines[i]
        if ln.strip() == "readyok":
            return lines[start:i + 1], lines[i + 1:]
        if ln.startswith("info depth") or ln.startswith("bestmove"):
            return lines[start:i], lines[i:]
    return lines[start:], []


print("=== Case A: position, then isready (defensive pattern)")
a = run(["uci", "position fen " + BAD, "isready", "go depth 4"])
pos, go = regions(a)
in_pos = any("invalid FEN" in ln for ln in pos)
in_go = any("invalid FEN" in ln for ln in go)
print("  position-reply region: %r" % (pos,))
print("  go-output region     : %r" % (go[:3],))
print("  in POSITION reply: %-5s | in GO output: %-5s" % (in_pos, in_go))
print("  reader that scans ONLY go output -> %s" % ("MISSES IT" if not in_go else "sees it"))

print("\n=== Case B: position, then go, no isready between")
b = run(["uci", "position fen " + BAD, "go depth 4"])
pos_b, go_b = regions(b)
in_pos_b = any("invalid FEN" in ln for ln in pos_b)
in_go_b = any("invalid FEN" in ln for ln in go_b)
print("  position-reply region: %r" % (pos_b,))
print("  go-output region     : %r" % (go_b[:3],))
print("  in POSITION reply: %-5s | in GO output: %-5s" % (in_pos_b, in_go_b))
print("  reader that scans ONLY the position reply -> %s"
      % ("MISSES IT" if not in_pos_b else "sees it"))

print("\n=== Case C: FRESH session, first and only position is the bad one")
c = run(["uci", "position fen " + BAD, "isready", "go depth 4"])
pos_c, go_c = regions(c)
in_pos_c = any("invalid FEN" in ln for ln in pos_c)
in_go_c = any("invalid FEN" in ln for ln in go_c)
print("  in POSITION reply: %-5s | in GO output: %-5s  (corrected clause: always emitted)"
      % (in_pos_c, in_go_c))

print("\n=== What the engine answered anyway")
for label, lines in (("A", a), ("B", b), ("C", c)):
    bm = [ln for ln in lines if ln.startswith("bestmove")]
    info = [ln for ln in lines if ln.startswith("info depth")]
    print("  %s: bestmove=%r  info-depth-lines=%d" % (label, bm, len(info)))

rows = 3
print("\n%-4s %-10s %-9s %-9s %-14s" % ("case", "pre-readyok", "in-go", "emitted", "before-1st-depth"))
for label, x, y, lines in (("A", in_pos, in_go, a), ("B", in_pos_b, in_go_b, b),
                           ("C", in_pos_c, in_go_c, c)):
    idx_fen = next((i for i, s in enumerate(lines) if "invalid FEN" in s), None)
    idx_dep = next((i for i, s in enumerate(lines) if s.startswith("info depth")), None)
    before = (idx_fen is not None and idx_dep is not None and idx_fen < idx_dep)
    print("%-4s %-10s %-9s %-9s %-14s" % (label, x, y, x or y, before))

always = all(x or y for x, y in ((in_pos, in_go), (in_pos_b, in_go_b), (in_pos_c, in_go_c)))
before_depth = []
for lines in (a, b, c):
    idx_fen = next((i for i, s in enumerate(lines) if "invalid FEN" in s), None)
    idx_dep = next((i for i, s in enumerate(lines) if s.startswith("info depth")), None)
    before_depth.append(idx_fen is not None and idx_dep is not None and idx_fen < idx_dep)
pre_readyok = in_pos  # case A only: isready was sent
print("\nrows examined: %d" % rows)
print("1. diagnostic emitted in EVERY case (corrected clause):        %s" % always)
print("2. diagnostic precedes the FIRST `info depth` line in all 3:   %s" % all(before_depth))
print("3. with `isready` it lands before `readyok` (case A):          %s" % pre_readyok)
print("4. a reader that scans only post-readyok output misses case A: %s" % (in_pos and not in_go))
print("\nNOTE: cases A and B put the diagnostic before the first search line either way, so a")
print("harness that buffers from `position` through `bestmove` catches both. The rule that")
print("matters is therefore: scan the whole window, not one named reply.")
sys.exit(0 if (always and all(before_depth)) else 1)
