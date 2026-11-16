#!/usr/bin/env python3
"""perft 4 with a PER-DIVIDE comparison, on both builds and under PC20.

This closes the limit I stated in job2/DIVIDE_CONTROL.md: my perft 3/4/5 comparisons were totals
only, and seat 06's S-F22 (plus my own S-C4 control) showed a compensating error can keep the total
exact. This compares the engine's `go perft 4` DIVIDE against python-chess move by move, at every
root move, so an over-count on one root move cannot be hidden by an under-count on another.

For each position and each root move the engine prints `<uci>: <nodes>`; python-chess computes the
subtree count for the same move. A position DIFFERS if the root-move SET differs or any count
differs. The total is reported too, but only as a cross-check against the per-divide sum.

Fail-loud rules (integrity lesson): the block count must equal the position count, every block must
carry a `nodes` line, every root move must be parseable, and a run that compares zero positions is
reported as NOT SHOWN rather than as a pass.

Usage: divide_perft4.py EXE FENS OUT.json [SETTINGS_REGIME]
  SETTINGS_REGIME = "none" (Threads 1, Hash 16) or "PC20" (Threads 1, Hash 16, S14 + the six)
"""
import hashlib
import json
import os
import re
import subprocess
import sys

import chess

EXE = sys.argv[1]
FENS = sys.argv[2]
OUT = sys.argv[3]
REGIME = sys.argv[4] if len(sys.argv) > 4 else "none"
DEPTH = 4

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC6 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BASE = [("Threads", "1"), ("Hash", "16")]
OPTS = BASE + (S14 + PC6 if REGIME == "PC20" else [])

BAD = ("unknown option", "invalid value", "error")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def py_divide(fen, depth):
    """{uci: subtree_nodes} for every legal root move."""
    b = chess.Board(fen)

    def perft(bd, d):
        if d == 0:
            return 1
        n = 0
        for m in bd.legal_moves:
            bd.push(m)
            n += perft(bd, d - 1)
            bd.pop()
        return n

    div = {}
    for m in b.legal_moves:
        b.push(m)
        div[m.uci()] = perft(b, depth - 1)
        b.pop()
    return div


def ref_job(fen):
    return py_divide(fen, DEPTH)


