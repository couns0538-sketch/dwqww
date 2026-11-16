#!/usr/bin/env python3
"""seat 17: re-run my own base-tree findings on the PC r15 build under PC20.

Each finding is re-tested with the SAME driver, on the PC build, with PC20 sent first:
  S14 (14 settings) + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
  MateAlphaGuard true, OwnBook false.

A finding that is gone on PC20 is "repaired on the PC"; one that is still there is worth more.

usage: pc_recheck.py <pc_exe> <base_exe> <outdir>
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, "/agent/repos/dwqww/forge-combo29/swarm/17/job1")
from uci_driver import run_one

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
PC20 = S14 + PC20_EXTRA


def pc20_lines():
    out = []
    for name, value in PC20:
        out += ["setoption name %s value %s" % (name, value), "isready"]
    return out


def cases():
    """(id, label, position, go, what would show the fault)."""
    return [
        ("S-F1", "no-legal-match searchmoves answers 0000 on a live position",
         "position startpos", "go depth 5 searchmoves e7e5"),
        ("S-F1b", "same, Black to move",
         "position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
         "go depth 5 searchmoves e2e4"),
        ("S-F8", "no-match searchmoves prints N depth lines all nodes 0",
         "position startpos", "go nodes 1000 searchmoves e7e5"),
        ("S-C11", "halfmove 100 with a mate in 1: a1a8 at 99, missed at 100",
         "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1", "go depth 5"),
        ("S-C11b", "control at halfmove 99 (should be mate 1, a1a8)",
         "position fen 6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 99 1", "go depth 5"),
        ("S-C10", "fullmove 0 refused -> old board (startpos perft 1 = 20)",
         "position fen 4k3/8/8/8/8/8/8/4K3 w - - 0 0", "go perft 1"),
        ("S-F9", "Hash resizing: same bestmove, nodes converge",
         "position fen 1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1", "go depth 12"),
    ]


def one(exe, opts_lines, position, go, log):
    cmds = ["uci", "isready"] + opts_lines + ["position " + position.split(" ", 1)[1] if position.startswith("position ") else position,
                                              "isready", go]
    info = run_one(exe, cmds, 180, log)
    text = open(log).read()
    depths = [ln for ln in text.splitlines() if ln.startswith("info depth")]
    nodes = [int(ln.split(" nodes ")[1].split()[0]) for ln in depths if " nodes " in ln]
    # perft style output
    perft_nodes = [int(ln.split()[1]) for ln in text.splitlines() if ln.startswith("nodes ")]
    return {
        "bestmove": info["bestmove"],
        "info_depth_lines": len(depths),
        "max_nodes": max(nodes) if nodes else (perft_nodes[-1] if perft_nodes else None),
        "complaints": [ln for ln in text.splitlines()
                       if "unknown option" in ln or "invalid value" in ln],
    }


def main():
    pc_exe, base_exe, outdir = sys.argv[1:4]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for cid, label, position, go in cases():
        log_pc = os.path.join(outdir, "%s_pc20.log" % cid)
        pc = one(pc_exe, pc20_lines(), position, go, log_pc)
        log_base = os.path.join(outdir, "%s_base.log" % cid)
        # base tree: S14 only (no PC20-only options exist there)
        base_opts = []
        for name, value in S14:
            base_opts += ["setoption name %s value %s" % (name, value), "isready"]
        base = one(base_exe, base_opts, position, go, log_base)
        row = {"id": cid, "label": label, "position": position, "go": go,
               "pc20": pc, "base_s14": base}
        rows.append(row)
        print(json.dumps(row), flush=True)
    json.dump(rows, open(os.path.join(outdir, "recheck.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
