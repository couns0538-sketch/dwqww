#!/usr/bin/env python3
"""seat 17 NEW AREA (file 6): `go softnodes N` on the PC build under PC20, Threads 1.

The owner's PC uses `go softnodes 2000` for its self-play: the search stops at the end of the first
depth after N nodes. Three questions:
  Q1 is it deterministic run to run (it must be)?
  Q2 does it stop at a FINISHED depth (i.e. the reported depth was completed, not abandoned mid-iteration)?
  Q3 how far past N do the node counts go?

Also answers: is the emitted `info depth` set complete 1..D (a finished climb) or truncated?

Threads 1, Hash 16, PC20, PC r15 build. Fresh process per run.

usage: softnodes.py <exe> <outdir> <runs>
"""
import json
import os
import re
import subprocess
import sys

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

POSITIONS = [
    ("G1", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G2", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("G3", "6k1/p4r1p/1p2Q3/2p5/2P1N3/1P3P2/PK6/6q1 b - - 0 1"),
]


def run(exe, fen, softnodes, timeout=180):
    """Drive the search to `bestmove` before sending quit (19-F12: a pipelined quit fabricates an
    answer with 0 nodes, which would make every softnodes measurement meaningless)."""
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(predicate):
        while True:
            reply = proc.stdout.readline()
            if reply == "":
                return None
            out.append(reply.rstrip("\n"))
            if predicate(reply):
                return reply

    try:
        send("uci")
        read_until(lambda l: l.strip() == "uciok")
        for name, value in PC20:
            send("setoption name %s value %s" % (name, value))
            send("isready")
            read_until(lambda l: l.strip() == "readyok")
        send("position fen " + fen)
        send("isready")
        read_until(lambda l: l.strip() == "readyok")
        send("go softnodes %d" % softnodes)
        read_until(lambda l: l.startswith("bestmove"))
    finally:
        try:
            send("quit")
            proc.wait(timeout=20)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
    return "\n".join(out) + "\n"


def parse(text):
    depth_lines = []
    for line in text.splitlines():
        if not line.startswith("info depth"):
            continue
        rec = {}
        m = re.search(r"depth (\d+)", line)
        rec["depth"] = int(m.group(1)) if m else None
        m = re.search(r"nodes (\d+)", line)
        rec["nodes"] = int(m.group(1)) if m else None
        m = re.search(r"score (cp|mate) (-?\d+)", line)
        rec["score"] = "%s %s" % (m.group(1), m.group(2)) if m else None
        m = re.search(r"seldepth (\d+)", line)
        rec["seldepth"] = int(m.group(1)) if m else None
        m = re.search(r" time (\d+)", line)
        rec["time_ms"] = int(m.group(1)) if m else None
        m = re.search(r" pv (.*)$", line)
        rec["pv"] = m.group(1) if m else ""
        depth_lines.append(rec)
    best = [l for l in text.splitlines() if l.startswith("bestmove")]
    soft = [l for l in text.splitlines() if "info string softnodes" in l]
    return depth_lines, (best[-1] if best else None), (soft[-1] if soft else None)


def main():
    exe, outdir, runs = sys.argv[1], sys.argv[2], int(sys.argv[3])
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for soft in (2000, 20000, 50000, 250000):
        for name, fen in POSITIONS:
            per_run = []
            for r in range(runs):
                text = run(exe, fen, soft)
                log = os.path.join(outdir, "%s_soft%d_run%d.log" % (name, soft, r))
                open(log, "w").write(text)
                depths, best, softline = parse(text)
                per_run.append({
                    "depth_lines": len(depths),
                    "last_depth": depths[-1]["depth"] if depths else None,
                    "last_nodes": depths[-1]["nodes"] if depths else None,
                    "last_score": depths[-1]["score"] if depths else None,
                    "last_seldepth": depths[-1]["seldepth"] if depths else None,
                    "pv": depths[-1]["pv"] if depths else None,
                    "bestmove": best,
                    "softnodes_line": softline,
                    "depth_sequence_complete": ([d["depth"] for d in depths] == list(range(1, len(depths) + 1))),
                })
            # determinism = every run identical on the fields that matter
            same = all(json.dumps(x, sort_keys=True) == json.dumps(per_run[0], sort_keys=True) for x in per_run)
            row = {
                "position": name, "softnodes": soft, "runs": runs,
                "deterministic": same,
                "last_depth": per_run[0]["last_depth"],
                "last_nodes": per_run[0]["last_nodes"],
                "overshoot_nodes": (per_run[0]["last_nodes"] - soft) if per_run[0]["last_nodes"] else None,
                "overshoot_ratio": round(per_run[0]["last_nodes"] / soft, 3) if per_run[0]["last_nodes"] else None,
                "depth_sequence_complete": per_run[0]["depth_sequence_complete"],
                "bestmove": per_run[0]["bestmove"],
                "softnodes_line": per_run[0]["softnodes_line"],
                "distinct_runs": len({json.dumps(x, sort_keys=True) for x in per_run}),
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
    json.dump(rows, open(os.path.join(outdir, "softnodes.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
