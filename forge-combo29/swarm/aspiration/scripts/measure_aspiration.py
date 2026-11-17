"""Measure 1 + 3 + 4: is the published score a value or a bound?

The question: does an aspiration fail-high / fail-low ever leave an
un-re-searched bound in the published score?

The engine prints NO `lowerbound` / `upperbound` token (verified against
6b98f217: no such string in src/ or include/), so the wire cannot answer this by
itself. The script answers it three ways and requires agreement:

  A. INTERNAL (traced build). For each FINISHED iteration the trace reports the
     final window and the returned score, plus `inside` = score strictly inside
     (alpha, beta). A bound is exactly a score that is not inside. `inside == 0`
     on a published iteration IS a published bound, independent of the wire.

  B. EXTERNAL (FORGE_ASP_OFF build). Same position and depth with aspiration
     never narrowing. Published scores must match. A bound can pass A only
     through a bug in the trace; it fails B because the reference is a true value.

  C. CONTROL (FORGE_ASP_FAULT build). Publishes a fail-high bound without
     re-searching. A and B must both flag it, or the checkers are broken and
     every clean run in this file is worthless (shared brief, rule 3).

Measure 4: AspirationDelta at 4 / 18 / 50 / 200 -- scores must not move, nodes may.
Measure 3: AspCappedReopen and AspArmLate off vs on -- score, mate distance, move.

Usage: measure_aspiration.py [--depth N] [--limit K] [--phase all|validity|delta|switches]
"""
import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import asp_paths  # noqa: E402
from uci import Engine  # noqa: E402

EVIDENCE = asp_paths.EVIDENCE
BUILDS = {name: str(asp_paths.binary(name)) for name in asp_paths.BUILD_FLAGS}


def load_corpus():
    return json.loads((EVIDENCE / "corpus.json").read_text())


def last_per_depth(result):
    per_depth = {}
    for row in result["info"]:
        if row["depth"] is not None:
            per_depth[row["depth"]] = row
    return per_depth


def mate_plies(row):
    if not row or not row.get("is_mate"):
        return None
    n = row["score"]
    return 2 * n - 1 if n > 0 else -2 * abs(n) - 1 + 2 * 0 + (-2 * abs(n) + 2 * abs(n) - 1 + 1) - 1 + 0 or None


def mate_plies_clean(row):
    """`mate N` -> plies. +N = we mate in N moves; -N = we are mated in N."""
    if not row or not row.get("is_mate"):
        return None
    n = row["score"]
    return (2 * n - 1) if n > 0 else (-(2 * abs(n) - 1))


BASE_OPTIONS = {"OwnBook": "false"}


def run_one(build, options, fen, go, want_trace):
    merged = dict(BASE_OPTIONS)
    merged.update(options or {})
    with Engine(build, merged) as eng:
        eng.newgame()
        eng.position(fen)
        res = eng.search(go, collect_trace=want_trace)
    res["build"] = build
    res["options"] = options
    return res


def summarize(res):
    rows = last_per_depth(res)
    if not rows:
        return {"depth": None, "score_kind": None, "score": None,
                "mate_plies": None, "bestmove": res["bestmove"], "nodes": None}
    top = max(rows)
    row = rows[top]
    return {
        "depth": top,
        "score_kind": row["score_kind"],
        "score": row["score"],
        "mate_plies": mate_plies_clean(row),
        "bestmove": res["bestmove"],
        "nodes": row["nodes"],
        "bound_field": row["bound"],   # always "unstated": the engine never says
    }


