#!/usr/bin/env python3
"""check_s21f12.py OUT — my own check of seat 21's 21-F12:

"The PC build's drawn-root repair REACHES `searchmoves`: at halfmove 100, `go searchmoves e1e8 depth 4` searches
 **8 nodes** and returns the mating move, where the base build answers **0 nodes** for the same line. The 'no legal
 named move' case is unchanged on the PC build (still `0000` + the info line, 0 nodes)."

I need a halfmove-100 board where e1e8 is a mating move and is legal. Construction: a position where a white rook on
e1 can deliver mate on e8, with the halfmove counter at 100. The board must have a mate-in-1 that RESETS the
fifty-move counter or is a mate (per FABLE_TO_swarm_6, a mate delivered on the move that reaches the 100th half-move
is still a mate, so the engine must find it).

I build it and verify with python-chess that e1e8 is mate before using it. Then:
 - base build, `go searchmoves e1e8 depth 4`  -> expected 0 nodes (the drawn-root shortcut)
 - PC build,   `go searchmoves e1e8 depth 4`  -> expected a real search with a small node count
 - CONTROL on both: `go depth 4` without searchmoves, so the harness can tell "searchmoves changed it" from
   "the whole position is mishandled"
 - CONTROL: the illegal-name case on the PC build must still give 0000 + the info string (not a search)

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
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# Build a mate-in-1 for White with a rook on e1 -> e8, kings far apart, halfmove counter 100.
# Black king h8, white rook e1, white king a1: Re8 is mate if h8 has no escape... use a rook+king net instead.
CANDIDATES = [
    # white Kg6, R e1; black Kh8 -> Re8# is mate (Re8 pins the h-file? verify with python-chess)
    "7k/8/6K1/8/8/8/8/4R3 w - - 100 1",
    # white Kf6, Re1, black Kh7 -> Re7+ not mate; try Kg6 + Re8
    "7k/8/5K2/8/8/8/8/4R3 w - - 100 1",
]


def pick_board():
    for fen in CANDIDATES:
        b = chess.Board(fen)
        for m in b.legal_moves:
            b.push(m)
            if b.is_checkmate():
                b.pop()
                return fen, b.uci(m)
            b.pop()
    return None, None


def run(exe, fen, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def sync():
        send("isready")
        got = []
        while True:
            l = p.stdout.readline()
            if not l:
                raise EOFError
            got.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return got

    send("uci")
    while not p.stdout.readline().startswith("uciok"):
        pass
    for k, v in S14 + [("Threads", "1"), ("Hash", "16")]:
        send("setoption name %s value %s" % (k, v))
        sync()
    send("ucinewgame")
    sync()
    send("position fen " + fen)
    pre = sync()
    if any("invalid FEN" in l for l in pre):
        return {"err": "refused", "lines": pre}
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
    nodes = None
    n_info = 0
    for l in lines:
        if l.startswith("info depth"):
            n_info += 1
            t = l.split()
            if "nodes" in t:
                nodes = int(t[t.index("nodes") + 1])
    strings = [l for l in lines if l.startswith("info string")]
    return {"nodes": nodes, "n_info": n_info, "bm": lines[-1].split()[1] if lines else None,
            "strings": strings, "lines": lines}


out = []
def emit(s):
    out.append(s)
    print(s)

fen, mating_move = pick_board()
emit("## seat 21's 21-F12 — does the PC drawn-root repair reach `searchmoves`?")
emit("")
if fen is None:
    raise SystemExit("CONTROL FAILED: could not construct a halfmove-100 board with a mate-in-1")
b = chess.Board(fen)
emit("Board `%s`, verified in python-chess: `%s` is LEGAL and MATES." % (fen, mating_move))
emit("(halfmove counter 100, so the base tree's drawn-root shortcut applies)")
emit("")
emit("| build | command | nodes | info depth lines | bestmove | info string |")
emit("|---|---|---|---|---|---|")
rows = {}
for label, exe in (("base 6b98f217", BASE), ("PC r15", PC)):
    for cmd, go in (("searchmoves mate", "go searchmoves %s depth 4" % mating_move),
                    ("CONTROL no searchmoves", "go depth 4"),
                    ("CONTROL illegal name", "go searchmoves a1a8 depth 4")):
        r = run(exe, fen, go)
        rows[(label, cmd)] = r
        emit("| %s | %s | **%s** | %d | %s | %s |" %
             (label, cmd, f"{r['nodes']:,}" if r.get("nodes") is not None else "-",
              r.get("n_info", 0), r.get("bm"), "; ".join(x[:40] for x in r.get("strings", [])) or "-"))

emit("")
emit("## The claim, tested")
emit("")
emit("| their statement | my measurement |")
emit("|---|---|")
base_sm = rows[("base 6b98f217", "searchmoves mate")]
pc_sm = rows[("PC r15", "searchmoves mate")]
emit("| base build answers 0 nodes for the searchmoves line at halfmove 100 | **%s nodes** |" %
     (f"{base_sm['nodes']:,}" if base_sm.get("nodes") is not None else "-"))
emit("| PC build SEARCHES it (small nonzero node count) | **%s nodes** |" %
     (f"{pc_sm['nodes']:,}" if pc_sm.get("nodes") is not None else "-"))
pc_il = rows[("PC r15", "CONTROL illegal name")]
emit("| the no-legal-named-move case is unchanged on PC (0000 + info line, 0 nodes) | bestmove **%s**, info string %s |" %
     (pc_il.get("bm"), "present" if pc_il.get("strings") else "ABSENT"))
emit("")
pc_base_ctrl = rows[("base 6b98f217", "CONTROL no searchmoves")]
pc_pc_ctrl = rows[("PC r15", "CONTROL no searchmoves")]
emit("| CONTROL: without searchmoves, both builds handle the position the same way | base %s nodes / PC %s nodes |" %
     (f"{pc_base_ctrl.get('nodes'):,}" if pc_base_ctrl.get("nodes") is not None else "-",
      f"{pc_pc_ctrl.get('nodes'):,}" if pc_pc_ctrl.get("nodes") is not None else "-"))
emit("")
if (base_sm.get("nodes") == 0 and pc_sm.get("nodes") and pc_sm["nodes"] > 0
        and pc_il.get("bm") == "0000" and pc_il.get("strings")):
    emit("**CONFIRMS**: the PC build's repair reaches `searchmoves` (0 nodes on base, %d on PC) while the "
         "no-legal-named-move case still short-circuits with 0000 and the info string." % pc_sm["nodes"])
else:
    emit("**PARTIAL or NOT CONFIRMED** — see the table; the three conditions above are not all met.")

with open(OUT, "w") as fh:
    fh.write("\n".join(out) + "\n")
