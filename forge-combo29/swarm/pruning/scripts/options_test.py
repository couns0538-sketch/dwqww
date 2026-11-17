#!/usr/bin/env python3
"""Test the two shipped mate-safety options, and confirm the defects on the PRISTINE build.

Three questions, each of which decides how a defect may be reported:

1. **Does the defect reproduce on the audit base?** `build/clean/forge` is the
   unmodified source. If the probe build shows a defect the clean build does not,
   the probe caused it and the finding is about my instrument, not the engine.

2. **What do `SoundMatePruning` and `MateAlphaGuard` actually do?** Read from
   source, then measured:
     * `SoundMatePruning` switches OFF the whole shallow move-loop pruning block
       at three node classes: PV nodes, in-check nodes, and nodes whose alpha is
       already a mate score. It has no effect on null move, razoring, RFP or LMR,
       which are separate predicates gated only on `mate_moves_`/depth.
     * `MateAlphaGuard` only exists in a build with `-DFORGE_MATE_ALPHA_GUARD=1`,
       and then only adds `!is_mate_score(alpha)` to the quiet-futility and
       capture-futility arms INSIDE that same block. It is therefore a strict
       subset of `SoundMatePruning`'s mate-alpha arm. It is NOT in the audit base
       (the option is absent from `uci` output on a base build) -- a fact the
       findings doc records as the `FORGE_MATE_ALPHA_GUARD` trap.

3. **Does turning them on change any mate verdict on the corpus?** Measured, not
   argued, at the same depths as the main run.
"""

from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "scripts")
from ucidrv import Engine, check_fen  # noqa: E402


def run(engine: Engine, fen: str, depth: int, options: dict[str, str]) -> dict:
    engine.newgame()
    # Reset EVERY option this script touches, then apply the arm's settings.
    # Without the reset, an arm's `SoundMatePruning=true` persists into the next
    # row's `default` arm. That bug made this harness report 9 rows where "the
    # probe build" disagreed with the clean build, and a direct A/B of the two
    # binaries proved them identical -- the disagreement was the leak, not the
    # engine.
    for k in ("SoundMatePruning", "MateAlphaGuard"):
        engine.setoption(k, "false")
    for k, v in options.items():
        engine.setoption(k, v)
    check_fen(engine, fen)
    res = engine.go(f"depth {depth}")
    last = res.last
    return {
        "bestmove": res.bestmove,
        "score_mate": last.score_mate if last else None,
        "score_cp": last.score_cp if last else None,
        "nodes": res.nodes,
        "pv": last.pv if last else [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="corpus/mates.json")
    ap.add_argument("--depths", default="8,10,12")
    ap.add_argument("--out", default="evidence/options.json")
    args = ap.parse_args()

    depths = [int(d) for d in args.depths.split(",")]
    with open(args.corpus) as fh:
        entries = json.load(fh)["entries"]

    arms = [
        ("default", {}),
        ("SoundMatePruning=true", {"SoundMatePruning": "true"}),
    ]

    out: dict = {"arms": [a[0] for a in arms], "rows": [], "option_surface": {}}

    # Record what each build actually advertises, so "MateAlphaGuard absent on
    # the base" is a measured statement rather than a remembered one.
    for label, path in (("clean", "build/clean/forge"), ("probe", "build/probe/forge")):
        e = Engine(path, {"Threads": "1"})
        e.send("uci")
        lines = e._read_until(lambda l: l.strip() == "uciok")
        opts = [l.split("name", 1)[1].split("type")[0].strip()
                for l in lines if l.startswith("option name")]
        out["option_surface"][label] = {
            "has_SoundMatePruning": "SoundMatePruning" in opts,
            "has_MateAlphaGuard": "MateAlphaGuard" in opts,
        }
        e.close()

    engine = Engine("build/probe/forge", {"Threads": "1", "Hash": "64", "OwnBook": "false"})
    clean = Engine("build/clean/forge", {"Threads": "1", "Hash": "64", "OwnBook": "false"})
    try:
        for entry in entries:
            fen = entry["fen"]
            mating = {m["uci"] for m in entry["mating_moves"]}
            want = entry["moves_to_mate"]
            for depth in depths:
                row = {"fen": fen, "depth": depth, "true_moves": want,
                       "mating_moves": sorted(mating), "arms": {}}
                for name, opts in arms:
                    r = run(engine, fen, depth, opts)
                    r["correct"] = r["bestmove"] in mating and r["score_mate"] == want
                    r["move_ok"] = r["bestmove"] in mating
                    r["dist_ok"] = r["score_mate"] == want
                    row["arms"][name] = r
                # pristine build, same depth
                rb = run(clean, fen, depth, {})
                rb["correct"] = rb["bestmove"] in mating and rb["score_mate"] == want
                rb["move_ok"] = rb["bestmove"] in mating
                rb["dist_ok"] = rb["score_mate"] == want
                row["arms"]["clean-base"] = rb
                out["rows"].append(row)
            print(f"{fen[:44]} done", flush=True)
    finally:
        engine.close()
        clean.close()

    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=1)

    # Summary: disagreements between arms and against the base.
    summary = {}
    for name in [a[0] for a in arms] + ["clean-base"]:
        summary[name] = sum(1 for r in out["rows"] if not r["arms"][name]["correct"])
    smp_diff = [r for r in out["rows"]
                if r["arms"]["SoundMatePruning=true"]["correct"] != r["arms"]["default"]["correct"]]
    probe_vs_clean = [r for r in out["rows"]
                      if r["arms"]["default"]["correct"] != r["arms"]["clean-base"]["correct"]]
    print(json.dumps({
        "option_surface": out["option_surface"],
        "incorrect_rows_by_arm": summary,
        "rows_where_SoundMatePruning_changed_verdict": len(smp_diff),
        "rows_where_probe_and_clean_disagree": len(probe_vs_clean),
        "smp_examples": [{k: r["arms"][k] for k in ("default", "SoundMatePruning=true")} |
                         {"fen": r["fen"], "depth": r["depth"]} for r in smp_diff[:6]],
        "probe_vs_clean_examples": [{"fen": r["fen"], "depth": r["depth"],
                                     "probe": r["arms"]["default"], "clean": r["arms"]["clean-base"]}
                                    for r in probe_vs_clean[:6]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
