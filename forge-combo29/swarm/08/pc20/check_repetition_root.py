#!/usr/bin/env python3
"""check_repetition_root.py OUT — close the cell I left untested in 08-C33: the THIRD-OCCURRENCE root.

08-C33 confirmed the halfmove door of the drawn-root matrix on every cell, and left the repetition door untested
because it needs a move list reaching a position three times. This builds that list.

Construction: shuffle knights back and forth so the STARTING position recurs three times, then search from there.
The engine's `position startpos moves ...` path maintains its own hash history, so a genuine threefold is
represented; two occurrences must NOT be treated as drawn.

Sequence: Nf3 Nf6 Ng1 Ng8 (startpos 2nd occurrence) Nf3 Nf6 Ng1 Ng8 (startpos 3rd occurrence).
Then a mate-in-1 board is irrelevant here — the point is whether the root is adjudicated drawn, which shows as
0 nodes and a first-legal-move answer instead of a search.

The discriminating control is the SAME sequence truncated by two plies (two occurrences only), which must NOT be
treated as drawn.

ARGUMENT ORDER: OUT first.
"""
import subprocess
import sys

import chess

OUT = sys.argv[1]
PC = "/home/ubuntu/builds/pc/forge"
BASE = "/home/ubuntu/builds/release/forge"
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"), ("LmrNoisyDivisor", "333"),
       ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"), ("LmpBase", "8"),
       ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"), ("HistoryBonusLinear", "54"),
       ("HistoryBonusMax", "2212"), ("SingularDepth", "6"), ("IirDepth", "2"), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Threads", "1"), ("Hash", "16")]

TWO = "g1f3 g8f6 f3g1 f6g8"                          # startpos reached a 2nd time
THREE = TWO + " g1f3 g8f6 f3g1 f6g8"                  # startpos reached a 3rd time


def run(exe, moves):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    for k, v in S14:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position startpos moves " + moves)
    sync()
    send("go depth 4")
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
    nodes = None
    score = None
    for l in lines:
        if l.startswith("info depth"):
            t = l.split()
            try:
                if "nodes" in t:
                    nodes = int(t[t.index("nodes") + 1])
                if "score" in t:
                    si = t.index("score")
                    score = "%s %s" % (t[si + 1], t[si + 2])
            except (IndexError, ValueError):
                pass
    return {"bm": lines[-1].split()[1], "nodes": nodes, "score": score}


out = []
def emit(s):
    out.append(s)
    print(s)

# control: python-chess must agree the position has occurred three times in the long sequence
b = chess.Board()
for mv in THREE.split():
    b.push(chess.Move.from_uci(mv))
rep_count = b.is_repetition(3)
emit("## The THIRD-OCCURRENCE root — the cell 08-C33 left untested")
emit("")
emit("Control: after `%s`, python-chess says the position has occurred three times: **%s**" % (THREE, rep_count))
if not rep_count:
    raise SystemExit("CONTROL FAILED: python-chess does not see a threefold on this move list, so the test "
                     "cannot build the case")
emit("")
emit("| build | move list | bestmove | nodes | score | drawn root? |")
emit("|---|---|---|---|---|---|")
rows = {}
for label, exe in (("base 6b98f217", BASE), ("PC r15", PC)):
    for mlabel, moves in (("two occurrences (CONTROL)", TWO), ("THREE occurrences", THREE)):
        r = run(exe, moves)
        rows[(label, mlabel)] = r
        drawn = (r["nodes"] == 0)
        emit("| %s | %s | %s | %s | %s | %s |" %
             (label, mlabel, r["bm"], f"{r['nodes']:,}" if r["nodes"] is not None else "-",
              r["score"], "**YES (0 nodes)**" if drawn else "no"))

emit("")
emit("## The claim, tested")
emit("")
emit("| question | answer |")
emit("|---|---|")
b2 = rows[("base 6b98f217", "two occurrences (CONTROL)")]
b3 = rows[("base 6b98f217", "THREE occurrences")]
p2 = rows[("PC r15", "two occurrences (CONTROL)")]
p3 = rows[("PC r15", "THREE occurrences")]
emit("| base does NOT draw TWO occurrences (control) | **%s** (%s nodes) |" %
     ("correct" if b2["nodes"] else "**WRONG - drew it**", b2["nodes"]))
emit("| base DRAWS the third occurrence | **%s** (%s nodes) |" %
     ("YES" if b3["nodes"] == 0 else "no", b3["nodes"]))
emit("| PC does NOT draw TWO occurrences (control) | **%s** (%s nodes) |" %
     ("correct" if p2["nodes"] else "**WRONG - drew it**", p2["nodes"]))
emit("| PC finds a real search on the third occurrence | **%s** (%s nodes) |" %
     ("YES" if p3["nodes"] and p3["nodes"] > 0 else "NO - also drew it", p3["nodes"]))
emit("")
if b3["nodes"] == 0 and p3["nodes"] and p3["nodes"] > 0 and b2["nodes"] and p2["nodes"]:
    emit("**CONFIRMS the repetition door of S-F17 exactly**: the base build adjudicates a genuine THIRD occurrence as")
    emit("drawn (0 nodes) while the PC build searches it, and BOTH builds search the two-occurrence control — so the")
    emit("boundary is the third occurrence, not repetition in general. That closes the last cell of the matrix.")
elif b3["nodes"] == 0 and p3["nodes"] == 0:
    emit("**BOTH builds draw the third occurrence** — the PC repair does NOT reach the repetition door on this")
    emit("construction, which would REFUTE that half of S-F17. See the table.")
else:
    emit("**Partial/mixed** — see the table.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
