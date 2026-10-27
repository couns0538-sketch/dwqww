# S38: gate speed / time-loss / time-use audit (opus, 2026-10-27)

Sol's spec (inventory `S38`): `gate_time_audit.py` reads a fastchess PGN + log and prints per engine: median nps and
depth by game phase, time used vs allotted (p50/p95/p99/max), share of moves over the increment, TL/illegal/crash
counts; it flags nps asymmetry > 3% or p99 overshoot > 1.5x a reference gate. Pass: the TL count equals fastchess's
own summary on the fixture; per-engine nps matches a hand count on 5 games; read-only. Real-gate results were
UNVERIFIED in the spec (Sol had no PC access); here they were run on copies of 7 PC gates.

## Files
| file | what |
|---|---|
| `forge_sol_S38_gate_time_audit_20261027.py` | the audit tool (stdlib, read-only, deterministic) |
| `make_s38_fixture.py` | deterministic synthetic fastchess fixture (no engine is run) |
| `fixtures/s38_fixture_20261027.tar.gz`, `fixtures/fixture.sha256` | the generated fixture (7 files) and its hashes |
| `sample_reports/` | tool output on the fixture (REF gate, then A with `--ref`): the golden files the tests compare byte for byte |
| `real_run/G*.md`, `real_run/real_reports_json.tar.gz` | tool output on copies of 7 real PC gates (JSON in the archive) |
| `s38_hand_count.sh` | independent awk "hand count" of per-game nps (no code shared with the tool) |
| `s38_compare_result_md.py` | compares the tool with the driver's RESULT.md and GATE_RESULTS.csv |
| `test_gate_time_audit.py` | 17 tests (units + fixture end to end + golden files + hand count + refusal) |
| `mutation_check_s38.py` | planted-bug check: 12 one-line mutants of the tool must each fail the tests |
| `run_s38_evidence.sh` | regenerates every artifact and log |

## Use
```
python -I -B forge_sol_S38_gate_time_audit_20261027.py --pgn G.pgn [--log G.log] [--engine-log engine_io.head.log ...]
       [--ref REF.json] [--per-game-nps 5] [--label X] --out-json X.json --out-md X.md
```
Inputs are opened read-only. Outputs are refused (exit 2) under `C:\Users\Administrator\grok-pc`,
`D:\grok-pc-data\forge_push`, `F:\forge_nnue_train`, `F:\forge_out` or onto an input. Exit 0 clean, 1 flags raised,
3 PGN-vs-log mismatch. Run on copies (cp -p into scratch), as done here.

## What it measures (definitions)
- **Time used** = fastchess's per-move time in the PGN comment (`{eval/depth 0.857s, tl=9.343s}`).
- **Allotted** = the engine's own soft/hard limit, recomputed from the clock before the move with the AL1 lock time
  manager (`src/search.cpp`: avail = remaining - 10 ms; soft = avail/22 + 75% inc; hard = min(60% avail, 5 x soft);
  `--tm` changes it for another engine). The clock before a move is the previous `tl=` of that side, or base + inc for
  its first engine move (fastchess sends `go wtime 10100` at 10+0.1). The chain is checked against fastchess's own
  `tl=` on every move (`clock_accounting`; 0 mismatches > 2 ms on 1,171,301 real moves).
- **nps / phase**: last `info ... nps ... time` line before each `bestmove` in the `-log engine=true` file, searches
  with time >= 100 ms (`--nps-min-ms`, same filter as conc7_watch), phase = ply bands `<40, 40-79, >=80` from the
  `position` command (`--phase-plies`). Depth by phase comes from the PGN.
- **TL / illegal / crash**: PGN `Termination` + reason text, attributed to the losing side; cross-checked against
  fastchess's own `Finished game N (...): RESULT {reason}` lines (what GATE_RESULTS.csv `time_losses` counts).
  fastchess 1.8.2 prints no per-player "Timeouts:" block in these SPRT runs (string exists in fastchess.exe, never
  seen in any PC log), so those per-game lines are "fastchess's own summary".
