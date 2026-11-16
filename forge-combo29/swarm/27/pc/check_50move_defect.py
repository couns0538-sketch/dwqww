#!/usr/bin/env python3
"""check_50move_defect.py <exe> <outdir> [--settings PC20] [--label NAME]

FABLE_TO_swarm_6's rule: "A cp 0 at a high counter is a defect ONLY when a forced mate exists that ends no
later than the 100th half-move. Test: the same board with counter 0 at `go depth 20` or more, read `mate N`;
it is a defect only if 2N-1 <= 100 - counter AND the board with the real counter still scores cp 0 at that
depth."

So this script reports, per board and counter:
  - the score at the REAL counter at depth 20 (the thing under suspicion)
  - the score at counter 0 at depth 20 (the reference, where the horizon cannot interfere)
  - the mate distance N from the counter-0 search
  - the inequality 2N-1 <= 100-counter, written out with both numbers
  - a verdict that follows ONLY from those numbers

Boards: seat 08's won K+R vs K at counter 91 (the case File 6 explicitly asks to check), the same at 99 and
100, and my own quiet middlegame from S-C8.
Threads 1 everywhere. Fresh process per search.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook false"]

# (label, FEN template with %d for the half-move counter, counters to test)
BOARDS = [
    ("K+R vs K (seat 08's board)", "1K6/8/8/3R4/8/8/8/k7 w - - %d 1", [0, 90, 91, 95, 99, 100]),
    ("my quiet middlegame", "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - %d 8", [0, 90, 91, 92, 99]),
]
DEPTH = 20


class Missing(Exception):
    pass


def search(exe, settings, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=900):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        for item in settings:
            name, _, val = item.rpartition(" ")
            s("setoption name %s value %s" % (name, val))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        t0 = time.monotonic()
        s("go depth %d" % depth)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=3600)
        wall = time.monotonic() - t0
        if not ok:
            raise Missing("no bestmove (fen %s depth %d)" % (fen, depth))
        infos = [l for l in lines if l.startswith("info depth %d " % depth)]
        if not infos:
            raise Missing("no 'info depth %d' line for %r (19-F12 signature)" % (depth, fen))
        last = infos[-1]
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        n = re.search(r"nodes (\d+)", last)
        if not sc or not n:
            raise Missing("info line lacks score/nodes: %r" % last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"fen": fen, "depth": depth, "kind": sc.group(1), "value": int(sc.group(2)),
                "nodes": int(n.group(1)), "bestmove": bm, "wall_s": round(wall, 2),
                "last": last}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--label", default="run")
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "threads": 1, "depth": DEPTH, "label": a.label,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "boards": []}

    for label, tpl, counters in BOARDS:
        # reference: counter 0, depth 20 -> the mate distance if any
        ref = search(exe, settings, tpl % 0, DEPTH)
        n_mate = ref["value"] if ref["kind"] == "mate" and ref["value"] > 0 else None
        row = {"board": label, "template": tpl, "reference_counter0": ref,
               "mate_in_n": n_mate, "rows": [],
               "defect_test": ""}
        if n_mate is None:
            row["defect_test"] = ("counter-0 score is %s %d at depth %d, not a positive mate, so the "
                                  "File-6 inequality cannot be met: a cp 0 here is NOT a defect"
                                  % (ref["kind"], ref["value"], DEPTH))
        for c in counters:
            if c == 0:
                continue
            r = search(exe, settings, tpl % c, DEPTH)
            entry = {"counter": c, "result": r,
                     "2N_minus_1": (2 * n_mate - 1) if n_mate else None,
                     "100_minus_counter": 100 - c,
                     "inequality_holds": ((2 * n_mate - 1) <= (100 - c)) if n_mate else None,
                     "scores_cp0": (r["kind"] == "cp" and r["value"] == 0)}
            row["rows"].append(entry)
        if n_mate is not None:
            hits = [e["counter"] for e in row["rows"]
                    if e["inequality_holds"] and e["scores_cp0"]]
            row["defect_test"] = (
                "mate in %d at counter 0 (2N-1 = %d). Counters where 2N-1 <= 100-counter AND the "
                "counter-c search still scores cp 0: %s. %s"
                % (n_mate, 2 * n_mate - 1, hits if hits else "none",
                   "THOSE ARE DEFECTS -- a forced mate was reachable before the match program ends the game"
                   if hits else "NO DEFECT: where the counter is high the mate is no longer reachable "
                                "before 100, and where it is reachable the engine does not score cp 0"))
        out["boards"].append(row)
        print("\n== %s" % label)
        print("   reference counter 0: %s %d (nodes %d, %s) in %.1fs"
              % (ref["kind"], ref["value"], ref["nodes"], ref["bestmove"], ref["wall_s"]))
        for e in row["rows"]:
            r = e["result"]
            print("   counter %-4d: %-6s %-6d nodes %-10d bm %-6s | 2N-1=%s  100-c=%s  holds=%-5s cp0=%-5s"
                  % (e["counter"], r["kind"], r["value"], r["nodes"], r["bestmove"],
                     e["2N_minus_1"], e["100_minus_counter"], e["inequality_holds"], e["scores_cp0"]))
        print("   VERDICT: %s" % row["defect_test"])

    with open(os.path.join(a.outdir, "check_50move_%s_%s.json" % (a.label, a.settings)), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote", os.path.join(a.outdir, "check_50move_%s_%s.json" % (a.label, a.settings)))


if __name__ == "__main__":
    main()
