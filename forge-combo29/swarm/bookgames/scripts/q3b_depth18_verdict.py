"""Q3, decisive half: for every book move that conceded material, ask the engine
at depth 18 whether it is actually worse than its own top choice.

The material judge in q3_book_vs_search.py answers "did this move give up
material". That is NOT the same question as "is this book move bad", and
conflating them is the error this audit must not make. A gambit gives up a pawn
and is not a defect. So every material concession is re-asked here with the
engine's own evaluation at depth 18, the depth the brief requires before anything
may be called a defect.

How the comparison is made, and why this way:

  * The engine is queried with OwnBook OFF at the position, depth 18, and its top
    move and score are recorded.
  * The book move's score is obtained by forcing it through `go depth 18
    searchmoves <bookmove>` and reading the resulting score.
  * `searchmoves` perturbs search ORDER (findings §6) but not the root
    evaluation's meaning, and here both arms are single-move-ish comparisons of
    the SAME position, so the perturbation is bounded by the measured noise floor
    rather than ignored.

  * The noise floor is MEASURED, not assumed: the same position is searched twice
    with an identical command and the absolute score difference recorded. Any gap
    at or below that floor is reported as "within the noise floor", never as a
    defect, and the floor is printed beside the count.

A move is called a defect ONLY if the gap is at least a pawn AND strictly above
the measured noise floor. Everything else is "material conceded, the evaluation
does not condemn it" -- which is what a gambit looks like.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import statistics
import sys
import time

import chess

from forge_uci import Engine

DEPTH = 18


def probe(job) -> dict:
    engine_path, fen, book_move, depth, timeout = job
    out = {"fen": fen, "book_move": book_move, "depth": depth,
           "top_move": None, "top_score": None, "book_forced_score": None,
           "gap_cp": None, "repeat_gap_cp": None, "error": None}
    eng = Engine(engine_path)
    try:
        eng.handshake()
        eng.newgame()
        eng.setoption("OwnBook", "false")

        eng.position_checked(f"fen {fen}")
        r1 = eng.go(f"depth {depth}", timeout)
        if r1.timed_out:
            out["error"] = "unrestricted search timed out"
            return out
        out["top_move"] = r1.bestmove()
        out["top_score"] = r1.last_score_cp()

        # noise floor: same command again
        eng.position_checked(f"fen {fen}")
        r2 = eng.go(f"depth {depth}", timeout)
        s2 = r2.last_score_cp()
        if s2 is not None and out["top_score"] is not None:
            out["repeat_gap_cp"] = abs(s2 - out["top_score"])

        eng.position_checked(f"fen {fen}")
        r3 = eng.go(f"depth {depth} searchmoves {book_move}", timeout)
        out["book_forced_score"] = r3.last_score_cp()
        if r3.bestmove() not in (book_move, None):
            out["error"] = f"searchmoves returned {r3.bestmove()} instead of {book_move}"

        if out["top_score"] is not None and out["book_forced_score"] is not None:
            out["gap_cp"] = out["top_score"] - out["book_forced_score"]
        return out
    except Exception as exc:                                  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    finally:
        eng.quit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--losses", required=True, help="q3 report JSON with loss_detail")
    ap.add_argument("--out", required=True)
    ap.add_argument("--depth", type=int, default=DEPTH)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--pawn", type=int, default=100)
    args = ap.parse_args()

    report = json.load(open(args.losses))
    items = []
    for w in report["loss_detail"]:
        mv = w.get("judged_move") or w.get("book_move")
        if mv:
            items.append((w["fen"], mv))
    items = list(dict.fromkeys(items))
    print(f"{len(items)} distinct material-concession book moves at depth {args.depth}")

    jobs = [(args.engine, fen, mv, args.depth, args.timeout) for fen, mv in items]
    results = []
    started = time.monotonic()
    with mp.Pool(args.workers) as pool:
        for n, res in enumerate(pool.imap_unordered(probe, jobs), 1):
            results.append(res)
            print(f"  {n}/{len(jobs)} {res['book_move']} gap={res['gap_cp']}", flush=True)

    ok = [r for r in results if r["error"] is None and r["gap_cp"] is not None]
    floors = [r["repeat_gap_cp"] for r in ok if r["repeat_gap_cp"] is not None]
    noise_floor = max(floors) if floors else None

    defects = [r for r in ok if r["gap_cp"] >= args.pawn and
               (noise_floor is None or r["gap_cp"] > noise_floor)]
    within_noise = [r for r in ok if noise_floor is not None and r["gap_cp"] <= noise_floor]

    out = {
        "engine": args.engine,
        "depth": args.depth,
        "concession_moves": len(items),
        "probed_ok": len(ok),
        "errors": [r for r in results if r["error"]][:10],
        "noise_floor_cp_max": noise_floor,
        "noise_floor_cp_mean": round(statistics.fmean(floors), 1) if floors else None,
        "noise_floor_method": "same position, same `go depth 18` command, twice; the "
                              "absolute score difference is the floor",
        "condemned_as_defect": len(defects),
        "defect_detail": defects,
        "within_noise_floor": len(within_noise),
        "gaps_cp": sorted(r["gap_cp"] for r in ok),
        "median_gap_cp": statistics.median([r["gap_cp"] for r in ok]) if ok else None,
        "elapsed_s": round(time.monotonic() - started, 1),
    }
    out["verdict"] = (
        f"{len(defects)} of {len(ok)} material concessions are condemned at depth "
        f"{args.depth} (gap >= {args.pawn} cp and above the measured noise floor of "
        f"{noise_floor} cp). The rest concede material without the engine calling them "
        "worse -- which is what a gambit looks like, and is not a defect."
        if defects else
        f"NONE of the {len(ok)} material concessions is condemned at depth {args.depth}: "
        f"every gap is under a pawn or inside the measured noise floor of {noise_floor} cp. "
        "Material was conceded; the evaluation does not call it a loss."
    )
    json.dump(out, open(args.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("defect_detail", "errors")}, indent=1))
    for d in defects:
        print("  DEFECT:", d["fen"], d["book_move"], "gap", d["gap_cp"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
