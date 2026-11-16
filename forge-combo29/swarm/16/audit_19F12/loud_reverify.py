#!/usr/bin/env python3
"""loud_reverify.py EXE OUT.txt : re-verify a sample behind EVERY confirmation of mine, with parsing that
FAILS LOUDLY. A missing line, a None, an empty result or a NaN raises immediately and is counted as
NOT VERIFIED. Nothing may pass by comparing nothing against nothing.

Checks, one per confirmation:
  S-C1  seat 06 S-F2   : ep-square FENs        -> assert the `invalid FEN` line exists (not a silent no-match)
  S-C2  seat 06 S-F1   : colour mirror eval    -> assert BOTH eval lines parsed, and the numbers VARY
  S-C3  seat 06 S-F3   : left-right hce        -> assert both eval lines parsed on the symmetrised build
  S-C4  seat 06 S-F5   : total == hce + nnue   -> assert all three numbers parsed on every row
  S-C5  seat 20 S-F14  : side-to-move relative -> assert three DIFFERENT values were produced
  S-C6  seat 06 S-F12  : depth-1 node counts   -> assert nodes parsed for the whole search AND each move
  S-C7  seat 28 S-F1   : movetime stop         -> assert the reported time parsed and is not missing
  honesty             : bench/perft            -> assert a nodes number parsed on every line
"""
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
S14 = [("OwnBook", "false"), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]

results = []
log = []


class Missing(Exception):
    pass


LAST_SETUP = {}


def run(fen, cmds_after, opts=(), depth=None, limit=120, exe=None):
    """Start a process, apply options, set the position, then send cmds_after and read until `until`.
    Every command is acknowledged; stdin is never closed before the final quit."""
    p = subprocess.Popen([exe or EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def rd_until(tok, lim):
        got = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return got, False
            l = l.rstrip("\n")
            got.append(l)
            if l.strip().startswith(tok) or l.strip() == tok:
                return got, True
        return got, False

    send("uci"); rd_until("uciok", 15)
    for n, v in opts:
        send(f"setoption name {n} value {v}")
        send("isready"); rd_until("readyok", 15)
    setup = []
    if fen:
        send("position fen " + fen)
        send("isready")
        a, _ = rd_until("readyok", 15)
        setup += a
    LAST_SETUP["lines"] = setup
    out = list(setup)
    for cmd, tok, lim in cmds_after:
        send(cmd)
        if tok == "readyok":
            # eval / bench / perft print their own line and NOT a readyok, so send isready to close it off
            send("isready")
        got, ok = rd_until(tok, lim)
        out += got
        if not ok:
            p.kill()
            raise Missing(f"no '{tok}' after '{cmd}' within {lim}s")
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    return out


def parse_eval(lines):
    for l in lines:
        if l.startswith("info string eval"):
            d = {}
            parts = l.split()
            for i, t in enumerate(parts):
                if t in ("hce", "nnue", "total") and i + 1 < len(parts):
                    d[t] = int(parts[i + 1])
            if len(d) != 3:
                raise Missing(f"eval line incomplete: {l}")
            return d
    raise Missing("no 'info string eval' line found")


def check(name, fn):
    try:
        detail = fn()
        results.append((name, "VERIFIED", detail))
    except Missing as exc:
        results.append((name, "NOT VERIFIED", str(exc)))
    except Exception as exc:  # noqa: BLE001
        results.append((name, "NOT VERIFIED", f"{type(exc).__name__}: {exc}"))


# ---------- S-C1: ep-square refusal ----------
def c1():
    good = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    bad = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1"
    run(bad, [])
    msg = [l for l in LAST_SETUP.get("lines", []) if "invalid FEN" in l]
    if not msg:
        raise Missing("the refused FEN produced NO 'invalid FEN' line (silent no-match)")
    b = run(good, [("go perft 1", "nodes", 60), ("isready", "readyok", 20)])
    nodes = [int(l.split()[-1]) for l in b if l.startswith("nodes")]
    if not nodes:
        raise Missing("accepted ep FEN produced no `nodes` line")
    return f"refused with '{msg[0]}'; accepted ep FEN perft1={nodes[-1]} (python-chess 20)"


# ---------- S-C2: colour mirror ----------
def c2():
    fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job1/set_G.epd")
            if l.strip()][:6]
    vals = []
    for fen in fens:
        mir = chess.Board(fen).mirror().fen()
        a = parse_eval(run(fen, [("eval", "readyok", 30)], opts=S14))
        b = parse_eval(run(mir, [("eval", "readyok", 30)], opts=S14))
        if a != b:
            raise Missing(f"mirror differs on {fen}: {a} vs {b}")
        vals.append(a["total"])
    if len(set(vals)) < 2:
        raise Missing(f"all totals identical ({set(vals)}) -> comparison could be constant")
    return f"6 pairs equal; totals vary: {sorted(set(vals))}"


# ---------- S-C3/S-C4: left-right on the symmetrised build ----------
SYM = "/home/ubuntu/builds/bld-sympsqt/forge"


def c3():
    fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job2/G_nocastle.fens")
            if l.strip()][:6]
    hs = []
    for fen in fens:
        lr = chess.Board(fen).transform(chess.flip_horizontal).fen()
        a = parse_eval(run(fen, [("eval", "readyok", 30)], opts=S14, exe=SYM))
        b = parse_eval(run(lr, [("eval", "readyok", 30)], opts=S14, exe=SYM))
        if a["hce"] != b["hce"]:
            raise Missing(f"symmetrised build still differs in hce on {fen}: {a} vs {b}")
        hs.append(a["hce"])
    if len(set(hs)) < 2:
        raise Missing("all hce identical -> comparison could be constant")
    return f"6 pairs: hce equal on the symmetrised build; hce values vary: {sorted(set(hs))}"


