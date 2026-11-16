#!/usr/bin/env python3
"""S02 — complete the 2x2 that S-C16 left incomplete, on ONE instrument, over seat 23's own 60 positions.

The gap in S-C16: seat 23 measured changed positions with the top-two gap at a fixed depth, but their UNCHANGED
half used a different instrument (best move versus a RANDOM alternative). So no clean 2x2 could be built. This
does it properly:

  for every one of seat 23's 60 positions (their job10/out_60.json):
    1. classify CHANGED vs UNCHANGED from THEIR OWN recorded bestmoves at N = 20000 / 50000 / 250000 — so the
       classification is theirs, not mine;
    2. measure the TOP-TWO GAP on the SAME instrument for both halves: at the depth the 20000 budget actually
       reached (their `depths` list gives that depth), score each of the top two moves ALONE with
       `go depth D searchmoves <move>`.

Every board is measured the same way whether it changed or not, which is exactly what was missing.

The move list per position comes from a MultiPV-2 search at that same depth D, so "top two" means the engine's own
two preferred moves at the depth the budget reached — the same definition seat 23 used for the changed half.

PC r15 + PC20, Threads 1, Hash 16, OwnBook false, fresh process per search, interactive driver, COLD.

usage: gap_2x2.py <pc_exe> <seat23_out_60.json> <outdir>
"""
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/agent/repos/pc/forge-combo29/build-pc/forge"
SRC = sys.argv[2] if len(sys.argv) > 2 else "/tmp/o60.json"
OUT = sys.argv[3] if len(sys.argv) > 3 else "out_2x2"

PC20 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
    "setoption name CuckooRep value true", "setoption name HistRework value 2",
    "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
    "setoption name MateAlphaGuard value true", "setoption name OwnBook value false",
]
CLASSIFY_BUDGET = 20000


def run(fen, go, multipv=None):
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
    L = []
    threading.Thread(target=lambda: [L.append(l.rstrip("\n")) for l in p.stdout], daemon=True).start()

    def send(t):
        if p.poll() is None:
            try:
                p.stdin.write(t + "\n")
                p.stdin.flush()
            except Exception:
                pass

    def wait(pref, n0=0, to=180.0):
        dl = time.monotonic() + to
        while time.monotonic() < dl:
            if any(l.startswith(pref) for l in L[n0:]):
                return True
            if p.poll() is not None:
                return any(l.startswith(pref) for l in L[n0:])
            time.sleep(0.001)
        return False

    send("uci")
    if not wait("uciok"):
        raise SystemExit("FAIL: no uciok")
    for s in PC20:
        send(s)
    if multipv:
        send("setoption name MultiPV value %d" % multipv)
    send("isready")
    if not wait("readyok"):
        raise SystemExit("FAIL: no readyok")
    for line in L:
        if "unknown option" in line or "invalid value" in line:
            raise SystemExit("FAIL: option refused: %r" % line)
    send("position fen " + fen)
    send("isready")
    n0 = len(L)
    wait("readyok", n0)
    n0 = len(L)
    send(go)
    if not wait("bestmove", n0, 240):
        return {"bestmove": None, "scores": {}}
    seg = list(L[n0:])
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    bm = [l for l in seg if l.startswith("bestmove")]
    scores = {}
    for line in seg:
        m = re.match(r"info depth (\d+) multipv (\d+) score (\S+) (-?\d+).*? pv (\S+)", line)
        if m:
            scores[(int(m.group(1)), int(m.group(2)))] = (m.group(3), int(m.group(4)), m.group(5))
            continue
        # a `searchmoves` search emits NO `multipv` field; record it as multipv 1
        m2 = re.match(r"info depth (\d+) .*?score (\S+) (-?\d+).*? pv (\S+)", line)
        if m2:
            scores[(int(m2.group(1)), 1)] = (m2.group(2), int(m2.group(3)), m2.group(4))
    return {"bestmove": bm[-1].split()[1] if bm else None, "scores": scores}


