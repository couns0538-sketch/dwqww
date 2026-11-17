#!/usr/bin/env python3
"""check_s01f102.py OUT — my own check of seat 01's S-F102 / S-F103 (the book CANNOT fire on a depth search).

Their claim, from their words:
"the book is probed only when `game_search` holds — clock or movetime — so a depth search can NEVER produce a book
 answer ... Corrected to a clock search, the same harness then reported 3/3."

This is a claim about the ENGINE's book gating, and it has a planted-positive structure built in: a `go wtime` search
on the same position must give a book line. So the check is:
  1. `go depth 12` on three opening positions -> expect **0 book lines** (structurally impossible);
  2. `go wtime 6000` on the SAME three -> expect **3 book lines** (the positive, proving the harness can see one);
  3. `go movetime 100` on the same three -> expect book lines too (the other game_search form).

My own independent harness, PC r15 under PC20, Threads 1, Hash 16, OwnBook at its default TRUE (the book must be
enabled for any of this to be meaningful — that is itself a control).

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

OUT = sys.argv[1]
EXE = "/home/ubuntu/builds/pc/forge"
PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
        ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
        ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
        ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
        ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true")]
# three OPENING positions, reached by move lists (the book is keyed on opening positions)
OPENINGS = ["", "e2e4", "e2e4 e7e5"]
GOS = [("go depth 12", "depth"), ("go wtime 6000 btime 6000", "clock"), ("go movetime 100", "movetime")]


def run(moves, go, ownbook=True):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            if l.startswith("readyok"):
                return

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in PC20:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("setoption name Threads value 1")
    sync()
    send("setoption name Hash value 16")
    sync()
    send("setoption name OwnBook value %s" % ("true" if ownbook else "false"))
    sync()
    send("ucinewgame")
    sync()
    if moves:
        send("position startpos moves " + moves)
    else:
        send("position startpos")
    sync()
    send(go)
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    sync()
    send("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    book = [l for l in lines if "book move" in l]
    return {"book": bool(book), "n_info": sum(1 for l in lines if l.startswith("info depth")),
            "bm": lines[-1].split()[1]}


out = []
def emit(s):
    out.append(s)
    print(s)

emit("## seat 01 S-F102/S-F103 — can the book fire on a DEPTH search? (it should be impossible)")
emit("")
emit("PC r15, PC20, Threads 1, Hash 16, **OwnBook true** (the control that makes the test meaningful).")
emit("")
emit("| opening | go form | book line? | info depth lines | bestmove |")
emit("|---|---|---|---|---|")
counts = {}
for go, kind in GOS:
    nbook = 0
    for moves in OPENINGS:
        r = run(moves, go)
        counts.setdefault(kind, 0)
        if r["book"]:
            counts[kind] += 1
            nbook += 1
        emit("| %s | %s | **%s** | %d | %s |" %
             (moves if moves else "startpos", kind, "BOOK" if r["book"] else "no", r["n_info"], r["bm"]))
    emit("| | | **%d of 3** | | |" % nbook)

# control: with OwnBook FALSE the clock search must NOT produce a book line
r_off = run("", "go wtime 6000 btime 6000", ownbook=False)
emit("")
emit("### control: `OwnBook false` + `go wtime` on startpos")
emit("")
emit("| book line? | info depth lines | bestmove |")
emit("|---|---|---|")
emit("| **%s** | %d | %s |" % ("BOOK" if r_off["book"] else "no (as required)", r_off["n_info"], r_off["bm"]))

emit("")
emit("## The claim, tested")
emit("")
emit("| their statement | my measurement |")
emit("|---|---|")
emit("| a depth search can NEVER produce a book answer | **%d of 3 book lines on `go depth 12`** |" % counts.get("depth", 0))
emit("| a clock search does produce them | **%d of 3 on `go wtime 6000`** |" % counts.get("clock", 0))
emit("| `movetime` should too (the other game_search form) | **%d of 3 on `go movetime 100`** |" % counts.get("movetime", 0))
emit("| OwnBook false must suppress the clock book line | **%s** |" % ("suppressed" if not r_off["book"] else "NOT suppressed"))
emit("")
ok = (counts.get("depth", 1) == 0 and counts.get("clock", 0) == 3
      and counts.get("movetime", 0) == 3 and not r_off["book"])
if ok:
    emit("**CONFIRMS**: the book fires on both `game_search` forms (3/3 each) and NEVER on a depth search (0/3),")
    emit("and `OwnBook false` suppresses it. Their corrected 3/3 reproduces exactly, and their false negative is")
    emit("demonstrably a property of the instrument — my own depth arm is the same structurally-blind test.")
else:
    emit("**PARTIAL** — see the table.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
