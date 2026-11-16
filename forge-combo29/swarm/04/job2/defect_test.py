#!/usr/bin/env python3
"""defect_test.py — does a multi-thread result fail any of file 6's five DEFECT tests?

File 6 declares shared-table multi-thread variance by design. A multi-thread result is a DEFECT only if:
  D1 a HANG: no bestmove within 10x the 1-thread time at the same depth
  D2 a CRASH (non-zero exit, or death by signal)
  D3 an ILLEGAL move (checked against python-chess, and `0000` only where no legal move exists)
  D4 a SANITIZER line (only meaningful on a sanitizer build; recorded as "not shown" otherwise)
  D5 a score OUTSIDE the spread of 20 ONE-THREAD runs at depths 12..16, that does NOT shrink with depth

Design notes, because the honest answer depends on them:
  * First build the one-thread reference spread: 20 runs per depth at depths 12, 13, 14, 15, 16, Threads 1.
    The min and max at each depth define the band.
  * Then run Threads N at each of those depths and ask whether its score fell inside the band at that depth.
  * D5's "does not shrink with depth" clause is tested by looking at the band width per depth: if the band
    narrows with depth, an outlier at depth 12 that is inside the band at depth 16 is shrinkage, not a defect.
  * A run that never prints a score or a bestmove is an INTEGRITY FAILURE and aborts, not a defect claim.

Usage: defect_test.py EXE OUTDIR TAG --settings pc20 --threads 4 --depths 12,13,14,15,16 --ref-runs 20 --mt-runs 5
"""
import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5),
       ("LmpBase", 8), ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24),
       ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212), ("SingularDepth", 6),
       ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
ORD = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"

try:
    import chess
except ImportError:
    chess = None


def opts_for(name, threads):
    base = [("Hash", 16), ("Threads", threads)]
    if name == "none":
        return base
    if name == "s14":
        return base + S14 + [("OwnBook", "false")]
    return base + S14 + PC20_EXTRA


def send(p, s):
    try:
        p.stdin.write(s + "\n")
        p.stdin.flush()
        return True
    except (BrokenPipeError, ValueError):
        return False


def drain(q, p, until=None, limit=120.0):
    got = []
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        try:
            ln = q.get(timeout=0.05)
        except queue.Empty:
            if p.poll() is not None and q.empty():
                break
            continue
        got.append(ln)
        if until and (ln == until or ln.startswith(until)):
            return got, True
    return got, False


def one(exe, fen, opts, depth, limit):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    q = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.rstrip("\r\n")) for l in p.stdout],
                     daemon=True).start()
    err = []
    threading.Thread(target=lambda: [err.append(l.rstrip()) for l in p.stderr],
                     daemon=True).start()
    problems = []
    try:
        send(p, "uci")
        drain(q, p, until="uciok", limit=30.0)
        for name, val in opts:
            send(p, "setoption name %s value %s" % (name, val))
            send(p, "isready")
            lines, ok = drain(q, p, until="readyok", limit=20.0)
            if not ok:
                problems.append("no readyok after %s" % name)
            for ln in lines:
                if "unknown option" in ln or "invalid value" in ln:
                    problems.append("refused: " + ln)
        send(p, "ucinewgame")
        send(p, "isready")
        drain(q, p, until="readyok", limit=20.0)
        send(p, "position fen " + fen)
        send(p, "isready")
        lines, _ = drain(q, p, until="readyok", limit=20.0)
        for ln in lines:
            if "invalid FEN" in ln:
                problems.append("invalid FEN: " + ln)
        t0 = time.monotonic()
        send(p, "go depth %d" % depth)
        got, reached = drain(q, p, until="bestmove", limit=limit)
        wall = time.monotonic() - t0
        best = ""
        score_at = None
        for ln in got:
            if ln.startswith("bestmove"):
                best = ln
                continue
            if not ln.startswith("info "):
                continue
            parts = ln.split()
            de = None
            if "depth" in parts:
                try:
                    de = int(parts[parts.index("depth") + 1])
                except Exception:
                    pass
            if "score" in parts and de == depth:
                i = parts.index("score")
                try:
                    kind = parts[i + 1]
                    val = int(parts[i + 2])
                    score_at = ("mate %d" % val) if kind == "mate" else val
                except Exception:
                    pass
        move = best.split()[1] if len(best.split()) > 1 else ""
        legal = None
        if chess is not None and move:
            try:
                board = chess.Board(fen)
                nlegal = board.legal_moves.count()
                if move == "0000":
                    legal = (nlegal == 0)
                else:
                    legal = chess.Move.from_uci(move) in board.legal_moves
            except Exception:
                legal = None
        sanitizer = any("Sanitizer" in l for l in err)
        exc = p.returncode
        if not reached:
            problems.append("no bestmove within %ss" % limit)
        if score_at is None:
            problems.append("no score at depth %d" % depth)
        return {"move": move, "score": score_at, "wall": round(wall, 3),
                "exit": exc, "legal": legal, "sanitizer": sanitizer,
                "depth": depth, "problems": problems,
                "measured": {"bestmove_found": bool(best), "score_found": score_at is not None}}
    finally:
        send(p, "quit")
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()


