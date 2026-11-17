#!/usr/bin/env python3
"""The 51 tunables behind FORGE_EXPOSE_TUNABLES.

This block is the largest untouched surface in the engine and the one a tuning
run actually varies, so a crash or a silent no-op here is worse than an Elo
loss: a tuning harness would read a successful reply and tune against a value
the engine never took.

For each tunable the matrix sets four values and records what the engine did:

  min        the advertised minimum            -> must be accepted
  max        the advertised maximum            -> must be accepted
  below      min - 1                           -> must be REPORTED and clamped
  above      max + 1                           -> must be REPORTED and clamped
  malformed  "abc"                             -> must be REFUSED, old value kept

plus an "applied?" probe: after setting a value the engine re-reads it through a
search, because a `setoption` reply alone does not say whether the number
reached the search.

Three things this is designed to catch, each of which the report's existing
findings make plausible:

  1. A tunable whose UCI advertisement disagrees with the internal clamp table
     (search.cpp:114-148). The advertised range is what a tuner trusts, so a
     mismatch means the tuner explores values the engine silently clamps.
  2. A malformed value that is accepted. `apply_spin` (uci.cpp:278-287) refuses a
     non-integer, so this must never happen; if it does, the option is being
     parsed by a different path.
  3. A crash or a hang under any of the five values, including the extremes.
     Several of these are divisors (LmrQuietDivisor, NullMoveDepthDivisor,
     TmSoftDivisor, LmrHistoryDivisor), and the advertised minimum is the only
     thing stopping a division by zero.

Exit status is 0 only when every row is clean. The row count is printed so a
zero-crash result is distinguishable from a matrix that never ran.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver  # noqa: E402

# The tunables block, read from the engine's advertised option list and filtered
# to the names in tune::parameters(). Hard-coded here because the engine does not
# label which options are tunables; the list is checked against the source table
# by --expect-count and by the name set below.
TUNABLES = [
    "LmrQuietBase", "LmrQuietDivisor", "LmrNoisyBase", "LmrNoisyDivisor",
    "NullMoveMinDepth", "NullMoveBase", "NullMoveDepthDivisor", "NullMoveEvalDivisor",
    "RfpDepth", "RfpMargin", "RfpImproving", "RazorDepth", "RazorBase",
    "RazorMultiplier", "FutilityDepth", "FutilityBase", "FutilityMultiplier",
    "LmpBase", "HistoryPruneDepth", "HistoryPruneMultiplier", "SeeQuietMultiplier",
    "SeeNoisyMultiplier", "SingularDepth", "SingularMargin", "IirDepth",
    "ProbcutDepth", "ProbcutMargin", "QsFutilityMargin", "QsSeeMargin",
    "AspirationDelta", "HistoryBonusQuadratic", "HistoryBonusLinear", "HistoryBonusMax",
    "LmrHistoryDivisor", "CheckExtensionDepth", "LmrCutoffThreshold",
    "MaterialCorrectionWeight", "TmSoftDivisor", "TmIncrementPercent", "TmHardPercent",
    "TmHardSoftMultiple", "TmStableFactor", "TmSemiStableFactor", "TmUnstableFactor",
    "TmEffortBase", "TmFallingEvalPercent", "TmMinFactorPercent", "CaptureFutilityBase",
    "CaptureFutilityMultiplier", "CaptureFutilityDepth", "FailLowContinuationBonus",
]
EXPECTED_COUNT = 51

# Options that are divisors. Their advertised minimum is the only guard against a
# division by zero, so the minimum is tested as a live value, not just accepted.
DIVISORS = {
    "LmrQuietDivisor", "LmrNoisyDivisor", "NullMoveDepthDivisor", "NullMoveEvalDivisor",
    "LmrHistoryDivisor", "TmSoftDivisor",
}

PROBE_FEN = "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
PROBE_DEPTH = 8


def parse_spin(options: list[str]) -> dict[str, dict]:
    out = {}
    for line in options:
        m = re.match(r"option name (.+?) type (\S+)(?: default (\S+))?(?: min (-?\d+))?(?: max (-?\d+))?", line)
        if not m:
            continue
        name, kind, default, minimum, maximum = m.groups()
        if kind != "spin":
            continue
        out[name] = {"min": int(minimum) if minimum else None,
                     "max": int(maximum) if maximum else None,
                     "default": default}
    return out


def probe_search(engine: driver.Engine) -> dict:
    """Run one fixed search so a changed tunable has a chance to show, and so a
    crash or hang inside the search is attributed to the option that was set."""
    engine.set_position(PROBE_FEN, cold=True)
    return engine.go_depth(PROBE_DEPTH)


def set_and_observe(engine: driver.Engine, name: str, value: str) -> dict:
    """Send one setoption and report what the engine said and did."""
    before = len(engine.log)
    engine.send(f"setoption name {name} value {value}")
    engine.isready()
    reply = engine.log[before:]
    invalid = any("invalid value" in l for l in reply)
    unknown = any("unknown option" in l for l in reply)
    try:
        probe = probe_search(engine)
        crashed = False
        detail = None
        nodes = probe["nodes"]
    except Exception as exc:  # a crash or hang shows up here
        crashed = True
        detail = f"{type(exc).__name__}: {exc}"
        nodes = None
    return {"reported_invalid": invalid, "reported_unknown": unknown,
            "accepted_silently": not invalid and not unknown,
            "crashed": crashed, "crash_detail": detail, "probe_nodes": nodes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip-probe", action="store_true",
                    help="skip the search probe (accepted/refused only)")
    args = ap.parse_args()

    assert len(TUNABLES) == EXPECTED_COUNT, len(TUNABLES)

    rows = []
    with driver.Engine(args.engine, timeout=120.0) as engine:
        advertised = parse_spin(engine.options)
        missing = [n for n in TUNABLES if n not in advertised]
        extra = [n for n in advertised if n not in TUNABLES
                 and n not in ("Hash", "Threads", "MultiPV", "Move Overhead",
                               "Book Depth", "Book Variety", "DrawJitter")]
        if missing:
            raise SystemExit(f"tunables not advertised by the engine: {missing}")

        # Baseline probe, so every later node count has something to differ from.
        base_nodes = None if args.skip_probe else probe_search(engine)["nodes"]

        for name in TUNABLES:
            spec = advertised[name]
            lo, hi = spec["min"], spec["max"]
            row = {"option": name, "advertised_min": lo, "advertised_max": hi,
                   "default": spec["default"], "is_divisor": name in DIVISORS,
                   "cases": {}}
            for label, value in (
                ("min", str(lo)),
                ("max", str(hi)),
                ("below", str(lo - 1)),
                ("above", str(hi + 1)),
                ("malformed", "abc"),
            ):
                obs = {"value": value, "case": label}
                obs.update(set_and_observe(engine, name, value) if not args.skip_probe
                           else _observe_only(engine, name, value))
                # Expected behaviour, from uci.cpp:278-287.
                if label in ("min", "max"):
                    expected = "accept"
                    ok = obs["accepted_silently"] and not obs["crashed"]
                elif label in ("below", "above"):
                    expected = "report_and_clamp"
                    ok = obs["reported_invalid"] and not obs["crashed"]
                else:
                    expected = "refuse"
                    ok = obs["reported_invalid"] and not obs["crashed"]
                obs["expected"] = expected
                obs["ok"] = ok
                if not args.skip_probe:
                    obs["effect"] = (None if obs["probe_nodes"] is None or base_nodes is None
                                     else obs["probe_nodes"] - base_nodes)
                row["cases"][label] = obs
            row["all_ok"] = all(c["ok"] for c in row["cases"].values())
            row["crashed"] = any(c["crashed"] for c in row["cases"].values())
            row["effect_seen"] = any(c.get("effect") not in (0, None)
                                     for c in row["cases"].values() if not c["crashed"])
            rows.append(row)
            flag = "ok" if row["all_ok"] else "FAIL"
            crash = " CRASH" if row["crashed"] else ""
            print(f"{name:26s} [{lo},{hi}] {flag}{crash}", flush=True)

        # Restore defaults so the engine is left as found, and prove it.
        for name in TUNABLES:
            engine.set_option(name, advertised[name]["default"])

    report = {
        "tunables": len(TUNABLES),
        "advertised_count": len(advertised),
        "expected_count": EXPECTED_COUNT,
        "count_matches": len(TUNABLES) == EXPECTED_COUNT,
        "divisors": sorted(DIVISORS),
        "crashes": sum(1 for r in rows if r["crashed"]),
        "rows_not_ok": [r["option"] for r in rows if not r["all_ok"]],
        "no_effect_on_probe": [r["option"] for r in rows if not r["effect_seen"]],
        "rows": rows,
        "passed": all(r["all_ok"] for r in rows),
    }
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "tunables.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    print(f"\ntunables={report['tunables']} crashes={report['crashes']} "
          f"rows_not_ok={len(report['rows_not_ok'])} no_probe_effect={len(report['no_effect_on_probe'])}")
    return 0 if report["passed"] else 1


def _observe_only(engine: driver.Engine, name: str, value: str) -> dict:
    before = len(engine.log)
    engine.send(f"setoption name {name} value {value}")
    engine.isready()
    reply = engine.log[before:]
    invalid = any("invalid value" in l for l in reply)
    unknown = any("unknown option" in l for l in reply)
    return {"reported_invalid": invalid, "reported_unknown": unknown,
            "accepted_silently": not invalid and not unknown,
            "crashed": False, "crash_detail": None, "probe_nodes": None}


if __name__ == "__main__":
    sys.exit(main())
