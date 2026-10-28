#!/usr/bin/env python3
"""R3-4 evidence: how much each candidate search constant changes the searched tree.

For every candidate, one engine process runs `bench <depth>` (8 positions, fixed depth, Threads 1, Hash 16) with
the constant at default + step and at default - step (step = max(1, round(10% of the default))), then resets
it. Reported: total bench nodes and the relative change against the default run. A constant whose step does not
change the tree (0.00%) gives SPSA nothing to measure (e.g. the capture-futility multiplier while
CaptureFutilityBase is 0). Node counts are deterministic, so one run per setting suffices. Tree size is not
strength: this is a liveness / sensitivity check that supports, not replaces, the reasons in README.md.

usage: r3_4_sensitivity_scan.py <forge exe> [--depth 13] [--json out.json]
"""
import argparse
import json
import re
import subprocess
import sys

CANDIDATES = [
    # (group, name, default) - the 20 advertised ones first, then the other candidates of the same mechanisms,
    # then context constants outside the six requested groups.
    ("LMR", "LmrQuietBase", 85), ("LMR", "LmrQuietDivisor", 220), ("LMR", "LmrNoisyBase", 10),
    ("LMR", "LmrNoisyDivisor", 340), ("LMR", "LmrHistoryDivisor", 6000), ("LMR", "LmrCutoffThreshold", 3),
    ("null move", "NullMoveBase", 3), ("null move", "NullMoveDepthDivisor", 3), ("null move", "NullMoveEvalDivisor", 200),
    ("null move", "NullMoveMarginDepth", 24), ("null move", "NullMoveMarginBase", 180),
    ("RFP", "RfpMargin", 72), ("RFP", "RfpImproving", 40), ("RFP", "RfpDepth", 8),
    ("futility", "FutilityBase", 100), ("futility", "FutilityMultiplier", 110), ("futility", "QsFutilityMargin", 160),
    ("SEE", "SeeQuietMultiplier", 24), ("SEE", "SeeNoisyMultiplier", 150),
    ("aspiration", "AspirationDelta", 18),
    ("SEE (not chosen: 0-99 identical)", "QsSeeMargin", 40), ("null move (not chosen)", "NullMoveMinDepth", 3),
    ("futility (not chosen)", "FutilityDepth", 7),
    ("context", "LmpBase", 4), ("context", "HistoryPruneMultiplier", 2048), ("context", "RazorBase", 150),
    ("context", "RazorMultiplier", 350), ("context", "ProbcutMargin", 180), ("context", "SingularMargin", 2),
    ("context (dead: CaptureFutilityBase 0)", "CaptureFutilityMultiplier", 250),
]


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, bufsize=1)

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def wait(self, pattern):
        rx = re.compile(pattern)
        for line in self.p.stdout:
            m = rx.search(line)
            if m:
                return m
        raise SystemExit("engine exited before " + pattern)

    def bench(self, depth):
        self.send(f"bench {depth}")
        return int(self.wait(rf"bench depth {depth} nodes (\d+)").group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("--depth", type=int, default=13)
    ap.add_argument("--json")
    a = ap.parse_args()
    e = Engine(a.exe)
    e.send("uci")
    reply = []
    for line in e.p.stdout:
        reply.append(line.strip())
        if line.strip() == "uciok":
            break
    for o in ("Threads value 1", "Hash value 16", "OwnBook value false"):
        e.send("setoption name " + o)
    e.send("isready")
    e.wait("^readyok")
    base = e.bench(a.depth)
    print(f"default bench d{a.depth} nodes {base}", flush=True)
    rows = []
    print(f"{'group':<38}{'name':<26}{'default':>8}{'step':>6}{'nodes -':>11}{'nodes +':>11}{'-step %':>9}{'+step %':>9}"
          f"{'mean |%|':>9}  listed", flush=True)
    for group, name, default in CANDIDATES:
        step = max(1, round(0.1 * default))
        listed = any(line.startswith(f"option name {name} ") for line in reply)
        nodes = {}
        for sign in (-1, 1):
            e.send(f"setoption name {name} value {default + sign * step}")
            nodes[sign] = e.bench(a.depth)
        e.send(f"setoption name {name} value {default}")
        down, up = (nodes[-1] / base - 1) * 100, (nodes[1] / base - 1) * 100
        rows.append({"group": group, "name": name, "default": default, "step": step, "nodes_minus": nodes[-1],
                     "nodes_plus": nodes[1], "pct_minus": down, "pct_plus": up, "mean_abs_pct": (abs(down) + abs(up)) / 2,
                     "advertised": listed})
        print(f"{group:<38}{name:<26}{default:>8}{step:>6}{nodes[-1]:>11}{nodes[1]:>11}{down:>+9.2f}{up:>+9.2f}"
              f"{(abs(down) + abs(up)) / 2:>9.2f}  {'yes' if listed else 'no'}", flush=True)
    end = e.bench(a.depth)
    print(f"default bench d{a.depth} nodes at the end {end} ({'same' if end == base else 'DIFFERENT'})", flush=True)
    e.send("quit")
    e.p.wait(timeout=60)
    if a.json:
        with open(a.json, "w", newline="\n") as f:
            json.dump({"exe": a.exe, "depth": a.depth, "default_nodes": base, "end_nodes": end, "rows": rows}, f, indent=1)
    sys.exit(0 if end == base else 1)


if __name__ == "__main__":
    main()
