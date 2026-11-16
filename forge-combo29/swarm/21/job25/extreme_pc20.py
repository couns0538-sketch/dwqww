#!/usr/bin/env python3
"""extreme_pc20.py OUTDIR

Area 1 job 2's extreme-field cases on the PC build under PC20, Threads 1, plus the base build
under default options as the comparison. Fresh process per case; the FEN acceptance and a
`nodes` value are both asserted (19-F12 + integrity rules).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, bestmove_of, last_info  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

B = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - {hm} {fm}"
CASES = [
    ("hm_0", B.format(hm=0, fm=1)), ("hm_99", B.format(hm=99, fm=1)),
    ("hm_100", B.format(hm=100, fm=1)), ("hm_150", B.format(hm=150, fm=1)),
    ("hm_9999", B.format(hm=9999, fm=1)), ("hm_2p31", B.format(hm=2147483648, fm=1)),
    ("hm_neg1", B.format(hm=-1, fm=1)),
    ("fm_0", B.format(hm=0, fm=0)), ("fm_1", B.format(hm=0, fm=1)),
    ("fm_1e9", B.format(hm=0, fm=1000000000)), ("fm_neg1", B.format(hm=0, fm=-1)),
    ("ep_e3", "r3k2r/pppppppp/8/8/8/4P3/PPPP1PPP/R3K2R w KQkq e3 0 1"),
    ("ep_z3", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq z3 0 1"),
    ("two_kings", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K1KR w KQkq - 0 1"),
    ("no_kings", "r7/pppppppp/8/8/8/8/PPPPPPPP/R7 w KQkq - 0 1"),
    ("pawn_rank1", "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/P3K2R w kq - 0 1"),
    ("mate_hm100", "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60"),
]


def perft2(bd):
    t = 0
    for m in bd.legal_moves:
        c = bd.copy()
        c.push(m)
        t += c.legal_moves.count()
    return t


def run(exe, outdir, tag, fen, opts):
    e = SafeEngine(exe, os.path.join(outdir, tag + "_raw.txt"), hash_mb=16, threads=1)
    for n, v in opts:
        e.send("setoption name %s value %s" % (n, v))
        e.send("isready")
        e.wait_for("readyok")
    if opts:
        e.send("ucinewgame")
        e.send("isready")
        e.wait_for("readyok")
    ans = e.position("position fen " + fen)
    refused = any("invalid FEN" in l for l in ans)
    nodes = None
    info = ""
    bm = ""
    if not refused:
        gl = e.go("go depth 4", timeout=90)
        bm = bestmove_of(gl)
        info = last_info(gl)
        m = re.search(r" nodes (\d+)", info)
        nodes = int(m.group(1)) if m else None
        pl = e.go("go perft 2", token="nodes", timeout=120)
        pv = [int(l.split()[1]) for l in pl if l.startswith("nodes ")]
        if not pv:
            e.close()
            raise AssertionError("%s: no nodes for perft" % tag)
        p2 = pv[0]
    else:
        p2 = None
    e.close()
    try:
        py = perft2(chess.Board(fen))
    except Exception:
        py = None
    return dict(fen=fen, refused=refused, nodes=nodes, bestmove=bm, info=info,
                perft2=p2, py=py)


def main():
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    pc = os.path.expanduser("~/b/pc_asan/forge")
    base = os.path.expanduser("~/b/asan/forge")
    R = {}
    rows = ["| case | PC20: refused | PC20: nodes | PC20: perft2 | python perft2 | base: refused | base: nodes |",
            "|---|---|---|---|---|---|---|"]
    for tag, fen in CASES:
        rp = run(pc, outdir, "pc_" + tag, fen, S14 + PC20_EXTRA)
        rb = run(base, outdir, "base_" + tag, fen, [])
        R[tag] = dict(pc=rp, base=rb)
        rows.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            tag, rp["refused"], rp["nodes"], rp["perft2"], rp["py"],
            rb["refused"], rb["nodes"]))
    # assertions from the prediction
    q = {
        "P1 PC still refuses fullmove 0": R["fm_0"]["pc"]["refused"],
        "P2 PC refuses negative clocks and accepts 2^31 halfmove":
            R["hm_neg1"]["pc"]["refused"] and R["fm_neg1"]["pc"]["refused"]
            and not R["hm_2p31"]["pc"]["refused"],
        "P3 PC searches every halfmove >= 100 (nodes > 0)":
            all((R[t]["pc"]["nodes"] or 0) > 0 for t in ("hm_100", "hm_150", "hm_9999", "hm_2p31", "mate_hm100")),
        "P4 PC still refuses ep/two-kings/no-kings/pawn-rank1":
            all(R[t]["pc"]["refused"] for t in ("ep_e3", "ep_z3", "two_kings", "no_kings", "pawn_rank1")),
        "P5 PC perft2 == python on every accepted case":
            all(R[t]["pc"]["perft2"] == R[t]["pc"]["py"]
                for t in R if not R[t]["pc"]["refused"]),
    }
    text = "\n".join(rows) + "\n\n| question | outcome |\n|---|---|\n"
    for k, v in q.items():
        text += "| %s | %s |\n" % (k, "yes" if v else "NO")
    with open(os.path.join(outdir, "summary.md"), "w") as fh:
        fh.write(text)
    with open(os.path.join(outdir, "summary.json"), "w") as fh:
        json.dump(R, fh, indent=1)
    print(text)


if __name__ == "__main__":
    main()