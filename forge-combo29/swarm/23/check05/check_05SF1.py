#!/usr/bin/env python3
"""check_05SF1.py : independent check of swarm seat 05's S-F1.

Claim: on `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` at depth 12 the engine reports `score mate -12`
(a promise of mate in 24 plies), but the PV it prints is 18 plies and does not end in checkmate; deeper
searches abandon -12 for -9, -6, -4.

My own harness (not theirs). Everything is drained to `bestmove` before the next command, so the
fabricated-0-node answer cannot intrude (19-F12).
For each depth it records the last `info depth D` line, whether a `mate` score is present, the PV length in
plies, and whether playing the PV out actually ends in checkmate (python-chess replays it).

usage: check_05SF1.py EXE OPTFILE OUTPREFIX [FEN]
  OPTFILE may be empty string for "no options".
"""
import re
import subprocess
import sys

import chess

EXE, OPTFILE, OUTPREFIX = sys.argv[1], sys.argv[2], sys.argv[3]
FEN = sys.argv[4] if len(sys.argv) > 4 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
DEPTHS = [12, 14, 16, 18, 20]

LAST = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?(?: pv (.*))?$")


def replay_pv(fen, pv):
    """play the PV with python-chess; return (plies_played, ends_in_mate, error)."""
    b = chess.Board(fen)
    plies = 0
    for uci in pv.split():
        try:
            m = chess.Move.from_uci(uci)
        except ValueError:
            return plies, False, "bad uci %s" % uci
        if m not in b.legal_moves:
            return plies, False, "illegal %s at ply %d" % (uci, plies + 1)
        b.push(m)
        plies += 1
    return plies, b.is_checkmate(), None


def start():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("died in uci")
        s = line.strip()
        if s.startswith("option name "):
            names.add(s.split("option name ")[1].split(" type ")[0])
        if s == "uciok":
            break
    opts = []
    if OPTFILE:
        opts = [l.strip() for l in open(OPTFILE) if l.strip() and not l.startswith("#")]
        for line in opts:
            name = line.split("name ")[1].split(" value ")[0]
            if name not in names:
                raise RuntimeError("STOP: %r not in uci list" % name)
            p.stdin.write(line + "\n"); p.stdin.flush()
            p.stdin.write("isready\n"); p.stdin.flush()
            while p.stdout.readline().strip() != "readyok":
                pass
    return p, opts


rows = []
p, opts = start()
print("exe %s" % EXE)
print("options %s" % (opts if opts else "none"))
print("fen %s" % FEN)
print()
print("| depth | score | mate promise (plies) | PV plies | PV ends in mate | consistent |")
print("|---|---|---|---|---|---|")
for d in DEPTHS:
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen %s\n" % FEN); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip() != "readyok":
        pass
    p.stdin.write("go depth %d\n" % d); p.stdin.flush()
    last = None
    bm = None
    while True:
        line = p.stdout.readline()
        if not line:
            raise RuntimeError("died in search")
        s = line.strip()
        m = LAST.match(s)
        if m:
            last = (int(m.group(1)), m.group(2), int(m.group(3)), m.group(4) or "")
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
    if last is None:
        print("| %d | NO INFO LINE | - | - | - | - |" % d)
        continue
    depth, kind, val, pv = last
    plies, mate, err = replay_pv(FEN, pv)
    if kind == "mate":
        need = 2 * abs(val) - 1 if val > 0 else 2 * abs(val)
        consistent = "yes" if (mate and plies == need) else "NO (needs %d plies)" % need
        promise = "%d" % need
    else:
        consistent = "n/a (cp score)"
        promise = "-"
    print("| %d | %s %d | %s | %d | %s | %s |" % (d, kind, val, promise, plies, mate, consistent))
    rows.append({"depth": d, "kind": kind, "score": val, "promise": promise,
                 "pv_plies": plies, "pv_mate": mate, "pv": pv, "bestmove": bm,
                 "pv_error": err})

p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except subprocess.TimeoutExpired:
    p.kill()

with open(OUTPREFIX + ".raw.txt", "w") as f:
    f.write("fen %s\n" % FEN)
    for r in rows:
        f.write("depth %d kind=%s score=%d promise=%s pv_plies=%d pv_mate=%s bestmove=%s pv_error=%s\npv %s\n"
                % (r["depth"], r["kind"], r["score"], r["promise"], r["pv_plies"], r["pv_mate"],
                   r["bestmove"], r["pv_error"], r["pv"]))
print()
print("raw rows -> %s.raw.txt" % OUTPREFIX)