- **Flags**: `NPS_ASYMMETRY` (median nps max/min - 1 > 3%), `P99_OVERSHOOT` (p99 of used/soft > 1.5 x the same role,
  cand/base, in `--ref`), `CROSS_CHECK_MISMATCH`, `CLOCK_ACCOUNTING`.

## Fixture (no engine games were played)
The spec asks for a fixture from two box engines (<= 50 games). The PC runs conc-8 gates at ~87% CPU; an idle-priority
match still shares SMT cores with gate engines and could lower the gate nps ratio that conc7_watch acts on, so no
engine was run. `make_s38_fixture.py` writes the real fastchess formats instead (PGN with timeleft comments, stdout log,
engine log lines, termination strings taken from fastchess.exe): `s38fx_A` 30 games, single slot, cand nps ~4.5% above
base, cand with a heavy time tail, events cand 2 TL + 1 disconnect, base 1 TL + 1 illegal move, one
`Warning; Illegal PV move` line; `s38fx_REF` 12 clean symmetric games. The generator is deterministic (two runs
byte-identical) and also writes its own truth file (TL counts, every search's final nps).

## Results
- Fixture: TL PGN == fastchess lines == truth (cand 2, base 1); illegal/crash match; median nps == generator truth;
  flags raised: NPS_ASYMMETRY 4.55% and P99_OVERSHOOT cand (2.01 x REF); none for REF; `logs/step1_fixture.log`.
- Hand count: tool `--per-game-nps 5` == `s38_hand_count.sh` (awk) on 10/10 rows for the fixture AND for the real
  G125 `engine_io.head.log` copy (`logs/step3_hand_count.log`).
- Tests 17/17 OK; mutation check 12/12 mutants caught (`logs/step2_unit_tests.log`, `logs/step4_mutation_check.log`).
- Real-file run on copies of G120, G120c, G104, G104c, G124, G124c, G125 (37 files, sha256 equal to the originals):
  TL 0, crash/illegal 0, `Warning;` 0 everywhere, equal to RESULT.md and to GATE_RESULTS.csv (G120/G120c/G104); mean
  PGN depth and move count per engine equal to RESULT.md on all 14 engine rows (e.g. G125 base 21.08 / 97289, cand
  21.26 / 97289). PGN games == fastchess Finished lines on all 7; after an early SPRT stop (G120, G104) the last
  "Results of" block counts one game less (an orphan game still in flight; the block counts complete pairs).
- Real time use is stable: used p50 156-166 ms, p95 602-630 ms, p99 ~1.0 s, max 2.49-2.67 s; used/soft p99 3.85-3.99
  (0.99-1.02 x G120, no overshoot flag); 0-2 moves per gate over the hard limit by <= 2 ms; 72-76% of moves over
  the increment. The lowest clock is 177-178 ms in every gate: R -> 0.4 R + 106 (hard = 60% of avail, + 100 ms inc) has
  its fixed point at 176.7 ms, so in each gate some game ran several moves at the hard cap; with timemargin=1000 this
  never forfeits, and no game did.
- nps (engine_io.head.log only, i.e. the first ~9 minutes of a gate): G120 asymmetry 0.78%; **G125 3.68% (flag)**:
  cand e48f042 1.836 M vs AL1 base 1.771 M median, higher in all three phases (UNVERIFIED cause; same engine code, so a
  search-shape effect of the net is likely but not shown; no Elo or speed claim).

## Limits / UNVERIFIED
- No fastchess match was run, so the fixture's TL/illegal/disconnect PGN form (Termination + reason on the last
  recorded move) is UNVERIFIED against real fastchess output; none of the 71,103 real PC gate games ended other than
  `normal`, so it cannot be checked on PC data either.
- nps only where an engine log exists; the driver keeps only the head and tail (100 MB each) of engine_io.log; the
  real run used the head of G120 and G125 only.
- The allotment model is the AL1 lock time manager; a candidate with a different time manager or Tm* tune needs `--tm`.