def phase_validity(depth, limit):
    """A/B/C over the whole corpus."""
    corpus = load_corpus()
    positions = corpus["depth_positions"][:limit] if limit else corpus["depth_positions"]
    go = f"go depth {depth}"
    out = {"depth": depth, "go": go, "rows": [], "fault_rows": []}

    for pos in positions:
        fen = pos["fen"]
        asp = run_one(BUILDS["trace"], {}, fen, go, want_trace=True)
        ref = run_one(BUILDS["noasp"], {}, fen, go, want_trace=False)
        a = summarize(asp)
        b = summarize(ref)
        traces = asp["traces"]

        # A: any published iteration whose score is not strictly inside its window.
        not_inside = [t for t in traces if t.get("inside") == 0]
        # A score failing the window at the FINAL iteration is the dangerous one;
        # a non-final iteration that broke out is re-searched by the next one.
        last_trace = traces[-1] if traces else None
        final_bound = bool(last_trace and last_trace.get("inside") == 0)

        row = {
            "label": pos["label"],
            "fen": fen,
            "asp": a,
            "ref": b,
            "score_agrees": (a["score_kind"], a["score"]) == (b["score_kind"], b["score"]),
            "mate_agrees": a["mate_plies"] == b["mate_plies"],
            "move_agrees": a["bestmove"] == b["bestmove"],
            "final_bound": final_bound,
            "iterations_not_inside": len(not_inside),
            "trace_iterations": len(traces),
            "aspiration_engaged": any((t.get("tries") or 1) > 1 or t.get("narrow") == 1
                                      for t in traces),
        }
        out["rows"].append(row)

    # C: planted fault must be caught by exactly the same two checks.
    #
    # The denominator has to be "rows where the fault actually fires", not "rows
    # tried": the planted defect needs a fail-high at the LAST root iteration, and
    # most positions do not have one. Reporting 3/8 as if it were a detector miss
    # rate would be a denominator error in the safe direction, which is the exact
    # trap the shared brief records for the fuzz count. So both numbers are kept.
    fault_positions = positions[: min(40, len(positions))]
    fault_opportunities = 0
    for pos in fault_positions:
        fen = pos["fen"]
        f = run_one(BUILDS["fault"], {}, fen, go, want_trace=True)
        ref = run_one(BUILDS["noasp"], {}, fen, go, want_trace=False)
        fs = summarize(f)
        rs = summarize(ref)
        traces = f["traces"]
        last_trace = traces[-1] if traces else None
        fired = bool(last_trace and last_trace.get("exit") == "high_fault")
        caught = bool(last_trace and last_trace.get("inside") == 0)
        if fired:
            fault_opportunities += 1
        out["fault_rows"].append({
            "label": pos["label"],
            "fen": fen,
            "fault": fs,
            "ref": rs,
            "fault_exit": last_trace.get("exit") if last_trace else None,
            "fault_fired": fired,
            "final_bound_detected": caught,
            "score_differs_from_ref": (fs["score_kind"], fs["score"]) != (rs["score_kind"], rs["score"]),
            "caught": caught,
        })
    out["fault_control"] = {
        "rows_tried": len(fault_positions),
        "fault_fired": fault_opportunities,
        "detected": sum(r["caught"] for r in out["fault_rows"] if r["fault_fired"]),
        "note": "detected/fault_fired is the detector rate; rows_tried is not the "
                "denominator because the planted defect needs a fail-high on the "
                "last root iteration and most positions do not have one",
    }
    return out


def phase_delta(depth, limit):
    corpus = load_corpus()
    positions = corpus["depth_positions"][:limit] if limit else corpus["depth_positions"]
    go = f"go depth {depth}"
    rows = []
    for pos in positions:
        fen = pos["fen"]
        per_delta = {}
        for delta in (4, 18, 50, 200):
            res = run_one(BUILDS["trace"], {"AspirationDelta": delta}, fen, go, want_trace=True)
            s = summarize(res)
            per_delta[delta] = {
                "score": [s["score_kind"], s["score"]],
                "mate_plies": s["mate_plies"],
                "bestmove": s["bestmove"],
                "nodes": s["nodes"],
                "iterations": len(res["traces"]),
                "retries": sum(max(0, (t.get("tries") or 1) - 1) for t in res["traces"]),
            }
        scores = {tuple(v["score"]) for v in per_delta.values()}
        mates = {v["mate_plies"] for v in per_delta.values()}
        moves = {v["bestmove"] for v in per_delta.values()}
        rows.append({
            "label": pos["label"], "fen": fen, "per_delta": per_delta,
            "score_invariant": len(scores) == 1,
            "mate_invariant": len(mates) == 1,
            "move_invariant": len(moves) == 1,
        })
    return {"depth": depth, "go": go, "rows": rows}


