#!/usr/bin/env python3
"""plant_zeros.py OUT — plants for my two load-bearing ZEROS.

Both are safety claims the owner may rely on, and seat 19's point applies to each: a zero with no plant is "not shown".

  ZERO A: "0 of 400 timed searches exceeded their clock" (08-F7, 08-F24, and the sweep tables).
  ZERO B: "0 of 800 bestmoves were illegal" (08-F7).

For each, the plant must make the SAME comparator report a FAILURE when one exists. A comparator that cannot fail
turns a real fault into a zero, which is exactly the failure mode being guarded against.

ZERO A plant — two arms:
  A1 a FAKE engine that sleeps 2.5 s on a 1 s clock: the timer must record it as "over the clock".
  A2 the real engine on a 1 s clock: must record "not over the clock". (Same code, opposite verdicts.)

ZERO B plant — two arms:
  B1 a FAKE engine that answers `bestmove a1a8` (illegal from startpos): the legality check must flag it.
  B2 the real engine on the same position: must pass.

Both fake engines speak enough UCI to get past the harness's sync, so the plant exercises the comparator, not the
handshake.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys
import time

import chess

OUT = sys.argv[1]
REAL = "/home/ubuntu/builds/pc/forge"
FAKE_SLOW = "/tmp/fake_slow_engine.sh"
FAKE_ILLEGAL = "/tmp/fake_illegal_engine.sh"

# A fake engine that answers every `go` after 2.5 s -> must be caught as a clock overrun on a 1 s clock.
open(FAKE_SLOW, "w").write("""#!/usr/bin/env bash
while IFS= read -r line; do
  case "$line" in
    uci) echo "id name FAKE_SLOW"; echo "uciok";;
    isready) echo "readyok";;
    setoption*) : ;;
    ucinewgame) : ;;
    position*) : ;;
    go*) sleep 2.5; echo "info depth 1 score cp 0 nodes 1 pv e2e4"; echo "bestmove e2e4";;
    quit) exit 0;;
  esac
done
""")

# A fake engine that answers immediately with an ILLEGAL move from startpos -> must be caught by the legality check.
open(FAKE_ILLEGAL, "w").write("""#!/usr/bin/env bash
while IFS= read -r line; do
  case "$line" in
    uci) echo "id name FAKE_ILLEGAL"; echo "uciok";;
    isready) echo "readyok";;
    setoption*) : ;;
    ucinewgame) : ;;
    position*) : ;;
    go*) echo "info depth 1 score cp 0 nodes 1 pv a1a8"; echo "bestmove a1a8";;
    quit) exit 0;;
  esac
done
""")
import os
os.chmod(FAKE_SLOW, 0o755)
os.chmod(FAKE_ILLEGAL, 0o755)

START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CLOCK = "go wtime 1000 btime 1000 winc 0 binc 0"


def timed_search(exe, fen, go, timeout=20.0, want_info=False):
    """Minimal harness: send go, read to bestmove, return (wall_ms, bestmove[, n_info])."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    while True:
        l = p.stdout.readline()
        if not l or l.startswith("uciok"):
            break
    send("isready")
    while True:
        l = p.stdout.readline()
        if not l or l.startswith("readyok"):
            break
    send("setoption name OwnBook value false")
    send("isready")
    while True:
        l = p.stdout.readline()
        if not l or l.startswith("readyok"):
            break
    send("position fen " + fen)
    send("isready")
    while True:
        l = p.stdout.readline()
        if not l or l.startswith("readyok"):
            break
    t0 = time.monotonic()
    send(go)
    bm = None
    n_info = 0
    while True:
        if time.monotonic() - t0 > timeout:
            p.kill()
            return (None, None, 0) if want_info else (None, None)
        l = p.stdout.readline()
        if not l:
            break
        if l.startswith("info depth"):
            n_info += 1
        if l.startswith("bestmove"):
            bm = l.split()[1]
            break
    wall = (time.monotonic() - t0) * 1000.0
    try:
        send("quit")
        p.wait(timeout=5)
    except Exception:
        p.kill()
    return (wall, bm, n_info) if want_info else (wall, bm)


def legal(bm, fen):
    b = chess.Board(fen)
    if bm is None:
        return False
    try:
        return chess.Move.from_uci(bm) in b.legal_moves
    except Exception:
        return False


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## PLANT for ZERO A — 'no search exceeded its clock'")
emit("")
emit("Clock 1000 ms. The comparator is `wall > 1000`.")
emit("")
emit("| arm | engine | wall ms | over the 1000 ms clock? | required |")
emit("|---|---|---|---|---|")
w_slow, _ = timed_search(FAKE_SLOW, START, CLOCK)
if w_slow is None:
    raise SystemExit("PLANT A1 FAILED TO RUN: the fake slow engine produced no bestmove")
a1 = w_slow > 1000
emit("| A1 PLANT | fake engine sleeping 2.5 s | %.0f | **%s** | **YES** |" % (w_slow, "YES" if a1 else "NO — COMPARATOR BLIND"))
w_real, _, n_info_real = timed_search(REAL, START, CLOCK, want_info=True)
if w_real is None:
    raise SystemExit("PLANT A2 FAILED TO RUN: the real engine produced no bestmove")
if n_info_real == 0:
    raise SystemExit("PLANT A2 INVALID: the real engine answered with 0 info depth lines, i.e. from the BOOK, so "
                     "it did not search and cannot serve as a control (OwnBook false is now sent above)")
a2 = w_real > 1000
emit("| A2 control | real engine (%d info lines, so it searched) | %.0f | %s | no |" %
     (n_info_real, w_real, "YES" if a2 else "no"))

emit("")
emit("## PLANT for ZERO B — 'no bestmove was illegal'")
emit("")
emit("The comparator is `bestmove in python-chess legal moves for the FEN`.")
emit("")
emit("| arm | engine | bestmove | legal? | required |")
emit("|---|---|---|---|---|")
_, bm_fake = timed_search(FAKE_ILLEGAL, START, CLOCK)
if bm_fake is None:
    raise SystemExit("PLANT B1 FAILED TO RUN: the fake illegal engine produced no bestmove")
b1 = legal(bm_fake, START)
emit("| B1 PLANT | fake engine answering a1a8 | **%s** | **%s** | **illegal (NO)** |" %
     (bm_fake, "legal" if b1 else "ILLEGAL — caught"))
_, bm_real = timed_search(REAL, START, CLOCK)
if bm_real is None:
    raise SystemExit("PLANT B2 FAILED TO RUN: the real engine produced no bestmove")
b2 = legal(bm_real, START)
emit("| B2 control | real engine | %s | %s | legal (yes) |" % (bm_real, "legal" if b2 else "ILLEGAL"))

emit("")
emit("## VERDICT")
emit("")
emit("| zero | plant caught the fault? | control passed? | the zero is |")
emit("|---|---|---|---|")
emit("| A: no search over its clock | **%s** | **%s** | **%s** |" %
     ("YES" if a1 else "NO", "YES" if not a2 else "NO",
      "MEASURED" if (a1 and not a2) else "NOT SHOWN"))
emit("| B: no illegal bestmove | **%s** | **%s** | **%s** |" %
     ("YES" if not b1 else "NO", "YES" if b2 else "NO",
      "MEASURED" if (not b1 and b2) else "NOT SHOWN"))

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
