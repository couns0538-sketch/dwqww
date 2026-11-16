#!/usr/bin/env python3
"""rerun_f1_on_pc.py BASE_EXE PC_EXE OUTDIR

Re-runs this seat's find 07-F1 on the PC r15 build under PC20, and on the base build for comparison.

07-F1: `position ... ` + `go depth N searchmoves <names with no legal root move>` on a board that
HAS legal moves emits a fabricated `info depth N ... score cp 0 nodes 0` line before `bestmove 0000`.

A finding that is gone on the PC build is "repaired on the PC"; one that survives is worth more.

Settings PC20 = the 14 S14 settings, then CuckooRep true, HistRework 2, TtPruneV2 true,
CorrHistV2 true, MateAlphaGuard true, OwnBook false, with Threads 1 and Hash 16.

Every case is one fresh process, driven by never sending a command while a `go` is running: the
driver reads stdout until `bestmove`.
"""
import os
import queue
import re
import subprocess
import sys
import threading

S14 = [
    "LmrQuietBase value 93", "LmrQuietDivisor value 205", "LmrNoisyBase value 13",
    "LmrNoisyDivisor value 333", "LmrHistoryDivisor value 5643", "NullMoveBase value 5",
    "LmpBase value 8", "HistoryPruneMultiplier value 2220",
    "HistoryBonusQuadratic value 24", "HistoryBonusLinear value 54",
    "HistoryBonusMax value 2212", "SingularDepth value 6", "IirDepth value 2",
    "NonPawnCorrection value true",
]
PC20 = S14 + ["CuckooRep value true", "HistRework value 2", "TtPruneV2 value true",
              "CorrHistV2 value true", "MateAlphaGuard value true", "OwnBook value false"]

# (name, position command, go command, expectation) -- the same cases as job2 plus the controls.
CASES = [
    ("no_legal_name_has_moves", "position startpos", "go depth 4 searchmoves e2e5"),
    ("empty_list", "position startpos", "go depth 4 searchmoves"),
    ("black_to_move_wrong_colour", "position startpos moves e2e4", "go depth 4 searchmoves e2e5"),
    ("one_legal_name_control", "position startpos", "go depth 6 searchmoves e2e4"),
    ("two_names_one_legal", "position startpos", "go depth 6 searchmoves e2e4 e2e5"),
    ("stalemate_root_control", "position fen 7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", "go depth 3 searchmoves a1a2"),
    ("plain_search_control", "position startpos", "go depth 4"),
]


class Reader:
    def __init__(s, st):
        s.q = queue.Queue()
        threading.Thread(target=s._pump, args=(st,), daemon=True).start()

    def _pump(s, st):
        for l in st:
            s.q.put(l)
        s.q.put(None)

    def get(s, t=180):
        try:
            return s.q.get(timeout=t)
        except queue.Empty:
            return None


def run(exe, options, position, go):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(p.stdout)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def drain():
        while True:
            l = r.get()
            if l is None:
                raise RuntimeError("no readyok")
            if l.strip() == "readyok":
                return

    send("uci")
    while True:
        l = r.get(60)
        if l is None or l.strip() == "uciok":
            break
    for opt in ["Hash value 16", "Threads value 1"] + options:
        send("setoption name " + opt)
        send("isready")
        drain()
    send("ucinewgame")
    send("isready")
    drain()
    send(position)
    send("isready")
    drain()
    send(go)
    depth_lines, best, bad = [], None, []
    while True:
        l = r.get(300)
        if l is None:
            raise RuntimeError("no bestmove")
        if l.startswith("info depth"):
            depth_lines.append(l.strip())
        if "unknown option" in l.lower() or "invalid value" in l.lower() or "error" in l.lower():
            bad.append(l.strip())
        if l.startswith("bestmove"):
            best = l.split()[1]
            break
    send("quit")
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    if bad:
        raise SystemExit(f"FAIL bad option/error line: {bad[:3]}")
    return depth_lines, best


def summarise(depth_lines, best):
    """The observable 07-F1 signature: a depth line whose nodes is 0, plus bestmove 0000."""
    zero_nodes = []
    last_nodes = None
    for l in depth_lines:
        m = re.search(r" nodes (\d+) ", l + " ")
        if m:
            last_nodes = int(m.group(1))
            if last_nodes == 0:
                zero_nodes.append(l)
    return {"depth_lines": len(depth_lines), "zero_node_lines": len(zero_nodes),
            "last_nodes": last_nodes, "bestmove": best,
            "fabricated": bool(zero_nodes) and best == "0000"}


def main():
    base_exe, pc_exe, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    print(f"{'case':30s} {'BASE(default)':>26s}   {'PC r15 (PC20)':>26s}")
    rows = []
    for name, pos, go in CASES:
        bd, bb = run(base_exe, [], pos, go)
        pd, pb = run(pc_exe, PC20, pos, go)
        bs, ps = summarise(bd, bb), summarise(pd, pb)
        rows.append({"case": name, "position": pos, "go": go, "base": bs, "pc20": ps})
        print(f"{name:30s} {bs['bestmove']:>12s} zero={bs['zero_node_lines']} "
              f"last={bs['last_nodes']}   {ps['bestmove']:>12s} zero={ps['zero_node_lines']} "
              f"last={ps['last_nodes']}", flush=True)
    import json
    json.dump(rows, open(os.path.join(outdir, "rerun_f1.json"), "w"), indent=1)
    print()
    f1_base = [r for r in rows if r["case"] in ("no_legal_name_has_moves", "empty_list",
                                                "black_to_move_wrong_colour") and r["base"]["fabricated"]]
    f1_pc = [r for r in rows if r["case"] in ("no_legal_name_has_moves", "empty_list",
                                              "black_to_move_wrong_colour") and r["pc20"]["fabricated"]]
    print(f"07-F1 reproduced on BASE: {len(f1_base)}/3 cases")
    print(f"07-F1 reproduced on PC r15 under PC20: {len(f1_pc)}/3 cases")
    # controls must search
    for r in rows:
        if r["case"].endswith("control") or r["case"] == "plain_search_control":
            if r["pc20"]["bestmove"] == "0000":
                print(f"  WARNING control {r['case']} answered 0000 on the PC build")
    if f1_pc:
        print("RESULT: 07-F1 SURVIVES on the PC build -> worth more now")
    else:
        print("RESULT: 07-F1 is REPAIRED on the PC build (not present under PC20)")


if __name__ == "__main__":
    main()