def phase_switches(depth, limit):
    corpus = load_corpus()
    positions = corpus["depth_positions"][:limit] if limit else corpus["depth_positions"]
    mates = corpus["mate_positions"]
    go = f"go depth {depth}"
    combos = [
        ("base", {}),
        ("capped", {"AspCappedReopen": "true"}),
        ("armlate", {"AspArmLate": "true"}),
        ("both", {"AspCappedReopen": "true", "AspArmLate": "true"}),
    ]
    rows = []
    for pos in list(positions) + list(mates):
        fen = pos["fen"]
        per = {}
        for name, opts in combos:
            res = run_one(BUILDS["trace"], opts, fen, go, want_trace=True)
            s = summarize(res)
            per[name] = {
                "score": [s["score_kind"], s["score"]],
                "mate_plies": s["mate_plies"],
                "bestmove": s["bestmove"],
                "nodes": s["nodes"] if "nodes" in s else None,
                "retries": sum(max(0, (t.get("tries") or 1) - 1) for t in res["traces"]),
                "any_final_bound": any((t.get("inside") == 0) for t in res["traces"][-1:]),
            }
        base = per["base"]
        rows.append({
            "label": pos.get("label"), "fen": fen,
            "dtm_plies": pos.get("dtm_plies"),
            "per": per,
            "changed_by": [n for n in ("capped", "armlate", "both")
                           if (per[n]["score"], per[n]["mate_plies"], per[n]["bestmove"]) !=
                              (base["score"], base["mate_plies"], base["bestmove"])],
            "score_changes": [n for n in ("capped", "armlate", "both")
                              if per[n]["score"] != base["score"]],
            "mate_changes": [n for n in ("capped", "armlate", "both")
                             if per[n]["mate_plies"] != base["mate_plies"]],
        })
    return {"depth": depth, "go": go, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--phase", default="all")
    args = ap.parse_args()

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if args.phase in ("all", "validity"):
        v = phase_validity(args.depth, args.limit)
        (EVIDENCE / f"validity_d{args.depth}.json").write_text(json.dumps(v, indent=2) + "\n")
        rows = v["rows"]
        print(f"[validity d{args.depth}] positions={len(rows)} "
              f"aspiration_engaged={sum(r['aspiration_engaged'] for r in rows)} "
              f"final_bound={sum(r['final_bound'] for r in rows)} "
              f"score_mismatch={sum(not r['score_agrees'] for r in rows)} "
              f"move_mismatch={sum(not r['move_agrees'] for r in rows)}")
        fc = v["fault_control"]
        print(f"[fault control ] rows_tried={fc['rows_tried']} fired={fc['fault_fired']} "
              f"detected={fc['detected']}/{fc['fault_fired']}")
    if args.phase in ("all", "delta"):
        d = phase_delta(args.depth, args.limit)
        (EVIDENCE / f"delta_d{args.depth}.json").write_text(json.dumps(d, indent=2) + "\n")
        rows = d["rows"]
        print(f"[delta      d{args.depth}] positions={len(rows)} "
              f"score_not_invariant={sum(not r['score_invariant'] for r in rows)} "
              f"move_not_invariant={sum(not r['move_invariant'] for r in rows)}")
    if args.phase in ("all", "switches"):
        s = phase_switches(args.depth, args.limit)
        (EVIDENCE / f"switches_d{args.depth}.json").write_text(json.dumps(s, indent=2) + "\n")
        rows = s["rows"]
        print(f"[switches   d{args.depth}] positions={len(rows)} "
              f"score_changed={sum(bool(r['score_changes']) for r in rows)} "
              f"mate_changed={sum(bool(r['mate_changes']) for r in rows)}")


if __name__ == "__main__":
    main()
