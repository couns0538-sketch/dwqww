# S02 check of 08-F2 (seat 08, area 8) — CONFIRMS

Their finding: "`go movetime T` searches for T - Move Overhead, not T: movetime 50 gave a median wall of
40.4 ms (200 searches), movetime 500 gave 490.5 ms, because search.cpp:2191-2193 sets hard = movetime -
overhead with Move Overhead defaulting to 10. A cross-engine "movetime 50" comparison gives Forge 20 % less
time."

## what I ran (my own harness, written from their sentence)
`check_movetime_overhead.py` — reads nothing of theirs; 6 positions x 12 trials = 72 searches per cell,
one engine process per cell, wall time with `time.monotonic()` from writing `go` to reading `bestmove`,
`OwnBook false` so no book answer can slip in.

The point of my check is that their number alone cannot separate two causes:
  (a) the engine really subtracts Move Overhead from movetime, or
  (b) the time manager simply stops ~20 % early for its own reasons.
So I measured each movetime TWICE, at Move Overhead 10 (default) and at Move Overhead 0.

## the table (output of that script, pasted)

```
50_ov10    n=72 median   40.56 ms  mean   40.84  min   40.28  max   57.74
50_ov0     n=72 median   50.69 ms  mean   50.91  min   50.24  max   67.66
200_ov10   n=72 median  190.62 ms  mean  190.85  min  190.18  max  206.98
200_ov0    n=72 median  200.58 ms  mean  200.84  min  200.22  max  217.45
```

| cell | n | median ms | mean ms | gap to the movetime |
|---|---|---|---|---|
| movetime 50, Move Overhead 10 | 72 | 40.56 | 40.84 | 9.44 |
| movetime 50, Move Overhead 0 | 72 | 50.69 | 50.91 | -0.69 |
| movetime 200, Move Overhead 10 | 72 | 190.62 | 190.85 | 9.38 |
| movetime 200, Move Overhead 0 | 72 | 200.58 | 200.84 | -0.58 |

## verdict
CONFIRMS. The gap to the movetime is 9.44 ms at movetime 50 and 9.38 ms at movetime 200 — the SAME
absolute 9.4 ms, not the same fraction (18.9 % vs 4.7 %), and it vanishes (to under 1 ms, i.e. timer
granularity) when Move Overhead is set to 0. That is cause (a) exactly, and it rules out (b): a fixed
fraction of the movetime could not be removed by changing an overhead option.

Their number reproduces too: their median 40.4 ms vs my 40.56 ms at movetime 50 with default overhead.

Code line, verified by opening the file (not taken from their report): /agent/repos/base/forge-combo29/src/search.cpp
```
2185:    const std::int64_t overhead = std::max<std::int64_t>(0, limits.move_overhead_ms);
2192:        hard_limit_ms_ = std::max<std::int64_t>(1, limits.movetime_ms - overhead);
2193:        soft_limit_ms_ = hard_limit_ms_;
```
Their citation "search.cpp:2191-2193" points at the same statement (2191 is the `else if (limits.movetime_ms >= 0)`
line). Correct.

## one thing I would put differently (not a refutation)
They call this a defect ("a cross-engine movetime 50 comparison gives Forge 20 % less time"). The mechanism
is real, but subtracting a move overhead from movetime is a deliberate, common design — it exists so a GUI's
"movetime" does not cause a flag. Whether it is a FAULT depends on the comparison: for a like-for-like match
against another engine at movetime 50 it is a genuine 20 % handicap, and the fix is to send
`setoption name Move Overhead value 0` in such a harness, not to change the engine. I record it as a
correct finding about behaviour with a caveat on the word "fault".

## control (the harness can see a difference)
The Move Overhead 0 cells ARE the control: same script, same positions, same trial count, and the measured
median moves by 10.1 ms / 10.0 ms. A harness that always printed the same number could not do that.

## raw
out/raw_50_ov10.json, out/raw_50_ov0.json, out/raw_200_ov10.json, out/raw_200_ov0.json (each row holds the
engine's full output for that search), out/meta.json (exe path, sha256, options sent, start time), out/table.md.

## times
see the `date -u` lines in the commits; out/meta.json holds `started_utc`.

## integrity re-audit (seat 19's warning, 2026-11-16T21:40Z)

Seat 19 reported a check that printed CONFIRMS while measuring nothing: it grepped engine output for a line
the engine never prints, the parser got nothing, the comparison went NaN, and the NaN passed. Every check of
mine that parses engine output was re-audited against that failure mode.

This check (the only CONFIRMS I have filed) is now guarded, and the guards were PROVEN to fire:

1. every cell must contain the full 72 measurements (`len(walls) != expected` -> exit, no number printed);
2. no measurement may be NaN or infinite -> exit;
3. every search must have produced a `bestmove` line -> exit ("wall time until something else happened"
   is not a latency measurement);
4. the verdict itself re-checks that all four cells exist before printing anything;
5. the CONFIRMS is only printed when five mechanism conditions all hold (gaps 8-12 ms at both movetimes,
   the two gaps within 1.5 ms of each other, and under 2 ms with Move Overhead 0) — the conclusion line is
   printed BY the script that measured the numbers, not typed by me.

Negative control (the guards must fire, and do — output pasted from the run):

```
$ python3 -c 'verdict({"50_ov10": [], ...})'
guard fired as intended -> FAIL verdict: cell 50_ov10 missing; cannot confirm or refute
$ python3 -c 'verdict({"50_ov10": [nan], ...})'
guard fired as intended -> FAIL verdict: a gap is NaN
```

A re-measurement with the guards active reproduces the result (`out_v2/`, a second independent run):

| cell | n | median ms | mean ms | gap to the movetime |
|---|---|---|---|---|
| movetime 50, Move Overhead 10 | 72 | 40.35 | 40.60 | 9.65 |
| movetime 50, Move Overhead 0 | 72 | 50.37 | 50.62 | -0.37 |
| movetime 200, Move Overhead 10 | 72 | 190.61 | 190.83 | 9.39 |
| movetime 200, Move Overhead 0 | 72 | 200.61 | 200.82 | -0.61 |

and its own verdict block:

```
- gap at movetime 50 overhead 10 is 8..12 ms                 PASS
- gap at movetime 200 overhead 10 is 8..12 ms                PASS
- the two gaps differ by under 1.5 ms (absolute, not a fraction) PASS
- overhead 0 gap at movetime 50 is under 2 ms                PASS
- overhead 0 gap at movetime 200 is under 2 ms               PASS
CONCLUSION: CONFIRMS 08-F2
```

What the guard does NOT do, said plainly: it checks that numbers are PRESENT and FINITE, not that they are
honest. A fabricated but self-consistent set would pass it. The defence against that is the raw per-search
files (out/ and out_v2/raw_*.json), each holding the engine's own output for that search.
