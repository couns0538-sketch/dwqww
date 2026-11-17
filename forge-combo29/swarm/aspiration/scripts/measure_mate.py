"""Measure 2: mate windows.

An aspiration window around a mate score is the dangerous case. Three questions:

 1. When an iteration's window sits around a mate score, is the mate re-searched
    until it is strictly inside the window (exact), or can a mate-SIZED BOUND be
    published as `mate N`? Answered from the traced build's `inside` flag, which
    is computed on the internal integers and cannot be fooled by the wire format.

 2. Does the reported MATE DISTANCE agree with an independent DTM proof
    (`gen_mates.py`), at a depth deep enough to see it?

 3. Does a wide window (AspirationDelta 200, and aspiration fully off) change the
    mate verdict or the distance? If turning aspiration off changes a mate
    verdict, aspiration is not a pure speed optimisation on this engine.

Also probes `go mate N`, which trap 3a0 shows is a DIFFERENT SEARCH: there the
window is [mated_in(ply), mate_in(ply+1)] and an empty window returns alpha
(search.cpp:1431-1435), so it is the one place a bound could reach the caller.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import asp_paths  # noqa: E402
from uci import Engine  # noqa: E402

EVIDENCE = asp_paths.EVIDENCE
BUILDS = {name: str(asp_paths.binary(name)) for name in asp_paths.BUILD_FLAGS}
BASE = {"OwnBook": "false"}


def run(build, opts, fen, go, trace=True):
    merged = dict(BASE)
    merged.update(opts or {})
    with Engine(BUILDS[build], merged) as eng:
        eng.newgame()
        eng.position(fen)
        return eng.search(go, collect_trace=trace)


def top(fen, res):
    rows = {}
    for row in res["info"]:
        if row["depth"] is not None:
            rows[row["depth"]] = row
    if not rows:
        return None
    return rows[max(rows)]


def mate_of(row):
    """The `mate N` value straight off the wire, sign included, or None."""
    if not row or not row.get("is_mate"):
        return None
    return row["score"]


def main():
    corpus = json.loads((EVIDENCE / "corpus.json").read_text())
    mates = corpus["mate_positions"]
    out = {"rows": [], "go_mate_rows": []}

    for pos in mates:
        fen = pos["fen"]
        dtm = pos["dtm_plies"]
        row = {"label": pos["label"], "fen": fen, "dtm_plies": dtm,
               "expected_mate_in": pos["mate_in"], "arms": {}}

        # Deep enough to see the mate: dtm plies + 4 gives the search room past
        # the mate horizon, and mates are capped by mate_depth anyway.
        depth = max(8, dtm + 4)
        go = f"go depth {depth}"
        for arm, build, opts in (
            ("asp_default", "trace", {}),
            ("asp_delta200", "trace", {"AspirationDelta": 200}),
            ("asp_off", "noasp", {}),
            ("capped_reopen", "trace", {"AspCappedReopen": "true"}),
            ("arm_late", "trace", {"AspArmLate": "true"}),
        ):
            res = run(build, opts, fen, go, trace=(build == "trace"))
            t = top(fen, res)
            traces = res["traces"]
            last = traces[-1] if traces else None
            row["arms"][arm] = {
                "go": go,
                "depth": t["depth"] if t else None,
                "score_kind": t["score_kind"] if t else None,
                "score": t["score"] if t else None,
                "mate_in": mate_of(t),
                "bestmove": res["bestmove"],
                "pv": t["pv"] if t else [],
                "nodes": t["nodes"] if t else None,
                "final_inside": last.get("inside") if last else None,
                "final_exit": last.get("exit") if last else None,
                "final_window": [last.get("fa"), last.get("fb")] if last else None,
                "iterations_with_mate_score": sum(
                    1 for tr in traces if abs(tr.get("score", 0)) >= 31000),
                "bound_iterations": sum(1 for tr in traces if tr.get("inside") == 0),
            }

        base = row["arms"]["asp_default"]
        row["mate_agrees_with_proof"] = (base["mate_in"] is not None and
                                         abs(base["mate_in"]) == pos["mate_in"])
        row["publishes_mate_as_value"] = base["final_inside"] == 1
        row["any_arm_mate_differs"] = len({
            (a["mate_in"], a["bestmove"]) for a in row["arms"].values()}) > 1
        out["rows"].append(row)

    # `go mate N`: the window narrows to [mated_in(ply), mate_in(ply+1)] and an
    # empty window returns alpha. Probe whether a non-mate score can come back.
    for pos in mates:
        fen = pos["fen"]
        n = pos["mate_in"]
        res = run("trace", {}, fen, f"go mate {n}", trace=True)
        t = top(fen, res)
        traces = res["traces"]
        last = traces[-1] if traces else None
        out["go_mate_rows"].append({
            "label": pos["label"], "fen": fen, "asked_mate_in": n,
            "go": f"go mate {n}", "depth": t["depth"] if t else None,
            "score_kind": t["score_kind"] if t else None,
            "score": t["score"] if t else None,
            "mate_in": mate_of(t), "bestmove": res["bestmove"],
            "final_inside": last.get("inside") if last else None,
            "final_exit": last.get("exit") if last else None,
            "bound_iterations": sum(1 for tr in traces if tr.get("inside") == 0),
            "iterations": len(traces),
        })

    (EVIDENCE / "mate_windows.json").write_text(json.dumps(out, indent=2) + "\n")

    print(f"{'label':22s} {'dtm':>4} {'asp mate':>9} {'bound?':>7} {'off mate':>9} {'d200 mate':>10} {'arms differ':>11}")
    for r in out["rows"]:
        a = r["arms"]["asp_default"]
        off = r["arms"]["asp_off"]
        d2 = r["arms"]["asp_delta200"]
        print(f"{r['label']:22s} {r['dtm_plies']:>4} {str(a['mate_in']):>9} "
              f"{str(a['final_inside']):>7} {str(off['mate_in']):>9} {str(d2['mate_in']):>10} "
              f"{str(r['any_arm_mate_differs']):>11}")
    print()
    print(f"mate verdict agrees with DTM proof: {sum(r['mate_agrees_with_proof'] for r in out['rows'])}/{len(out['rows'])}")
    print(f"published as a value (inside window): {sum(r['publishes_mate_as_value'] for r in out['rows'])}/{len(out['rows'])}")
    print(f"any arm changes the mate verdict:     {sum(r['any_arm_mate_differs'] for r in out['rows'])}/{len(out['rows'])}")
    print()
    print("go mate N:")
    for r in out["go_mate_rows"]:
        print(f"  {r['label']:22s} asked={r['asked_mate_in']} got={r['score_kind']}/{r['score']} "
              f"depth={r['depth']} inside={r['final_inside']} exit={r['final_exit']} "
              f"bounds={r['bound_iterations']}/{r['iterations']}")


if __name__ == "__main__":
    main()
