#!/usr/bin/env python3
"""pcsym.py EXE OUT.txt [CONFIG...] : colour-mirror symmetry on the PC build under PC20 and each option removed.

For every configuration and depth: searches each position and its colour mirror, one fresh process each,
`ucinewgame` before the search, Threads 1 (swarm rule), and reports how many mirror pairs have equal node
counts / equal scores / equal (mirrored) bestmoves.
A missing score, a missing option or a refused setoption FAILS LOUDLY (seat 19's rule): nothing may pass by
comparing nothing.
"""
import re
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
DEPTHS = [1, 2]
NPOS = 20

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = {"CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
              "MateAlphaGuard": "true", "OwnBook": "false"}
FOUR = ["CuckooRep", "HistRework", "TtPruneV2", "CorrHistV2"]

CONFIGS = [
    ("pc20", {}),
    ("no_cuckoo", {"CuckooRep": "false"}),
    ("no_histrework", {"HistRework": 0}),
    ("no_ttprune", {"TtPruneV2": "false"}),
    ("no_corrhist", {"CorrHistV2": "false"}),
    ("all_four_off", {k: ("false" if k != "HistRework" else 0) for k in FOUR}),
    ("s14_only", {**{k: v for k, v in PC20_EXTRA.items() if k not in FOUR}}),
]


class Missing(Exception):
    pass


def search(fen, depth, opts):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=240):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    send("uci")
    uci, ok = to("uciok", 20)
    if not ok:
        raise Missing("no uciok")
    known = set()
    for l in uci:
        m = re.match(r"option name (.*) type ", l)
        if m:
            known.add(m.group(1))
    send("isready"); to("readyok", 20)
    for name, val in opts.items():
        if name not in known:
            raise Missing(f"option {name} not in the exe's uci list")
        send(f"setoption name {name} value {val}")
        send("isready")
        got, ok = to("readyok", 20)
        if not ok:
            raise Missing(f"no readyok after setoption {name}")
        for l in got:
            low = l.lower()
            if "unknown option" in low or "invalid value" in low:
                raise Missing(f"option refused: {l}")
    send("ucinewgame")
    send("isready"); to("readyok", 20)
    send("position fen " + fen)
    send("isready"); to("readyok", 20)
    send(f"go depth {depth}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    nodes = score = best = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(rf"^info depth {depth} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = f"{m.group(1)} {m.group(2)}"
            nodes = int(m.group(3))
    if nodes is None or score is None:
        raise Missing(f"no depth-{depth} score+nodes")
    if best is None:
        raise Missing("no bestmove")
    return nodes, score, best


def back(mv):
    if not mv or mv == "0000":
        return None
    m = chess.Move.from_uci(mv)
    return chess.Move(m.from_square ^ 56, m.to_square ^ 56, m.promotion).uci()


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/pcsym/G_nocastle.fens")
        if l.strip()][:NPOS]
base_opts = {**S14, **PC20_EXTRA}
out = [f"exe {EXE}", f"positions {len(fens)}", "Threads 1 (swarm rule), Hash 16, fresh process + ucinewgame per search", ""]
print(out[0])

for cname, override in CONFIGS:
    opts = dict(base_opts)
    opts.update(override)
    opts["Threads"] = 1
    opts["Hash"] = 16
    for depth in DEPTHS:
        try:
            eq_n = eq_s = eq_b = 0
            tot = 0
            for fen in fens:
                mir = chess.Board(fen).mirror().fen()
                na, sa, ba = search(fen, depth, opts)
                nb, sb, bb = search(mir, depth, opts)
                eq_n += (na == nb)
                eq_s += (sa == sb)
                eq_b += (ba == back(bb))
                tot += 1
            line = (f"{cname:14s} depth {depth} | nodes equal {eq_n:2d}/{tot} | score equal {eq_s:2d}/{tot} "
                    f"| bm equal {eq_b:2d}/{tot}")
        except Missing as exc:
            line = f"{cname:14s} depth {depth} | NOT MEASURED: {exc}"
        out.append(line)
        print(line)

text = "\n".join(out) + "\n"
with open(OUT, "w") as fh:
    fh.write(text)
