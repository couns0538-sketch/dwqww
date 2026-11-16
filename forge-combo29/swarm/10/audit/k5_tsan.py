#!/usr/bin/env python3
"""k5_tsan.py -- K5: "Threads 2 and 4 on the first 50 of O gave 0 reports", tested with the brief's
two proofs, on MY OWN TSan build and MY OWN planted race.

  proof 1: nm -C <exe> | grep -c __tsan_  > 0, recorded in the .meta
  proof 2: a scratch copy with ONE planted race (an unlocked global counter written by every thread)
           is reported by THE SAME RUNNER, which must count the sanitizer report

Then the claim itself: the first 50 of O, Threads 2 and Threads 4, depth 12, S14, one fresh process
per search, EOF-safe driver, TSAN_OPTIONS cleared.

Usage: k5_tsan.py OUTDIR
Exit codes are recorded per search; TSan reports are counted from stderr.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drv import Drv

REAL = os.path.expanduser("~/builds/tsan/forge")
PLANTED = os.path.expanduser("~/builds/planted_tsan/forge")
OUT = os.path.abspath(sys.argv[1])
SETS = os.path.join(OUT, "sets")
os.makedirs(os.path.join(OUT, "K5"), exist_ok=True)

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

TSAN_MARK = ("WARNING: ThreadSanitizer", "ThreadSanitizer: data race", "SUMMARY: ThreadSanitizer")


def nm_count(exe):
    try:
        out = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, timeout=120).stdout
        return out.count("__tsan_")
    except Exception:
        return -1


def env_clean():
    e = {k: v for k, v in os.environ.items()
         if k not in ("TSAN_OPTIONS", "ASAN_OPTIONS", "UBSAN_OPTIONS")}
    return e


def search(exe, fen, threads, timeout=300):
    """one fresh process; returns a record with nodes, bestmove, exit code and TSan report count"""
    d = None
    rec = {"fen": fen, "threads": threads, "nodes": None, "bestmove": None,
           "tsan_reports": 0, "rc": None, "error": None}
    try:
        d = Drv(exe, timeout=timeout)
        d.uci()
        d.isready()
        d.opt("Threads", str(threads))
        d.opt("Hash", "16")
        for k, v in S14:
            d.opt(k, v)
        d.isready()
        d.write("ucinewgame")
        d.isready()
        d.pos("position fen " + fen)
        nodes, best, lines = d.go("go depth 12", timeout=timeout)
        rec["nodes"] = nodes
        rec["bestmove"] = best
    except Exception as e:                                   # noqa: BLE001
        rec["error"] = "%s: %s" % (type(e).__name__, e)
    finally:
        if d is not None:
            try:
                stderr = d.p.stderr.read() if d.p.stderr else ""
            except Exception:
                stderr = ""
            rec["tsan_reports"] = sum(stderr.count(m) for m in TSAN_MARK[:2])
            rec["tsan_summary"] = stderr.count(TSAN_MARK[2])
            try:
                d.write("quit")
                rec["rc"] = d.p.wait(timeout=20)
            except Exception:
                d.p.kill()
                rec["rc"] = "killed"
    return rec


fens = [l.strip() for l in open(os.path.join(SETS, "first200.fens")) if l.strip()][:50]
meta = {"real_exe": REAL, "real_nm_tsan": nm_count(REAL),
        "planted_exe": PLANTED, "planted_nm_tsan": nm_count(PLANTED),
        "positions": len(fens), "depth": 12, "hash": 16, "s14": S14,
        "TSAN_OPTIONS": os.environ.get("TSAN_OPTIONS", "unset")}
with open(os.path.join(OUT, "K5", "meta.json"), "w") as f:
    json.dump(meta, f, indent=2)
    f.write("\n")

# ---- proof 2: the planted race must be counted by THIS runner
proof = search(PLANTED, fens[0], 4)
with open(os.path.join(OUT, "K5", "proof_planted.json"), "w") as f:
    json.dump(proof, f, indent=2)
    f.write("\n")
print("PROOF planted: tsan_reports=%s summary=%s error=%s"
      % (proof["tsan_reports"], proof.get("tsan_summary"), proof["error"]), flush=True)

# ---- the claim: Threads 2 and 4 over the first 50 of O
res = {}
for threads in (2, 4):
    rows = []
    for i, fen in enumerate(fens):
        r = search(REAL, fen, threads)
        rows.append(r)
        if i % 10 == 0:
            print("  T%d %d/%d" % (threads, i, len(fens)), flush=True)
    res["T%d" % threads] = {
        "searches": len(rows),
        "tsan_reports_total": sum(r["tsan_reports"] for r in rows),
        "searches_with_a_report": sum(1 for r in rows if r["tsan_reports"] > 0),
        "errors": sum(1 for r in rows if r["error"]),
        "missing_bestmove": sum(1 for r in rows if r["bestmove"] is None),
        "null_nodes": sum(1 for r in rows if r["nodes"] is None),
        "rows": rows,
    }
    with open(os.path.join(OUT, "K5", "sweep_%s.json" % threads), "w") as f:
        json.dump(res["T%d" % threads], f, indent=1)
        f.write("\n")

summary = {
    "proof1_nm_tsan_gt_0": meta["real_nm_tsan"] > 0,
    "proof2_planted_reported_by_same_runner": proof["tsan_reports"] > 0,
    "T2_reports": res["T2"]["tsan_reports_total"],
    "T4_reports": res["T4"]["tsan_reports_total"],
    "T2_searches": res["T2"]["searches"],
    "T4_searches": res["T4"]["searches"],
}
summary["verdict"] = (
    "PASS (0 reports, shown)" if (summary["proof1_nm_tsan_gt_0"] and
                                  summary["proof2_planted_reported_by_same_runner"] and
                                  summary["T2_reports"] == 0 and summary["T4_reports"] == 0)
    else "REFUTED or NOT SHOWN")
with open(os.path.join(OUT, "K5", "summary.json"), "w") as f:
    json.dump(summary, f, indent=2)
    f.write("\n")
print(json.dumps(summary, indent=2))
