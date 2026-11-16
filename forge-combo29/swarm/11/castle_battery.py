#!/usr/bin/env python3
"""castle_battery.py EXE : engine vs python-chess perft 3 on castling-broken FENs.

Only FENs the engine ACCEPTS are compared to python-chess (a refused FEN has no board).
Any row with engine != python-chess is the "trusted castling" class.
"""
import subprocess, sys, chess

EXE = sys.argv[1]
FENS = [
    ("startpos", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
    ("startpos-no-rights", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"),
    ("R3K2R-clean", "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"),
    ("R3K2R-norights", "r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1"),
    ("rooks-but-no-black-rights", "r3k2r/8/8/8/8/8/8/R3K2R w KQ - 0 1"),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("kings-not-home-claim", "4k3/8/8/8/8/8/8/4K3 w KQkq - 0 1"),
    ("rook-a1-only-claim-KQ", "4k3/8/8/8/8/8/8/R3K3 w KQ - 0 1"),
    ("black-king-moved-claim", "r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1"),
    ("white-queenside-blocked", "r3k2r/8/8/8/8/8/8/R1B1K2R w KQkq - 0 1"),
    ("bishop-b1", "r3k2r/8/8/8/8/8/8/RB2K2R w KQkq - 0 1"),
    ("knight-g1", "r3k2r/8/8/8/8/8/8/R3K1NR w KQkq - 0 1"),
    ("king-in-check-claim", "r3k2r/8/8/8/8/5r2/8/R3K2R w KQkq - 0 1"),
    ("full-rights-extra-queen", "r3k2r/8/8/8/8/8/8/R2QK2R w KQkq - 0 1"),
]


def engine_perft(fen, depth=3):
    p = subprocess.run([EXE], input=f"uci\nposition fen {fen}\nisready\ngo perft {depth}\nquit\n",
                       capture_output=True, text=True, timeout=60)
    out = p.stdout
    if "invalid FEN" in out:
        return None, out
    for line in out.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1]), out
    return None, out


def py_perft(b, d):
    if d == 0:
        return 1
    s = 0
    for m in b.legal_moves:
        b.push(m); s += py_perft(b, d - 1); b.pop()
    return s


print(f"{'case':30} {'engine':>9} {'py-chess':>9}  verdict")
diffs = 0
for name, fen in FENS:
    eng, raw = engine_perft(fen)
    try:
        b = chess.Board(fen)
        py = py_perft(b, 3)
    except Exception as e:
        py = f"REFUSED"
    if eng is None:
        print(f"{name:30} {'REFUSED':>9} {str(py):>9}  engine refuses (no board)")
        continue
    verdict = "EQUAL" if eng == py else "*** DIFFERS ***"
    if eng != py:
        diffs += 1
    print(f"{name:30} {eng:9d} {py if isinstance(py,int) else py:>9}  {verdict}")
print("\ndiffering cases:", diffs)
