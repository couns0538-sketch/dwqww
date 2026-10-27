# S38 Gate speed / TL / time-use audit: DONE (opus, 2026-10-27)
Branch opus-sol-S38 (base d4f4312 + 0d99f02), head aa53daf0. Tool job, no engine change; pushes [skip ci], no CI run.

## What was done
- `forge_sol_S38_gate_time_audit_20261027.py` (stdlib, read-only, deterministic) reads a fastchess PGN, the stdout log and the
  `-log engine=true` file(s). Per engine it reports:
  - time used against the engine's own allotment: soft/hard limits recomputed from the clock before each move with the AL1 lock time
    manager (avail = remaining - 10; soft = avail/22 + 75% inc; hard = min(60% avail, 5 x soft)), p50/p95/p99/max;
  - share of moves over the increment; moves over the hard limit; lowest clock; clock accounting checked against fastchess's `tl=`;
  - median depth (PGN) and median nps (last `info` before each `bestmove`, searches >= 100 ms) by ply phase;
  - TL/illegal/crash counts from PGN terminations, cross-checked against fastchess's own `Finished game … {reason}` lines (what
    GATE_RESULTS.csv counts);
  - flags: nps asymmetry > 3%, p99 used/soft > 1.5 x the same role in a `--ref` gate, cross-check or clock mismatches.
- It refuses output under PC gate/queue/lock/training roots or onto an input (exit 2).
- Fixture: `make_s38_fixture.py`, deterministic, real fastchess 1.8.2 formats and termination strings taken from fastchess.exe.
  - s38fx_A: 30 games, single slot, cand nps +4.5%, cand heavy time tail, cand 2 TL + 1 disconnect, base 1 TL + 1 illegal, one `Warning;`.
  - s38fx_REF: 12 clean games.
- Also: `s38_hand_count.sh` (independent awk nps hand count), `s38_compare_result_md.py`, 17 tests, 12-mutant check, sample reports,
  real-run reports, README, IDEA_SOURCE.

## Evidence
| check | command | raw result |
|---|---|---|
| tests | `S38_SCRATCH=F:\opus_scratch\sol_s38\tests_<n> python -I -B test_gate_time_audit.py` | Ran 17, OK (and 17/17 under venv 3.10.22) |
| mutation | `python -I -B mutation_check_s38.py --scratch F:\opus_scratch\sol_s38\mut_<n>` | 12/12 CAUGHT |
| fixture TL vs fastchess | sample_reports/s38fx_A_report.json | tl pgn = log = {base 1, cand 2}, match true; flags NPS_ASYMMETRY 4.55%, P99_OVERSHOOT cand 2.01 x REF; REF: no flags |
| nps hand count | `bash s38_hand_count.sh <engine log> <engine> 5` vs `--per-game-nps 5` | fixture 10/10 identical; real G125 engine_io.head.log 10/10 identical |
| real run | 7 gates copied with cp -p (37 files, sha256 = originals) | all gates equal (see below) |

Real-run details (copies of G120, G120c, G104, G104c, G124, G124c, G125):
- TL 0, crash/illegal 0, `Warning;` 0 everywhere, equal to RESULT.md and GATE_RESULTS.csv.
- Mean depth and moves equal to RESULT.md on all 14 engine rows (e.g. G125 base 21.08/97289, cand 21.26/97289).
- PGN games = Finished lines on all 7. After an early SPRT stop (G120 929 vs 928, G104 699 vs 698), the "Results of" block counts one
  orphan game less.

## Results (real gates)
- Time use is stable on all 7 gates:
  - used p50 156-166 ms, p95 602-630 ms, p99 ~1.0 s, max 2.49-2.67 s;
  - used/soft p99 3.85-3.99 (0.99-1.02 x G120, no overshoot flag);
  - 0-2 moves per gate over the hard limit by <= 2 ms; 72-76% of moves over the increment;
  - 0 clock-accounting mismatches on 1,171,301 moves.
- The lowest clock is 177-178 ms in every gate. That is the fixed point of R -> 0.4 R + 106 (hard limit binding), and it never
  forfeits under timemargin=1000.
- nps: G120 asymmetry 0.78%. **G125 3.68% (flagged)**: cand e48f042 1.836 M vs AL1 base 1.771 M median, higher in all phases.
  Head log only; cause UNVERIFIED; no speed claim.

## Left
- nps for more gates (engine logs are 100 MB head + tail each; only G120/G125 head logs were copied).
- The two-engine fixture, if a quiet machine ever exists.

## UNVERIFIED
- The fixture's TL/illegal/disconnect PGN form: no such real game exists among 71,103 PC gate games.
- No engine games played: deviation from the spec's "two box engines", chosen to avoid disturbing gates.
- Cause of G125's asymmetry.
