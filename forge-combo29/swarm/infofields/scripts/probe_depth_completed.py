"""Probe: does `depth` on the wire mean a *completed* iteration?

Two independent shapes are tested.

A.  ABORT CONFLATION.  The abort branch in search.cpp re-emits the pv of an
    unfinished iteration under that iteration's depth, while carrying the
    previous finished iteration's score:

        if (!stopped_by_nodes_ && ss->pv_length > 0 && ...) {
            result.best_move = ss->pv[0]; result.pv = ss->pv[..pv_length];
            emit(depth, result.score, result.pv);   // depth = UNFINISHED iter
        }

    Decisive wire test: if a depth D is published twice -- once by an abort
    revision and once by a completed iteration -- with two different scores for
    the same position, then the abort revision's `depth D` was not a completed
    depth D. Each run uses a FRESH process, so no warm-history confound.

B.  A/A DETERMINISM CONTROL.  Two identical fresh-process runs at a fixed depth
    must agree line for line; otherwise the A test proves nothing.
"""

import json
import os

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
os.makedirs(OUT, exist_ok=True)

FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
SETTINGS = {
    "build": "g++ / -DFORGE_MARCH=x86-64-v4 / Release / NDEBUG",
    "base_commit": "6b98f217",
    "threads": 1, "hash_mb": "default 32", "own_book": False,
    "process": "fresh process per search (no cross-run state)",
}


def fresh_run(go, stop_after=None, fen=FEN, options=()):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    for name, value in options:
        e.setoption(name, value)
    e.position(fen)
    lines, bm = e.search(go, stop_after=stop_after, timeout=300)
    e.quit()
    rows = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if not f or "depth" not in f:
            continue
        rows.append({"depth": int(f["depth"]), "score": f["score"],
                     "nodes": int(f["nodes"]), "time": int(f["time"]),
                     "pv": pv, "line": l})
    return {"go": go, "stop_after_s": stop_after, "rows": rows,
            "bestmove": bm, "raw_tail": lines[-2:]}


def main():
    out = {"settings": SETTINGS, "fen": FEN}

    # --- B: A/A control, two identical runs, fixed depth, fresh processes.
    aa = [fresh_run("depth 12"), fresh_run("depth 12")]
    same = [r["line"] for r in aa[0]["rows"]] == [r["line"] for r in aa[1]["rows"]]
    out["aa_control"] = {
        "go": "depth 12", "identical": same,
        "run1_tail": [r["line"] for r in aa[0]["rows"][-3:]],
        "run2_tail": [r["line"] for r in aa[1]["rows"][-3:]]}

    # --- B2: A/A control on the abort path itself (same stop time twice).
    ab = [fresh_run("depth 40", stop_after=0.60), fresh_run("depth 40", stop_after=0.60)]
    out["aa_control_abort"] = {
        "stop_after_s": 0.60,
        "depths_equal": [r["depth"] for r in ab[0]["rows"]] == [r["depth"] for r in ab[1]["rows"]],
        "run1_last": ab[0]["rows"][-1]["line"], "run2_last": ab[1]["rows"][-1]["line"],
        "run1_bestmove": ab[0]["bestmove"], "run2_bestmove": ab[1]["bestmove"]}

    # --- A: ladder of abort times; collect every (depth -> scores seen).
    runs = []
    for t in (0.30, 0.45, 0.60, 0.80, 1.00, 1.30, 1.70, 2.20):
        runs.append(fresh_run("depth 40", stop_after=t))
    out["abort_runs"] = runs

    seen = {}
    for run in runs:
        for r in run["rows"]:
            seen.setdefault(r["depth"], []).append(
                {"score": r["score"], "nodes": r["nodes"], "go": run["go"],
                 "stop_after_s": run["stop_after_s"], "line": r["line"],
                 "was_last_line": r is run["rows"][-1]})
    conflicts = []
    for d, entries in sorted(seen.items()):
        scores = {e["score"] for e in entries}
        if len(scores) > 1:
            conflicts.append({"depth": d, "scores": sorted(scores),
                              "entries": entries})
    out["depth_score_conflicts"] = conflicts

    # A depth is "completed" only in a run that went on to a greater depth.
    completed_conflicts = []
    for c in conflicts:
        completed = [e for e in c["entries"] if not e["was_last_line"]]
        if len({e["score"] for e in completed}) > 1:
            completed_conflicts.append({"depth": c["depth"],
                                        "completed_scores": sorted({e["score"] for e in completed}),
                                        "entries": completed})
    out["completed_depth_conflicts"] = completed_conflicts

    with open(os.path.join(OUT, "depth_completed.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print("AA identical:", same, "| abort AA depths equal:",
          out["aa_control_abort"]["depths_equal"])
    print("depths with >1 distinct score:", len(conflicts))
    for c in conflicts:
        kinds = []
        for e in c["entries"]:
            kinds.append("%s@%.2fs%s" % (e["score"], e["stop_after_s"] or 0,
                                         " (LAST)" if e["was_last_line"] else ""))
        print("  depth %-2d: %s" % (c["depth"], ", ".join(kinds)))
    print("depths where two *completed* runs disagree:", len(completed_conflicts))
    for c in completed_conflicts:
        print("  depth", c["depth"], c["completed_scores"])


if __name__ == "__main__":
    main()