def main():
    fens = [l.strip() for l in open(FENS) if l.strip()]
    if not fens:
        raise SystemExit("FAIL: %s holds no positions" % FENS)

    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    sent = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()
        sent.append(s)

    def read_until(pred, what):
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died waiting for %s" % what)
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad answer %r while waiting for %s" % (l, what))
            if pred(l):
                return l

    send("uci")
    idname = None
    opts_seen = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise SystemExit("FAIL: died in uci handshake")
        l = l.rstrip("\n")
        if l.startswith("id name"):
            idname = l
        if l.startswith("option name"):
            opts_seen.append(l)
        if l == "uciok":
            break

    for n, v in OPTS:
        if not any(o.startswith("option name %s " % n) for o in opts_seen):
            raise SystemExit("FAIL: option %r not advertised by this exe" % n)
        send("setoption name %s value %s" % (n, v))
        send("isready")
        read_until(lambda s: s == "readyok", "readyok after %s" % n)

    raw = []
    cache_path0 = OUT + ".engine_raw.json"
    reused = False
    if os.path.exists(cache_path0):
        try:
            cached = json.load(open(cache_path0))
            if ([c["fen"] for c in cached["raw"]] == fens
                    and cached.get("regime") == REGIME):
                raw = [(c["divide"], c["total"]) for c in cached["raw"]]
                idname = cached.get("id_name", idname)
                reused = True
                print("REUSED cached engine output for", len(raw), "positions", flush=True)
        except Exception as e:
            print("cache not reused:", e, flush=True)

    for i, fen in enumerate(fens):
        if reused:
            break
        send("position fen " + fen)
        send("isready")
        read_until(lambda s: s == "readyok", "readyok after position %d" % i)
        send("go perft %d" % DEPTH)
        block = {}
        total = None
        while True:
            l = p.stdout.readline()
            if not l:
                raise SystemExit("FAIL: engine died during perft on position %d" % i)
            l = l.rstrip("\n")
            if any(b in l.lower() for b in BAD):
                raise SystemExit("FAIL: bad answer %r on position %d" % (l, i))
            if l.startswith("nodes "):
                total = int(l.split()[1])
                break
            m = re.match(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$", l)
            if m:
                block[m.group(1)] = int(m.group(2))
            elif l.strip():
                raise SystemExit("FAIL: unparseable perft line %r on position %d" % (l, i))
        raw.append((block, total))
        if (i + 1) % 20 == 0:
            print("engine %d/%d" % (i + 1, len(fens)), flush=True)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()

    if len(raw) != len(fens):
        raise SystemExit("FAIL: %d divide blocks for %d positions" % (len(raw), len(fens)))

    cache_path = OUT + ".engine_raw.json"
    with open(cache_path, "w") as cf:
        json.dump({"id_name": idname, "options": OPTS, "regime": REGIME,
                   "raw": [{"fen": fens[i], "divide": raw[i][0], "total": raw[i][1]}
                           for i in range(len(fens))]}, cf)
    print("engine raw cached to", cache_path, flush=True)

    import multiprocessing as mp

    with mp.Pool(4) as pool:
        ref_divs = pool.map(ref_job, fens)
    print("python reference done (4 workers)", flush=True)

    results = []
    differing = []
    for i, fen in enumerate(fens):
        eng_div, eng_total = raw[i]
        ref_div = ref_divs[i]
        ref_total = sum(ref_div.values())
        missing = sorted(set(ref_div) - set(eng_div))
        extra = sorted(set(eng_div) - set(ref_div))
        wrong = sorted(m for m in set(ref_div) & set(eng_div) if ref_div[m] != eng_div[m])
        entry = {
            "position": i,
            "fen": fen,
            "root_moves_engine": len(eng_div),
            "root_moves_python": len(ref_div),
            "engine_total": eng_total,
            "python_total": ref_total,
            "per_divide_sum_equals_engine_total": sum(eng_div.values()) == eng_total,
            "missing": missing,
            "extra": extra,
            "wrong_counts": [{"move": m, "engine": eng_div[m], "python": ref_div[m]} for m in wrong],
            "differs": bool(missing or extra or wrong),
        }
        results.append(entry)
        if entry["differs"]:
            differing.append(entry)
        if (i + 1) % 20 == 0:
            print("compare %d/%d" % (i + 1, len(fens)), flush=True)

    summary = {
        "build": os.path.abspath(EXE),
        "sha256": sha256(EXE),
        "id_name": idname,
        "settings_regime": REGIME,
        "options_sent": OPTS,
        "depth": DEPTH,
        "positions": len(fens),
        "positions_compared": len(results),
        "root_moves_compared": sum(r["root_moves_python"] for r in results),
        "positions_differing": len(differing),
        "wrong_root_move_counts": sum(len(r["wrong_counts"]) for r in results),
        "missing_root_moves": sum(len(r["missing"]) for r in results),
        "extra_root_moves": sum(len(r["extra"]) for r in results),
        "engine_totals_matching_python": sum(1 for r in results if r["engine_total"] == r["python_total"]),
        "per_divide_sum_equals_engine_total": sum(1 for r in results if r["per_divide_sum_equals_engine_total"]),
    }
    with open(OUT, "w") as f:
        json.dump({"summary": summary, "differing": differing, "all": results}, f, indent=1)

    print()
    print("=== summary ===")
    for k, v in summary.items():
        print("%-38s %s" % (k, v))
    if len(results) == 0:
        print("\nNOT SHOWN: zero positions compared. This is NOT a pass.")
    elif differing:
        print("\nDIFFERENCES: %d positions" % len(differing))
        for d in differing[:10]:
            print("  position %d: missing %s extra %s wrong %s"
                  % (d["position"], d["missing"], d["extra"], d["wrong_counts"]))
    else:
        print("\nVERDICT: %d positions, %d root moves compared at perft %d, 0 differences."
              % (len(results), summary["root_moves_compared"], DEPTH))


main()
