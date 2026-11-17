"""Decisive test: is a `depth` on the wire a COMPLETED iteration?

search.cpp's abort branch re-emits a pv from the *unfinished* iteration under
that iteration's depth, and passes `result.score`, which is still the *previous*
iteration's score:

    if (!stopped_by_nodes_ && ss->pv_length > 0 && ...) {
        result.best_move = ss->pv[0];
        result.pv.assign(ss->pv.begin(), ss->pv.begin() + ss->pv_length);
        emit(depth, result.score, result.pv);      // depth D, score from D-1
    }

A line produced there is internally inconsistent, and that is detectable without
trusting any clock: a COMPLETED iteration D always carries the depth-D score and
the depth-D pv together. So for a given depth D we compare

  (1) the line a run to completion produces at depth D, against
  (2) the line an aborted run produces at depth D.

If (2)'s score equals the aborted run's own depth-(D-1) score and differs from
(1), then the aborted `depth D` is labelled with a depth it never finished at.

The control is an A/A pair: two full runs to depth D must agree exactly on
depth/score/pv (nodes and time may drift with the clock).
"""

import json
import os

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": 32, "own_book": False,
       "process": "fresh process per search"}


def run(go, stop_after=None):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.position(FEN)
    lines, bm = e.search(go, stop_after=stop_after, timeout=300)
    e.quit()
    rows = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f and "depth" in f:
            rows.append({"depth": int(f["depth"]), "score": f["score"],
                         "nodes": int(f["nodes"]), "time": int(f["time"]),
                         "pv": pv, "line": l})
    return {"rows": rows, "bestmove": bm}


def sig(rows):
    return [(r["depth"], r["score"], tuple(r["pv"])) for r in rows]


# A depth is only "finished" by a run that continues past it.
TARGET = None
reference = run("depth 22")
full = {r["depth"]: r for r in reference["rows"]}

# pick the depth most often reported last by aborts, so the test bites
trials = [0.50, 0.65, 0.80, 1.00, 1.20, 1.45, 1.75, 2.10, 2.60, 3.20]
aborts = []
for t in trials:
    r = run("depth 40", stop_after=t)
    r["stop_after_s"] = t
    aborts.append(r)

last_depths = [a["rows"][-1]["depth"] for a in aborts if a["rows"]]
TARGET = max(set(last_depths), key=last_depths.count)

findings = []
for a in aborts:
    rows = a["rows"]
    if not rows:
        continue
    last = rows[-1]
    prev = rows[-2] if len(rows) > 1 else None
    if last["depth"] != TARGET or prev is None:
        continue
    ref = full.get(TARGET)
    entry = {
        "stop_after_s": a["stop_after_s"],
        "last_line": last["line"],
        "last_depth": last["depth"],
        "last_score": last["score"],
        "prev_depth": prev["depth"],
        "prev_score": prev["score"],
        "prev_pv": prev["pv"],
        "last_pv": last["pv"],
        "reference_depth_line": ref["line"] if ref else None,
        "reference_score": ref["score"] if ref else None,
        "reference_pv": ref["pv"] if ref else None,
        "score_equals_prev": last["score"] == prev["score"],
        "score_differs_from_reference": bool(ref) and last["score"] != ref["score"],
        "pv_differs_from_reference": bool(ref) and last["pv"] != ref["pv"],
    }
    entry["violation"] = (entry["score_equals_prev"] and
                          entry["score_differs_from_reference"])
    findings.append(entry)

aa1, aa2 = run("depth 12"), run("depth 12")
control = {"identical_depth_score_pv": sig(aa1["rows"]) == sig(aa2["rows"]),
           "run1_last": aa1["rows"][-1]["line"], "run2_last": aa2["rows"][-1]["line"]}

payload = {"settings": SET, "fen": FEN, "aa_control": control,
           "reference_depth_22": reference["rows"],
           "aborts": [{k: v for k, v in a.items() if k != "rows"} | {"rows": a["rows"]}
                      for a in aborts],
           "target_depth": TARGET, "findings": findings}
with open(os.path.join(OUT, "depth_abort_decisive.json"), "w") as fh:
    json.dump(payload, fh, indent=1, sort_keys=True)

print("A/A control identical (depth,score,pv):", control["identical_depth_score_pv"])
print("target depth:", TARGET, "| aborts landing there:", len(findings))
for f in findings:
    print("  stop %.2fs: d%d %s  (prev d%d %s)  ref d%d %s" % (
        f["stop_after_s"], f["last_depth"], f["last_score"],
        f["prev_depth"], f["prev_score"], TARGET, f["reference_score"]))
    print("     violation:", f["violation"])
    print("     wire:", f["last_line"][:200])