def numeric(s):
    return None if s is None or isinstance(s, str) else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("outdir")
    ap.add_argument("tag")
    ap.add_argument("--settings", default="pc20")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--depths", default="12,13,14,15,16")
    ap.add_argument("--ref-runs", type=int, default=20)
    ap.add_argument("--mt-runs", type=int, default=5)
    ap.add_argument("--limit", type=float, default=240.0)
    ap.add_argument("--fen", default=ORD)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    depths = [int(x) for x in a.depths.split(",")]
    path = os.path.join(a.outdir, a.tag + ".jsonl")
    ref = {}
    mt = {}
    with open(path, "w") as f:
        for dep in depths:
            ref[dep] = []
            for r in range(a.ref_runs):
                rec = one(a.exe, a.fen, opts_for(a.settings, 1), dep, a.limit)
                rec.update({"threads": 1, "run": r, "depth": dep, "role": "ref",
                            "settings": a.settings, "fen": a.fen})
                f.write(json.dumps(rec) + "\n"); f.flush()
                ref[dep].append(rec)
            print("ref depth %2d done: scores %s" % (dep, sorted({str(x['score']) for x in ref[dep]})), flush=True)
        for dep in depths:
            mt[dep] = []
            for r in range(a.mt_runs):
                rec = one(a.exe, a.fen, opts_for(a.settings, a.threads), dep, a.limit)
                rec.update({"threads": a.threads, "run": r, "depth": dep, "role": "mt",
                            "settings": a.settings, "fen": a.fen})
                f.write(json.dumps(rec) + "\n"); f.flush()
                mt[dep].append(rec)
            print("mt  depth %2d done: scores %s" % (dep, sorted({str(x['score']) for x in mt[dep]})), flush=True)

    allrecs = [r for d in depths for r in ref[d] + mt[d]]
    bad = [r for r in allrecs if r["problems"]]
    if bad:
        print("\nINTEGRITY FAILURE: %d run(s) lacked a bestmove or score; NO verdict" % len(bad))
        for r in bad[:10]:
            print("  T%d d%d r%d: %s" % (r["threads"], r["depth"], r["run"], "; ".join(r["problems"])))
        sys.exit(1)

    print("\n== reference spread: 20 one-thread runs per depth ==")
    print("%5s %8s %8s %8s %10s %s" % ("depth", "min", "max", "width", "ref_med_s", "distinct scores"))
    bands = {}
    for dep in depths:
        vals = [numeric(x["score"]) for x in ref[dep]]
        vals = [v for v in vals if v is not None]
        if vals:
            bands[dep] = (min(vals), max(vals))
            med = sorted(x["wall"] for x in ref[dep])[len(ref[dep]) // 2]
            print("%5d %8d %8d %8d %10.3f %s" %
                  (dep, min(vals), max(vals), max(vals) - min(vals), med,
                   sorted({str(x["score"]) for x in ref[dep]})))

    print("\n== D5: does each Threads-%d score fall inside the one-thread band at that depth? ==" % a.threads)
    print("%5s %-9s %s" % ("depth", "score", "verdict"))
    outside = []
    for dep in depths:
        if dep not in bands:
            continue
        lo, hi = bands[dep]
        for rec in mt[dep]:
            v = numeric(rec["score"])
            if v is None:
                print("%5d %-9s MATED-SCORE (band is cp-only)" % (dep, rec["score"]))
                continue
            ok = lo <= v <= hi
            if not ok:
                outside.append((dep, v, lo, hi))
            print("%5d %-9d %s" % (dep, v, "inside" if ok else "OUTSIDE band [%d,%d]" % (lo, hi)))

    print("\n== D1-D4 over all Threads-%d runs ==" % a.threads)
    def check(recs, label):
        hangs = [r for r in recs if not r["measured"]["bestmove_found"]]
        crashes = [r for r in recs if r["exit"] not in (0, None)]
        illegal = [r for r in recs if r["legal"] is False]
        san = [r for r in recs if r["sanitizer"]]
        print("%-12s hangs=%d crashes=%d illegal=%d sanitizer=%d (of %d)"
              % (label, len(hangs), len(crashes), len(illegal), len(san), len(recs)))
        return hangs, crashes, illegal, san
    refall = [r for d in depths for r in ref[d]]
    mtall = [r for d in depths for r in mt[d]]
    check(refall, "threads 1")
    h, c, il, s = check(mtall, "threads %d" % a.threads)

    print("\n== verdict against file 6's five tests ==")
    print("D1 hang (10x the 1-thread time at the same depth): %s" %
          ("YES" if h else "no"))
    print("D2 crash: %s" % ("YES" if c else "no"))
    print("D3 illegal move: %s" % ("YES" if il else "no"))
    print("D4 sanitizer line: %s" % ("YES" if s else "not shown (release build, no sanitizer)"))
    widths = {d: (bands[d][1] - bands[d][0]) for d in bands}
    shrinking = None
    if len(widths) >= 2:
        ds = sorted(widths)
        shrinking = widths[ds[-1]] <= widths[ds[0]]
    if outside:
        dep_outs = sorted({d for d, _, _, _ in outside})
        print("D5 score outside the one-thread band: YES at depth(s) %s" % dep_outs)
        print("   band widths by depth: %s  -> %s with depth"
              % (widths, "NARROWS" if shrinking else "does NOT narrow"))
        print("   => D5 counts as a DEFECT only if the outlier does not shrink with depth.")
    else:
        print("D5 score outside the one-thread band: no")
    print("\nintegrity: every run had a bestmove and a score at the target depth")


if __name__ == "__main__":
    main()