def main():
    os.makedirs(OUT, exist_ok=True)
    src = json.load(open(SRC))
    recs = src["records"]

    # ---- 1. classify CHANGED vs UNCHANGED from seat 23's OWN bestmoves
    per_fen = {}
    for r in recs:
        per_fen.setdefault(r["fen"], {})[r["go"]] = r
    classified = []
    for fen, by_go in per_fen.items():
        moves = {g: r.get("bestmove") for g, r in by_go.items()}
        base = moves.get("go nodes %d" % CLASSIFY_BUDGET)
        if base is None:
            continue
        changed = any(m and m != base for g, m in moves.items() if g != "go nodes %d" % CLASSIFY_BUDGET)
        # the depth the 20000 budget actually reached, from THEIR recorded depth list
        r20 = by_go["go nodes %d" % CLASSIFY_BUDGET]
        depths = r20.get("depths") or []
        reached = depths[-1][0] if depths else None
        classified.append({"fen": fen, "changed": changed, "reached_depth": reached,
                           "moves": moves})
    n_ch = sum(1 for c in classified if c["changed"])
    print("== classification from seat 23's own records: %d positions, %d changed, %d unchanged"
          % (len(classified), n_ch, len(classified) - n_ch))
    print()

    # ---- 2. measure the top-two gap on the SAME instrument for both halves
    print("== measuring the top-two gap at each position's reached depth, same instrument for both halves")
    rows = []
    for i, c in enumerate(classified):
        D = c["reached_depth"]
        if not D:
            continue
        m2 = run(c["fen"], "go depth %d" % D, multipv=2)
        d_lines = {k[1]: v for k, v in m2["scores"].items() if k[0] == D}
        if 1 not in d_lines or 2 not in d_lines:
            continue
        mv1, mv2 = d_lines[1][2], d_lines[2][2]
        s1 = run(c["fen"], "go depth %d searchmoves %s" % (D, mv1))
        s2 = run(c["fen"], "go depth %d searchmoves %s" % (D, mv2))
        # score each move alone at D
        def alone(res):
            cand = {k: v for k, v in res["scores"].items() if k[0] == D}
            if not cand:
                return None
            return cand[max(cand)][1]
        a1, a2 = alone(s1), alone(s2)
        if a1 is None or a2 is None:
            continue
        rows.append({"fen": c["fen"], "changed": c["changed"], "depth": D,
                     "mv1": mv1, "mv2": mv2, "s1": a1, "s2": a2, "gap": abs(a1 - a2),
                     "kind": d_lines[1][0]})
        if (i + 1) % 10 == 0:
            print("   ... %d/%d measured" % (i + 1, len(classified)), flush=True)
    json.dump(rows, open(os.path.join(OUT, "rows.json"), "w"), indent=1)

    ch = [r["gap"] for r in rows if r["changed"]]
    un = [r["gap"] for r in rows if not r["changed"]]
    print()
    print("### THE COMPLETED 2x2 — same instrument (top-two gap at the reached depth), both halves")
    print()
    print("| class | n | min gap | median gap | max gap | within 30 cp |")
    print("|---|---|---|---|---|---|")
    for name, xs in (("CHANGED", ch), ("UNCHANGED", un)):
        if not xs:
            print("| %s | 0 | - | - | - | - |" % name)
            continue
        print("| %s | %d | %d | %.0f | %d | %d of %d (%.0f %%) |"
              % (name, len(xs), min(xs), statistics.median(xs), max(xs),
                 sum(1 for g in xs if g <= 30), len(xs),
                 100.0 * sum(1 for g in xs if g <= 30) / len(xs)))
    print()
    if ch and un:
        print("### the predictor, computed rather than asserted")
        print()
        for thr in (10, 20, 30, 50):
            tp = sum(1 for g in ch if g <= thr)
            fp = sum(1 for g in un if g <= thr)
            fn = len(ch) - tp
            tn = len(un) - fp
            prec = tp / (tp + fp) if (tp + fp) else 0
            rec = tp / len(ch) if ch else 0
            print("  threshold %2d cp -> precision %.0f %% (%d/%d), recall %.0f %% (%d/%d), "
                  "| TN %d/%d"
                  % (thr, 100 * prec, tp, tp + fp, 100 * rec, tp, len(ch), tn, len(un)))
        json.dump({"changed": ch, "unchanged": un, "rows": len(rows)},
                  open(os.path.join(OUT, "summary.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
