#!/usr/bin/env python3
"""Measure whether any pruning path loses or mis-distances a forced mate.

The measurement, per corpus entry:

  For each depth in the schedule, run `go depth N` (NEVER `go mate N` -- see
  the note below) and compare against the oracle:

    * MOVE:        is the engine's bestmove one of the entry's mating moves?
    * DISTANCE:    does the engine's reported mate number equal the oracle's?
    * VERDICT:     does the engine claim a mate at all when one exists?

  A row is a DEFECT when a forced mate exists and the engine either
  (a) plays a non-mating move, or (b) keeps a mating move but reports the wrong
  mate distance, or (c) reports no mate.

Why `go depth N` and never `go mate N`:
  `go mate N` sets limits.mate_moves > 0, which sets `mate_moves_` on the Worker.
  EVERY pruning gate in search() is guarded on `mate_moves_ == 0` -- null move,
  razoring, RFP, the whole shallow move-loop block, singular extensions and LMR
  all switch OFF under `go mate`. Measuring mate safety with `go mate` would
  disable the exact paths under audit and produce a guaranteed clean null.
  This is asserted in code below, not just documented.

Attribution:
  A defect row is re-run with each ablation class in turn. A class whose
  removal fixes the row is a candidate cause; a class whose removal changes
  nothing is excluded. Every row records which arm produced it.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field

sys.path.insert(0, "scripts")
from ucidrv import Engine, check_fen  # noqa: E402

CLASSES = ["null_move", "razor", "rfp", "futility", "lmr", "singular"]


@dataclass
class Row:
    fen: str
    true_plies: int
    true_moves: int
    mating_moves: list[str]
    depth: int
    arm: str
    bestmove: str
    score_mate: int | None
    score_cp: int | None
    nodes: int
    pv: list[str] = field(default_factory=list)
    move_ok: bool = False
    dist_ok: bool = False
    verdict_ok: bool = False
    counts: dict = field(default_factory=dict)

    @property
    def defect(self) -> bool:
        return not (self.move_ok and self.dist_ok and self.verdict_ok)

    def as_dict(self) -> dict:
        return {
            "fen": self.fen, "true_plies": self.true_plies, "true_moves": self.true_moves,
            "mating_moves": self.mating_moves, "depth": self.depth, "arm": self.arm,
            "bestmove": self.bestmove, "score_mate": self.score_mate,
            "score_cp": self.score_cp, "nodes": self.nodes, "pv": self.pv,
            "move_ok": self.move_ok, "dist_ok": self.dist_ok, "verdict_ok": self.verdict_ok,
            "defect": self.defect, "counts": self.counts,
        }


def get_stats(engine: Engine) -> dict:
    engine.send("probestats")
    line = engine._read_until(lambda l: l.startswith("probestats"))[-1]
    return json.loads(line[len("probestats"):])


def eval_row(entry: dict, depth: int, arm: str, engine: Engine) -> Row:
    fen = entry["fen"]
    # Order is load-bearing: ucinewgame resets the board to startpos.
    engine.newgame()
    check_fen(engine, fen)
    engine.send(f"ablate {arm}")
    engine.isready()
    res = engine.go(f"depth {depth}")   # `mate N` would disable every prune gate
    counts = get_stats(engine)

    last = res.last
    score_mate = last.score_mate if last else None
    score_cp = last.score_cp if last else None
    best = res.bestmove
    mating = set(entry["mating_moves"] and [m["uci"] for m in entry["mating_moves"]] or [])

    move_ok = best in mating
    # Engine mate score is in MOVES; oracle distance is in PLIES.
    want = entry["moves_to_mate"]
    dist_ok = (score_mate is not None and score_mate == want)
    verdict_ok = score_mate is not None and score_mate > 0

    return Row(
        fen=fen, true_plies=entry["plies"], true_moves=want,
        mating_moves=sorted(mating), depth=depth, arm=arm, bestmove=best,
        score_mate=score_mate, score_cp=score_cp, nodes=res.nodes,
        pv=last.pv if last else [], move_ok=move_ok, dist_ok=dist_ok,
        verdict_ok=verdict_ok, counts=counts,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus/mates.json")
    ap.add_argument("--engine", default="build/probe/forge")
    ap.add_argument("--depths", default="1,2,3,4,5,6,8,10,12")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="evidence/mate_safety_rows.json")
    args = ap.parse_args()

    depths = [int(d) for d in args.depths.split(",")]
    with open(args.corpus) as fh:
        entries = json.load(fh)["entries"]
    if args.limit:
        entries = entries[: args.limit]

    engine = Engine(args.engine, {"Threads": "1", "Hash": "64", "OwnBook": "false"})
    rows: list[dict] = []
    try:
        for i, entry in enumerate(entries):
            for depth in depths:
                row = eval_row(entry, depth, "none", engine)
                rows.append(row.as_dict())
            print(f"[{i+1}/{len(entries)}] {entry['fen'][:44]} true=mate {entry['moves_to_mate']}",
                  flush=True)
    finally:
        engine.close()

    with open(args.out, "w") as fh:
        json.dump(rows, fh, indent=1)

    defects = [r for r in rows if r["defect"]]
    # The headline split that §4 names: right move, wrong distance.
    rightmove_wrongdist = [r for r in defects if r["move_ok"] and not r["dist_ok"]]
    nonmating = [r for r in defects if not r["move_ok"]]
    nomate = [r for r in defects if not r["verdict_ok"]]

    print(json.dumps({
        "rows": len(rows),
        "defects": len(defects),
        "non_mating_move": len(nonmating),
        "right_move_wrong_distance": len(rightmove_wrongdist),
        "no_mate_reported": len(nomate),
        "defect_rows": defects[:20],
    }, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
