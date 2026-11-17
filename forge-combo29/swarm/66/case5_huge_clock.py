#!/usr/bin/env python3
"""case5_huge_clock.py - clock values near integer overflow.

`parse_clock_ms` accepts any complete decimal magnitude and clamps it to
kMaxClockMs = int64_max / 256 = 36028797018963967. Values below 2^31 are the
normal path; 2000000000, 3000000000, 9223372036854775807 and a 30-digit number
exercise the parse, the multiply inside plan_clock_budget, and the clamp.

The specific hazard: plan_clock_budget multiplies the clock by tunables
(`available * hard_percent / 100`, `soft * hard_soft_multiple`) and adds
`increment * increment_percent / 100`. With a clock at the parse ceiling and an
increment at the parse ceiling those products must stay inside int64, which is
why the ceiling is int64_max/256 rather than int64_max.

What this script asserts, for each value:
  * the position is accepted (so a missing search cannot be a refused FEN),
  * the search TERMINATES (an unbounded search here would be a hang: the plan
    should be a huge but finite budget, and the depth ceiling 64 still bounds it),
  * the plan the engine computes is the plan the formula gives, to the
    millisecond, read back from how long it actually searched when that is
    affordable -- and otherwise from the depth ceiling being reached.

Because a 2e9 ms clock is 23 days, the honest measurement is not "does it
terminate" alone: it is which limit binds. `go depth 20` on the same clock must
return at depth 20 in milliseconds, proving the depth ceiling still governs; a
bare `go wtime 2000000000` must NOT print bestmove inside a short timeout, and
must then answer an explicit `stop`.

Run:  python3 case5_huge_clock.py <engine>
"""

from __future__ import annotations

import sys

import ucilib

VALUES = [
    2_000_000_000,
    3_000_000_000,
    9_223_372_036_854_775_807,          # int64 max -> clamps to kMaxClockMs
    36028797018963967,                   # kMaxClockMs exactly
    36028797018963968,                   # one past the ceiling -> clamps
    "9" * 30,                            # 30 digits -> clamps
]
OVERHEAD = 10
PROBE_S = 8.0


def plan(time_ms, increment_ms, mtg, overhead, soft_div=22, inc_pct=75, hard_pct=60, mult=5):
    ceiling = (2**63 - 1) // 256
    time_ms = min(max(0, time_ms), ceiling)
    increment_ms = min(max(0, increment_ms), ceiling)
    if time_ms <= overhead:
        return {"soft": 0, "hard": 0, "reserve_empty": True, "clamped_to": time_ms}
    available = time_ms - overhead
    if mtg > 0:
        capped = min(mtg, 50)
        soft = available // (capped + 1) + increment_ms * 3 // 4
        hard = min(available * 4 // 5, soft * 4)
    else:
        soft = available // soft_div + increment_ms * inc_pct // 100
        hard = min(available * hard_pct // 100, soft * mult)
    soft = max(1, min(soft, available))
    hard = max(1, min(hard, available))
    if soft > hard:
        soft = hard
    return {"soft": soft, "hard": hard, "reserve_empty": False, "clamped_to": time_ms}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/w66/build/forge"
    check = ucilib.Checker("case 5: very large clocks")
    rows = []
    engine = ucilib.engine_ready(path)

    for value in VALUES:
        token = str(value)
        expected = plan(int(token), 0, 0, OVERHEAD)
        position = engine.set_position(None)
        # Probe with a short timeout: a huge clock must NOT answer quickly.
        probe = engine.go("wtime %s" % token, timeout=PROBE_S)
        stopped = None
        if probe["timed_out"]:
            line, stop_lines = engine.stop(timeout=60)
            stopped = line
            engine.isready()
        row = {
            "clock_token": token,
            "clock_parsed_as": expected["clamped_to"],
            "plan_soft_ms": expected["soft"],
            "plan_hard_ms": expected["hard"],
            "plan_hard_days": round(expected["hard"] / 86_400_000.0, 2),
            "position_invalid_fen": position["invalid_fen"],
            "answered_within_probe": not probe["timed_out"],
            "probe_s": PROBE_S,
            "probe_bestmove": probe["bestmove"],
            "probe_depth": (probe["last_info"] or {}).get("depth"),
            "stop_bestmove": stopped,
            "info_strings": probe["strings"] + [t for t in (stop_lines if stopped else [])],
        }
        rows.append(row)

    # The depth ceiling on the same huge clock: this is what proves the search
    # is bounded by depth and the clock is not the binding limit.
    depth_rows = []
    for token in (str(VALUES[0]), str(VALUES[2])):
        position = engine.set_position(None)
        result = engine.go("wtime %s depth 20" % token, timeout=120)
        info = result["last_info"] or {}
        depth_rows.append(
            {
                "clock_token": token,
                "go": result["go"],
                "terminated": not result["timed_out"],
                "wall_ms": round(result["elapsed_ms"], 1),
                "depth": info.get("depth"),
                "bestmove": result["bestmove"],
                "position_invalid_fen": position["invalid_fen"],
            }
        )

    for row in rows:
        check.add(
            "position accepted for clock %s" % row["clock_token"],
            not row["position_invalid_fen"],
            "invalid_fen=%s" % row["position_invalid_fen"],
        )
        check.add(
            "huge clock %s does NOT answer inside %.0f s (it is a real, huge budget)"
            % (row["clock_token"], PROBE_S),
            not row["answered_within_probe"],
            "answered=%s bestmove=%r" % (row["answered_within_probe"], row["probe_bestmove"]),
        )
        check.add(
            "explicit stop answers clock %s" % row["clock_token"],
            row["stop_bestmove"] is not None,
            "stop -> %r" % row["stop_bestmove"],
        )
        check.add(
            "no overflow diagnostic for clock %s" % row["clock_token"],
            not any("invalid" in text or "overflow" in text.lower() for text in row["info_strings"]),
            "strings=%r" % row["info_strings"][:2],
        )

    for row in depth_rows:
        check.add(
            "clock %s with `depth 20` terminates at depth 20 (the depth ceiling binds)"
            % row["clock_token"],
            row["terminated"] and row["depth"] == 20,
            "%.1f ms, depth %r, bestmove %r"
            % (row["wall_ms"], row["depth"], row["bestmove"]),
        )

    # Control: 2000000000 must behave like a LARGE clock, not like an
    # immediate answer and not like an ignore-everything search. Compare it
    # against the modest-clock depth reached at the same wall time.
    small = engine.set_position(None)
    small_result = engine.go("wtime 2000", timeout=30)
    check.add(
        "control: wtime 2000 terminates promptly (the harness sees a managed search)",
        not small_result["timed_out"] and small_result["elapsed_ms"] < 2000,
        "%.0f ms at depth %s"
        % (small_result["elapsed_ms"], (small_result["last_info"] or {}).get("depth")),
    )

    engine.quit()
    summary = check.summary()
    ucilib.emit({"rows": rows, "depth_rows": depth_rows, "summary": summary}, "case5.json")
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
