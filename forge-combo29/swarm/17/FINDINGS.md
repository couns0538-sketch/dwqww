# FINDINGS - seat 17 (area 7, reading the code for faults)

One line per finding, only ever added. A check of another seat's finding is its own line.

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-F1 | 7 | `go depth N searchmoves <name with no legal root move>` answers `bestmove 0000` on a position that HAS legal moves (startpos: 20 legal, 0000 returned) - UCI defines 0000 as "no legal move exists", so a GUI reads it as an illegal move | `forge-combo29/swarm/17/job1/finding_searchmoves.py` (run: `cd forge-combo29/swarm/17/job1 && python3 finding_searchmoves.py /agent/repos/base/forge-combo29/build/forge sm`) | NEW |
| S-F2 | 7 | source of S-F1: `src/search.cpp:2640` `if (result.best_move.is_none()) result.best_move = root_candidates.front();` reads `front()` of an EMPTY MoveList when `root_candidates` is empty but legal moves exist (line 2210 already detects exactly this state as `restricted_root_empty`) | `sed -n '2202,2211p;2253,2266p;2636,2641p' src/search.cpp` in a 6b98f217 worktree | NEW |

## Harness correction (swarm broadcast, seat 19 finding 19-F12), recorded by seat 17 on 2026-11-16T21:34Z

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-C0 | CONFIRMS 19-F12 | A pipelined `go depth 12` + immediate `quit` answers `bestmove a2a3` with 0 `info` lines, while the same search read to `bestmove` answers `e2e4` at 56,720 nodes; my harness gets the 56,720-node answer, so my results are from a harness of the second kind | `forge-combo29/swarm/17/job1/harness_check.py` (run: `cd forge-combo29/swarm/17/job1 && python3 harness_check.py /agent/repos/base/forge-combo29/build/forge harness_ok`) | CONFIRMS |

### Which of my own recorded results were affected
- INVALID and RE-RUN: `proof_runner.py` pipelined its command list including `quit`, so its first
  "real build, 0 sanitizer lines" run measured a search that never ran (the planted faults were
  unaffected - their hooks fire before the search). The runner now reads to `bestmove`, and the proof
  was re-run at 2026-11-16T21:34Z: real search reaches depth 6 / 1703 nodes / 0 sanitizer lines;
  planted heap over-read 2 lines; planted signed overflow 1 line. Files replaced in `job1/proof/`.
- NOT AFFECTED: `run_asan.py` / `run_asan.sh` always read stdout until `bestmove` before writing
  `quit`; a raw log (`job1/asan_G_1_12/one_1.log`) ends at depth 14 with 131,575 nodes and an `e2e4`-class
  answer, not `a2a3` with 0 nodes.
- NOT AFFECTED: `finding_searchmoves.py` (S-F1/S-F2) uses the same read-to-bestmove driver and its
  `bestmove 0000` answers are accompanied by `info depth 1..5` lines.

## Measurement-integrity audit (seat 19 warning), recorded by seat 17 on 2026-11-16T21:37Z

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-C0b | CONFIRMS 19-F12 (measurement rule) | my own checker had the same defect class: `harness_check.py` defaulted a missing `nodes` field to 0, so an unmeasured run printed "nodes=0" like a measured zero; it now prints `None` and every claim is asserted to rest on lines the engine actually printed | `forge-combo29/swarm/17/job1/harness_check.py` (run: `cd forge-combo29/swarm/17/job1 && python3 harness_check.py /agent/repos/base/forge-combo29/build/forge harness_ok`) | CONFIRMS |

### What changed, and the proof each guard fails when it should
- `run_asan.py`: refuses an exe with no sanitizer symbols (else "0 sanitizer lines" would mean nothing);
  counts `not_measured` (missing bestmove / missing info depth / missing node count) separately from clean
  results; exits non-zero when nothing was measured. Guard shown failing:
  `python3 run_asan.py <release exe> G.epd 1 2 8 /tmp/guard1` -> `FATAL: ... has no __asan_/__ubsan_/__tsan_ symbols`.
- `proof_runner.py`: each case now asserts the evidence it exists to show (real search: >=1 info depth line
  AND a node count; planted cases: >= expected sanitizer lines). Guard shown failing: pointing the planted case
  at an unplanted build gives `FATAL: case planted_heap_overread proves nothing: expected >= 2 sanitizer line(s), saw 0`.
- `harness_check.py`: an empty log raises `FATAL: ... no bestmove line; no info depth line ...`.
- Re-run after the fix (evidence in `job1/proof/` and `job1/harness_ok/`): real search 6 depth lines,
  1703 nodes, 0 sanitizer lines; planted heap over-read 2 lines; planted signed overflow 1 line.
