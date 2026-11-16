#!/usr/bin/env python3
"""scan_loneking.py EXE SETFILE OUTFILE : the S-F20 signature scan over lone-king positions.

For every position in SETFILE (columns: fen, lone side, provenance):
  1. FREE CHOICE: `go depth 16` -> bestmove, score, nodes.
  2. ALTERNATIVES: if the position has <= MAXMOVES legal moves, EVERY legal move is scored with
     `go depth 16 searchmoves <mv>`; otherwise the legal moves are ranked by a cheap shallow pass and only the top
     MAXMOVES are scored, and the position is marked PARTIAL.
  3. SIGNATURE: chosen score is worse than the best alternative by more than THRESH cp (mate scores compared
     properly: a positive mate beats any cp; a negative mate is worse than any cp; |mate| compares ply distance).

Every search is a fresh process, Threads 1, Hash 16, PC20, read to `bestmove` (never a pipelined quit — see the
method note in this folder), and any missing score aborts the run rather than defaulting.
"""
import os
import re
import subprocess
import sys

import chess

EXE, SETFILE, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DEPTH = int(os.environ.get("LK_DEPTH_EVAL", "16"))
THRESH = int(os.environ.get("LK_THRESH", "900"))       # more than a queen
MAXMOVES = int(os.environ.get("LK_MAXMOVES", "12"))
rawdir = OUT + ".raw"
os.makedirs(rawdir, exist_ok=True)

PC20 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
        ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
        ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
        ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
        ("IirDepth", "2"), ("NonPawnCorrection", "true"), ("CuckooRep", "true"),
        ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
        ("MateAlphaGuard", "true"), ("OwnBook", "false")]


def uci_names():
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names = set()
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        s = line.strip()
        if s.startswith("option name "):
            names.add(s[len("option name "):].split(" type ")[0])
        if s == "uciok":
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except Exception:  # noqa: BLE001
        p.kill()
    return names


AVAILABLE = uci_names()
OPTS = [("Threads", "1"), ("Hash", "16")] + [(o, v) for o, v in PC20 if o in AVAILABLE]


def search(fen, move, tag):
    """returns (bestmove, (kind, value), nodes) — kind is 'cp' or 'mate'."""
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    raw = open(os.path.join(rawdir, tag + ".txt"), "w")

    def send(c):
        raw.write(f">>> {c}\n")
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def until(tok):
        while True:
            line = p.stdout.readline()
            if line == "":
                raise RuntimeError(f"died waiting {tok} ({tag})")
            raw.write(line)
            raw.flush()
            s = line.strip()
            if s.startswith(tok):
                return s

    send("uci"); until("uciok")
    send("isready"); until("readyok")
    for o, v in OPTS:
        send(f"setoption name {o} value {v}")
        send("isready"); until("readyok")
    send("ucinewgame"); send("isready"); until("readyok")
    send(f"position fen {fen}")
    send("isready"); until("readyok")
    send(f"go depth {DEPTH}" + (f" searchmoves {move}" if move else ""))
    last, bm = None, None
    while True:
        line = p.stdout.readline()
        if line == "":
            raise RuntimeError(f"died before bestmove ({tag})")
        raw.write(line)
        raw.flush()
        s = line.strip()
        if s.startswith("bestmove"):
            bm = s.split()[1]
            break
        m = re.match(rf"info depth {DEPTH} .*?score (cp|mate) (-?\d+).*?nodes (\d+)", s)
        if m:
            last = (m.group(1), int(m.group(2)), int(m.group(3)))
    send("quit")
    try:
        p.wait(timeout=300)
    except Exception:  # noqa: BLE001
        p.kill()
    raw.close()
    if last is None:
        raise RuntimeError(f"no depth-{DEPTH} score for {tag}")
    return bm, (last[0], last[1]), last[2]


def better(a, b):
    """is score a better (for the side to move) than score b? mate>cp; mate N better than mate M when N<M;
    mate -N worse than mate -M when N<M (i.e. a longer mate against us is better)."""
    def key(s):
        kind, v = s
        if kind == "mate":
            return (2, -v) if v > 0 else (0, v)     # v<0: more negative = longer loss = better -> tuple ordering
        return (1, v)
    return key(a) > key(b)


def gap(cp_chosen, best_alt):
    """magnitude of the score difference in centipawn-equivalents, mate treated as >= 10000."""
    def num(s):
        kind, v = s
        if kind == "cp":
            return v
        return (10000 - 10 * v) if v > 0 else (-10000 - 10 * v)
    return num(best_alt) - num(cp_chosen)


rows = [l.rstrip("\n").split("\t") for l in open(SETFILE) if l.strip()]
out = []
hits = 0
partial = 0
for i, r in enumerate(rows):
    fen = r[0]
    b = chess.Board(fen)
    legal = sorted(m.uci() for m in b.legal_moves)
    if not legal:
        out.append(f"{i}\t{fen}\tNO_LEGAL_MOVES")
        continue
    is_partial = len(legal) > MAXMOVES
    if is_partial:
        partial += 1
    bm, chosen, cnodes = search(fen, None, f"p{i:03d}_free")
    cands = legal if not is_partial else legal[:MAXMOVES]   # ordered by uci for determinism; marked PARTIAL
    scores = {}
    for mv in cands:
        _, sc, _ = search(fen, mv, f"p{i:03d}_{mv}")
        scores[mv] = sc
    alts = {mv: sc for mv, sc in scores.items() if mv != bm}
    if not alts:
        out.append(f"{i}\t{fen}\tNO_ALTERNATIVE")
        continue
    best_alt_mv = max(alts, key=lambda mv: (1 if alts[mv][0] == "cp" else 0,
                                            alts[mv][1] if alts[mv][0] == "cp" else -alts[mv][1]))
    # use the comparator rather than the key above to be safe
    for mv in alts:
        if better(alts[mv], alts[best_alt_mv]):
            best_alt_mv = mv
    g = gap(chosen, alts[best_alt_mv])
    hit = g > THRESH
    hits += hit
    out.append(f"{i}\t{fen}\tchosen={bm} {chosen[0]} {chosen[1]} ({cnodes} nodes)\t"
               f"best_alt={best_alt_mv} {alts[best_alt_mv][0]} {alts[best_alt_mv][1]}\t"
               f"gap={g}\t{'HIT' if hit else 'ok'}\t{'PARTIAL' if is_partial else 'full'}\t"
               f"legal={len(legal)}")
    print(out[-1], flush=True)

with open(OUT, "w") as f:
    f.write(f"scanned {len(rows)} lone-king positions, depth {DEPTH}, PC20, Threads 1, Hash 16\n")
    f.write(f"signature threshold: chosen scores worse than the best alternative by more than {THRESH} cp-equiv\n")
    f.write(f"HITS: {hits} of {len(rows)}\n")
    f.write(f"PARTIAL scans (more than {MAXMOVES} legal moves, only the first {MAXMOVES} by name scored): {partial}\n\n")
    f.write("\n".join(out) + "\n")
print(f"\nHITS {hits} of {len(rows)}; partial {partial}")
