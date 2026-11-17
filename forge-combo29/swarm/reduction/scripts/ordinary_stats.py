#!/usr/bin/env python3
"""ordinary_stats.py EXE FENS [--depth N] [--limit N] [--json OUT]

Reduction statistics over ORDINARY positions (no lone king at the root): the
distribution of reduction magnitude, the mean reduction, the re-search rate, and
the LMR rejection profile. This is the number nobody has published.

Also reports, per position, the reductions per 1000 nodes, because a raw count is
just tree size: the informative quantity is how hard LMR works per node visited.

Usage: ordinary_stats.py EXE FENS --depth 12 --limit 50
"""
import argparse
import json
import re
import subprocess
import sys

RE_INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*? nodes (\d+) ")


def parse_total(lines):
    """The `lmrsum` block: the whole-search reduction totals."""
    best = None
    for line in lines:
        if not line.startswith("info string lmrsum depth 0 root all "):
            continue
        body = line
        kv = {}
        for key in ("applied", "research", "rej", "cap_gate", "cap_clamp"):
            m = re.search(rf"\b{key} (\d+)", body)
            if m:
                kv[key] = int(m.group(1))
        m = re.search(r"\brmean ([-\d.]+)", body)
        if m:
            kv["rmean"] = float(m.group(1))
        m = re.search(r"\bcap_rmean ([-\d.]+)", body)
        if m:
            kv["cap_rmean"] = float(m.group(1))
        m = re.search(r"\[([^\]]*)\]", body)
        if m:
            toks = m.group(1).split()
            for j in range(0, len(toks) - 1, 2):
                kv[f"guard_{toks[j]}"] = int(toks[j + 1])
        m = re.search(r"\bmag((?: r-?\d+=\d+)+)", body)
        if m:
            kv["mag"] = {int(t.split("=")[0][1:]): int(t.split("=")[1]) for t in m.group(1).split()}
        best = kv
    return best


def search(exe, fen, depth):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    lines = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(pred):
        while True:
            line = p.stdout.readline()
            if not line:
                return None
            line = line.rstrip("\n")
            lines.append(line)
            low = line.lower()
            if low.startswith(("unknown option", "invalid value", "invalid fen", "illegal move")):
                raise SystemExit(f"PROTOCOL ERROR {fen}: {line}")
            if pred(line):
                return line

    send("uci")
    until(lambda l: l.startswith("uciok"))
    for k, v in (("Threads", "1"), ("Hash", "16"), ("OwnBook", "false")):
        send(f"setoption name {k} value {v}")
        send("isready")
        until(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"position fen {fen}")
    send("isready")
    until(lambda l: l.startswith("readyok"))
    send(f"go depth {depth}")
    best = until(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.stdin.close()
    except Exception:
        pass
    p.wait(timeout=60)
    nodes = None
    score = None
    for line in lines:
        m = RE_INFO.match(line)
        if m:
            score = f"{m.group(2)}{m.group(3)}"
            nodes = int(m.group(4))
    mv = best.split()[1] if best and len(best.split()) > 1 else None
    return {"bestmove": mv, "score": score, "nodes": nodes, "total": parse_total(lines)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe")
    ap.add_argument("fens")
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    fens = [l.strip() for l in open(a.fens) if l.strip() and not l.strip().startswith("#")][: a.limit]
    rows = []
    print(f"exe {a.exe}  {len(fens)} positions  go depth {a.depth}  Threads 1 Hash 16 OwnBook false")
    print(f"{'#':>3s} {'nodes':>8s} {'applied':>8s} {'rmean':>6s} {'appl/1k':>8s} "
          f"{'research':>8s} {'resch%':>7s} {'rej':>7s} {'rej/1k':>7s} {'mag (r:count)':>30s}")
    total_mag = {}
    for i, fen in enumerate(fens, 1):
        r = search(a.exe, fen, a.depth)
        t = r["total"] or {}
        if not t:
            print(f"{i:>3d} NO LMR BLOCK — is this an instrumented build?")
            continue
        nodes = r["nodes"] or 1
        applied = t.get("applied", 0)
        research = t.get("research", 0)
        rej = t.get("rej", 0)
        mag = t.get("mag", {})
        for k, v in mag.items():
            total_mag[k] = total_mag.get(k, 0) + v
        rows.append({"i": i, "fen": fen, "nodes": r["nodes"], "score": r["score"],
                     "bestmove": r["bestmove"], "applied": applied,
                     "rmean": t.get("rmean"), "research": research, "rej": rej,
                     "mag": mag, "guards": {k[6:]: v for k, v in t.items() if k.startswith("guard_")}})
        magtxt = " ".join(f"{k}:{v}" for k, v in sorted(mag.items()))
        print(f"{i:>3d} {nodes:>8d} {applied:>8d} {t.get('rmean',0):>6.2f} "
              f"{1000.0*applied/nodes:>8.2f} {research:>8d} "
              f"{100.0*research/applied if applied else 0:>6.2f}% {rej:>7d} "
              f"{1000.0*rej/nodes:>7.2f} {magtxt:>30s}")

    if not rows:
        print("no rows")
        return 1

    n = len(rows)
    sum_nodes = sum(r["nodes"] or 0 for r in rows)
    sum_applied = sum(r["applied"] for r in rows)
    sum_research = sum(r["research"] for r in rows)
    sum_rej = sum(r["rej"] for r in rows)
    rmeans = sorted(r["rmean"] for r in rows if r["rmean"] is not None)
    permille = sorted(1000.0 * r["applied"] / (r["nodes"] or 1) for r in rows)

    print()
    print("=== pooled over the set")
    print(f"positions            {n}")
    print(f"nodes                {sum_nodes}")
    print(f"reductions applied   {sum_applied}")
    print(f"reductions / 1000 nodes (pooled)  {1000.0*sum_applied/sum_nodes:.2f}")
    print(f"per-position reductions/1k median {permille[n//2]:.2f}  min {permille[0]:.2f}  max {permille[-1]:.2f}")
    print(f"mean reduction r     median of per-position means {rmeans[n//2]:.3f}  "
          f"min {rmeans[0]:.3f}  max {rmeans[-1]:.3f}")
    print(f"pooled mean r        {sum(r['rmean']*r['applied'] for r in rows if r['rmean'] is not None)/max(1,sum_applied):.3f}")
    print(f"re-searches          {sum_research}  ({100.0*sum_research/max(1,sum_applied):.2f}% of applied reductions)")
    print(f"LMR rejections       {sum_rej}  ({1000.0*sum_rej/sum_nodes:.2f} per 1000 nodes)")
    print()
    print("=== reduction magnitude distribution, pooled")
    tot = sum(total_mag.values()) or 1
    for k in sorted(total_mag):
        print(f"  r={k:<2d} {total_mag[k]:>10d}  {100.0*total_mag[k]/tot:>6.2f}%")
    print()
    print("=== guard rejections, pooled (a node can fail several guards, so these overlap)")
    guards = {}
    for r in rows:
        for k, v in r["guards"].items():
            guards[k] = guards.get(k, 0) + v
    for k in sorted(guards, key=lambda x: -guards[x]):
        print(f"  {k:<12s} {guards[k]:>10d}  {100.0*guards[k]/max(1,sum_rej):>6.2f}% of rejected nodes")

    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"rows": rows, "sum_nodes": sum_nodes, "sum_applied": sum_applied,
                       "sum_research": sum_research, "sum_rej": sum_rej,
                       "mag": total_mag, "guards": guards, "depth": a.depth}, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
