#!/usr/bin/env python3
"""Build the feature x fixture matrix the owner asked for.

For each pruning feature, in each mate fixture, at a stated depth:
  * did the feature FIRE (counter > 0)?
  * and did the answer SURVIVE (correct move AND correct distance)?

A row where the feature never fires is reported as NOT REACHED, not as safe.
That distinction is the whole point: the brief's kill condition is a corpus that
never touches the pruning path, and a "no defect" on such a row is vacuous.

Output is a Markdown table plus JSON, both keyed on feature x fixture x depth.
"""

from __future__ import annotations

import json
import sys

sys.path.insert(0, "scripts")
from ucidrv import Engine, check_fen  # noqa: E402

# feature -> the counter fields that prove it fired
FEATURES = {
    "null_move": ["null_try", "null_cutoff"],
    "razor": ["razor_entered", "razor_cutoff"],
    "rfp": ["rfp_cutoff"],
    "futility(quiet)": ["futility_quiet_skip"],
    "futility(capture)": ["futility_capture_skip"],
    "lmp": ["lmp_skipped_moves"],
    "see_quiet": ["see_quiet_skip"],
    "see_noisy": ["see_noisy_skip"],
    "hist_prune": ["hist_quiet_skip"],
    "lmr": ["lmr_reduced"],
    "singular": ["singular_search", "singular_extension1", "singular_extension2"],
    "mate_alpha_node": ["nodes_with_mate_alpha"],
}


def get_stats(engine: Engine) -> dict:
    engine.send("probestats")
    line = engine._read_until(lambda l: l.startswith("probestats"))[-1]
    return json.loads(line[len("probestats"):])


def main() -> int:
    depths = [int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else "8,10").split(",")]
    with open("corpus/mates.json") as fh:
        entries = json.load(fh)["entries"]

    engine = Engine("build/probe/forge", {"Threads": "1", "Hash": "64", "OwnBook": "false"})
    rows = []
    try:
        for entry in entries:
            fen = entry["fen"]
            mating = {m["uci"] for m in entry["mating_moves"]}
            want = entry["moves_to_mate"]
            for d in depths:
                engine.newgame()
                check_fen(engine, fen)
                engine.isready()
                r = engine.go(f"depth {d}")
                s = get_stats(engine)
                last = r.last
                sm = last.score_mate if last else None
                rows.append({
                    "fen": fen, "depth": d, "true_moves": want,
                    "mating_moves": sorted(mating),
                    "bestmove": r.bestmove, "score_mate": sm,
                    "score_cp": last.score_cp if last else None,
                    "nodes": r.nodes,
                    "move_ok": r.bestmove in mating,
                    "dist_ok": sm == want,
                    "correct": r.bestmove in mating and sm == want,
                    "counts": s,
                })
            print(f"{fen[:46]} ok={rows[-1]['correct']}", flush=True)
    finally:
        engine.close()

    with open("evidence/matrix.json", "w") as fh:
        json.dump(rows, fh, indent=1)

    # Build the feature x fixture table.
    lines = ["| feature | fired in N fixtures | answer survived where it fired | answer wrong where it fired |",
             "|---|---|---|---|"]
    summary = {}
    for label, fields in FEATURES.items():
        fired_rows = [r for r in rows if any(r["counts"].get(f, 0) > 0 for f in fields)]
        ok = sum(1 for r in fired_rows if r["correct"])
        bad = len(fired_rows) - ok
        summary[label] = {"fired_rows": len(fired_rows), "survived": ok, "wrong": bad}
        lines.append(f"| {label} | {len(fired_rows)} | {ok} | {bad} |")

    with open("evidence/matrix.md", "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(json.dumps({"rows": len(rows), "by_feature": summary,
                      "total_wrong": sum(1 for r in rows if not r["correct"])}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