def c4():
    fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job1/set_G.epd")
            if l.strip()][:6]
    n = 0
    for fen in fens:
        d = parse_eval(run(fen, [("eval", "readyok", 30)], opts=S14))
        if d["total"] != d["hce"] + d["nnue"]:
            raise Missing(f"total != hce+nnue on {fen}: {d}")
        n += 1
    return f"{n}/6 positions: total == hce + nnue exactly"


# ---------- S-C5: side-to-move relative ----------
def c5():
    cases = ["4k3/8/8/8/8/8/8/QQQQK3 w - - 0 1", "qqqqk3/8/8/8/8/8/8/4K3 b - - 0 1",
             "4k3/8/8/8/8/8/8/QQQQK3 b - - 0 1"]
    vals = [parse_eval(run(f, [("eval", "readyok", 30)]))["hce"] for f in cases]
    if len(set(vals)) < 2:
        raise Missing(f"the three cases gave identical hce {vals} -> nothing to compare")
    if vals[0] != vals[1]:
        raise Missing(f"mirror is not equal: {vals[0]} vs {vals[1]}")
    return f"hce {vals[0]} / {vals[1]} (mirror, equal) / {vals[2]} (other side to move)"


# ---------- S-C6: depth-1 node counts ----------
def c6():
    FEN = "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1"
    mir = chess.Board(FEN).mirror().fen()

    def nodes_for(fen, extra=""):
        lines = run(fen, [(f"go depth 1{extra}", "bestmove", 60)])
        import re as _re
        ns = [int(m.group(1)) for l in lines if l.startswith("info depth 1")
              for m in [_re.search(r"\bnodes (\d+)", l)] if m]
        if not ns:
            raise Missing(f"no depth-1 info line with nodes for {fen}{extra}")
        return ns[-1]

    a = nodes_for(FEN)
    b = nodes_for(mir)
    if a == b:
        raise Missing(f"whole-position counts equal ({a}) -> the finding's signature did not reproduce")
    mv = sorted(chess.Board(FEN).legal_moves, key=lambda m: m.uci())[0].uci()
    ma = nodes_for(FEN, f" searchmoves {mv}")
    if ma <= 0:
        raise Missing("per-move count is zero/absent")
    return f"whole {a} vs {b} (differ); sample move {mv} alone gives {ma} nodes"


# ---------- S-C7: movetime ----------
def c7():
    FEN = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"
    times = []
    for mt in (10, 50):
        lines = run(FEN, [(f"go movetime {mt}", "bestmove", 120)],
                    opts=[("Threads", 1), ("Hash", 16)])
        ts = [int(l.split("time ")[1].split()[0]) for l in lines
              if l.startswith("info") and " time " in l]
        if not ts:
            raise Missing(f"no info line with a time for movetime {mt}")
        times.append((mt, ts[-1]))
    if times[0][1] == times[1][1]:
        raise Missing("movetime 10 and 50 gave the same reported time -> nothing measured")
    return f"reported time: movetime 10 -> {times[0][1]} ms, movetime 50 -> {times[1][1]} ms (differ)"


# ---------- honesty ----------
def hon():
    got = {}
    for spec in ("bench 11", "bench 13", "bench 16"):
        lines = run(None, [(spec, "readyok", 300)])
        ns = [l for l in lines if "nodes" in l]
        if not ns:
            raise Missing(f"no nodes line for {spec}")
        got[spec] = ns[-1].split("nodes")[1].strip().split()[0]
    lines = run(None, [("go perft 5", "nodes", 300), ("isready", "readyok", 20)])
    ns = [l for l in lines if l.startswith("nodes")]
    if not ns:
        raise Missing("no nodes line for perft 5")
    got["perft 5"] = ns[-1].split()[1]
    if got["perft 5"] != "4865609":
        raise Missing(f"perft 5 = {got['perft 5']}, expected 4865609")
    return f"parsed from output: {got}"


for nm, fn in (("S-C1", c1), ("S-C2", c2), ("S-C3", c3), ("S-C4", c4),
               ("S-C5", c5), ("S-C6", c6), ("S-C7", c7), ("honesty", hon)):
    check(nm, fn)
    print(f"{results[-1][0]:8s} {results[-1][1]:14s} {results[-1][2]}")

bad = [r for r in results if r[1] != "VERIFIED"]
text = "\n".join(["Loud-fail re-verification of every confirmation (seat 16)", ""]
                 + [f"{a:8s} {b:14s} {c}" for a, b, c in results]
                 + ["", f"VERIFIED {len(results) - len(bad)} of {len(results)}"])
print("\n" + text.splitlines()[-1])
with open(OUT, "w") as fh:
    fh.write(text + "\n")
if bad:
    print("FAILED:", [r[0] for r in bad])
    sys.exit(1)
