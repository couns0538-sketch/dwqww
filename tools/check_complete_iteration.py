#!/usr/bin/env python3
"""Check actual-UCI completed-iteration preservation, Ponder and restrictions.

The reference must be the frozen guard-OFF lock. Run first with --engine pointing
to that lock for RED, then with the guarded ON candidate for GREEN. Each search
is a fresh process. All original exchanges and result records are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from complete_iteration_probe import capture


POSITION = "fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
LEGAL = {f"{file}2{file}{rank}" for file in "abcdefgh" for rank in "34"} | {
    "b1a3", "b1c3", "g1f3", "g1h3"}
RESTRICTED = ["e2e4", "h2h3", "c2c4", "d2d4"]
TUPLE = ["depth", "score_kind", "score", "pv", "best", "ponder"]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--cpu", type=int, help="optional Linux taskset CPU; omitted by default")
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=False)
    results: dict[str, dict] = {}
    checks: list[dict] = []

    def run(name: str, go: str, reference=False, ponder=False, restricted=False):
        command = go + (" searchmoves " + " ".join(RESTRICTED) if restricted else "")
        value = capture(args.reference if reference else args.engine, POSITION, command,
                        args.outdir / (name + ".raw"), ["Ponder value true"] if ponder else [], args.cpu)
        results[name] = value
        return value

    def check(name: str, okay: bool, **details):
        checks.append({"name": name, "pass": bool(okay), **details})
        print(("PASS " if okay else "FAIL ") + name, flush=True)

    def same_tuple(name: str, actual: dict, reference: dict, same_nodes=False):
        differences = {key: {"expected": reference[key], "actual": actual[key]}
                       for key in TUPLE if actual[key] != reference[key]}
        if same_nodes and actual["nodes"] != reference["nodes"]:
            differences["nodes"] = {"expected": reference["nodes"], "actual": actual["nodes"]}
        check(name, not differences, differences=differences)

    scenarios = [("plain", False, False, 600, 3), ("ponder", True, False, 600, 3),
                 ("restricted-ponder", True, True, 1800, 7)]
    for name, ponder, restricted, budget, completed_depth in scenarios:
        reference = run(name + "-complete-reference", f"depth {completed_depth}", True, ponder, restricted)
        actual = run(name + "-interrupted", f"nodes {budget}", False, ponder, restricted)
        same_tuple(name + " preserves last completed tuple", actual, reference)
        check(name + " reports no unfinished iteration", bool(actual["infos"]) and
              all(info["depth"] <= completed_depth for info in actual["infos"]))
        check(name + " bestmove belongs to legal root restriction",
              actual["best"] in (set(RESTRICTED) if restricted else LEGAL))
        if ponder:
            check(name + " ponder suffix matches completed PV", len(reference["pv"]) >= 2 and
                  actual["best"] == reference["pv"][0] and actual["ponder"] == reference["pv"][1])

        # Node2 completes one root child, but not the depth1 iteration. Prove
        # that trigger on the unmodified lock, then require a legal empty-PV
        # fallback from ON. Searchmoves has four legal alternatives, not one.
        trigger = run(name + "-partial-first-reference", "nodes 2", True, ponder, restricted)
        check(name + " OFF proves nonempty first-iteration partial PV",
              bool(trigger["pv"]) and trigger["depth"] == 1 and
              reference["infos"][0]["depth"] == 1 and reference["infos"][0]["nodes"] > 2)
        fallback = run(name + "-zero-fallback", "nodes 0", False, ponder, restricted)
        first = run(name + "-partial-first", "nodes 2", False, ponder, restricted)
        check(name + " first interrupted iteration keeps legal fallback",
              not first["infos"] and not first["pv"] and first["ponder"] is None and
              first["best"] == fallback["best"] and
              first["best"] in (set(RESTRICTED) if restricted else LEGAL))

    for depth in [4, 10]:
        reference = run(f"full-depth{depth}-reference", f"depth {depth}", True, True)
        actual = run(f"full-depth{depth}", f"depth {depth}", False, True)
        same_tuple(f"completed depth{depth} tuple and nodes unchanged", actual, reference, True)

    record = {"engine": str(args.engine.resolve()), "engine_sha256": sha256(args.engine),
              "reference": str(args.reference.resolve()), "reference_sha256": sha256(args.reference),
              "position": POSITION, "history": [], "cpu": args.cpu,
              "checks": checks, "results": results}
    (args.outdir / "result.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    passed = sum(check["pass"] for check in checks)
    print(f"{passed}/{len(checks)} checks passed", flush=True)
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
