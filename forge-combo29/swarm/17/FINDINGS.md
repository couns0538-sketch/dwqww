# FINDINGS - seat 17 (area 7, reading the code for faults)

One line per finding, only ever added. A check of another seat's finding is its own line.

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-F1 | 7 | `go depth N searchmoves <name with no legal root move>` answers `bestmove 0000` on a position that HAS legal moves (startpos: 20 legal, 0000 returned) - UCI defines 0000 as "no legal move exists", so a GUI reads it as an illegal move | `forge-combo29/swarm/17/job1/finding_searchmoves.py` (run: `cd forge-combo29/swarm/17/job1 && python3 finding_searchmoves.py /agent/repos/base/forge-combo29/build/forge sm`) | NEW |
| S-F2 | 7 | WITHDRAWN - my stated SOURCE for S-F1 was wrong. I claimed `src/search.cpp:2640` reads `front()` of an empty MoveList; it does not, because every empty-`root_candidates` path returns at the early block on line 2253. The OBSERVABLE S-F1 (`bestmove 0000` with 20 legal moves) stands and is still mine; the mechanism I gave for it does not | refuted by my own marker test, `forge-combo29/swarm/17/job1/reach_check/flow.json` (`EARLY_PATH cand=0 ... legal=20` and no `PAST_EARLY` for every searchmoves case) | WITHDRAWN (source only) |

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

## Correction of my own S-F2 (2026-11-16T21:42Z), after reading seat 07's 07-R1

Seat 07's 07-R1 says my S-F2 source claim is wrong; it is, and I checked it myself rather than
taking it on trust. Scratch copy of 6b98f217 with marker prints (`/tmp/reach17`, not committed):
- `go depth 5 searchmoves e7e5` on startpos: `EARLY_PATH cand=0 drawn=0 legal=20`, and NO `PAST_EARLY`.
- `go depth 5 searchmoves zzzz`: same.
- `go depth 5 searchmoves e2e4`: no `EARLY_PATH`, `PAST_EARLY cand=1`.
- `go depth 6` startpos: `PAST_EARLY cand=20`.
- checkmated root: `EARLY_PATH cand=0 ... legal=0`.
So the empty-candidate case always leaves through line 2253; line 2640 never sees an empty list.
My first marker attempt was worthless (I instrumented a statement guarded by `is_none()`, so it
could not fire even on the normal path and proved nothing) - replaced by the control-flow markers
above. The observable S-F1 answer stays: `bestmove 0000` is returned while `legal=20`.
| S-C1 | CONFIRMS 07-R1 | seat 07 is right that search.cpp:2640 is not an empty-container read; my own marker test shows every empty-root_candidates search leaves at the 2253 early block (`EARLY_PATH cand=0 drawn=0 legal=20`, no `PAST_EARLY`) | `forge-combo29/swarm/17/job1/reach_check/flow.json` | CONFIRMS |
| S-C2 | CONFIRMS 07-F1 | reproduced on my build with my own driver: the five info lines are literally `score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` (empty pv) and the answer is `bestmove 0000`, while python-chess says the root has 20 legal moves; 07's extra claim (unsearched roots presented as a 0-node draw) is exactly what the raw lines show | `forge-combo29/swarm/17/job1/reach_check/case07f1.log` (driver: job1/uci_driver.py) | CONFIRMS |
| S-C3 | 07-F1 vs my S-F1 | note, not a refutation: S-F1 and 07-F1 describe the same engine behaviour from two seats. 07-F1 adds the `score cp 0 nodes 0` presentation and the `restricted_root_empty` plumbing detail; my S-F1 is the `bestmove 0000`-on-a-live-position statement. Neither supersedes the other | both command files | OVERLAP |
| S-C4 | CONFIRMS 27-F2 | exact threshold reproduced on my build at startpos: `go nodes` 1/5/10/20/25 answer `bestmove a2a3` with ZERO info depth lines; 26 answers `d2d4` with `info depth 1 ... nodes 26 ... pv d2d4`; the boundary is 26 as seat 27 said (not a range) | `forge-combo29/swarm/17/job1/check27/nodes.json` + `job1/check27/nodes_*.log` | CONFIRMS |
| S-C5 | CONFIRMS 27-F4, weaker rate | same effect, my numbers: on 8 G positions at depth 10 (S14 not applied), a fresh process vs the same process after `setoption name Clear Hash` gives the same bestmove for 7 and a DIFFERENT bestmove for 1 (index 7: `g5h5` fresh vs `g5h6` after Clear Hash). So the histories do survive Clear Hash as 27-F4 says; my changed-rate is 1/8, not their 9/20, because my sample, depth and position set differ | `forge-combo29/swarm/17/job1/check27clear/clear_hash.json` | CONFIRMS (rate differs) |
| S-C6 | STRENGTHENS 27-F4 | on 20 G positions at depth 10, `setoption name Clear Hash` between two searches changes the depth-10 NODE COUNT in 20/20 cases (e.g. 23448 -> 40313, 46317 -> 31393) and the bestmove in 1/20. So the transposition table is cleared but the move-ordering histories are not, exactly as 27-F4 says; node-count drift is the sensitive detector, bestmove the insensitive one | `forge-combo29/swarm/17/job1/check27clear/D_A_*.log`, `D_B_*.log` | CONFIRMS + strengthens |
| S-F3 | 7 | NOT a fault, recorded because it protects the honesty numbers: `bench 13` returns nodes 862329 identically after 0, 1, 2 and 5 preceding depth-6 searches in the same process, so the history drift of 27-F4 / my S-C6 does NOT contaminate the pinned node counts - `bench` resets that state itself. Any harness that compares bench pins across runs is therefore safe from this particular drift | `forge-combo29/swarm/17/job1/bench_repeat/bench_after.json` | NEGATIVE |
| S-F4 | 7 | Methodological trap, not an engine fault: `OwnBook` defaults to TRUE, so any clock or time-management measurement that starts from the initial position is answered by the book in ~0 ms with no `info depth` line. My own first clock run measured nothing this way (5 "results" with 0 depth lines). With `setoption name OwnBook value false` the same searches scale as expected: wtime 1000 -> 55 ms / depth 14, 10000 -> 374 ms / depth 18, 100000 -> 5234 ms / depth 25 | `forge-combo29/swarm/17/job1/clock/clock.json` (0 depth lines, book on) vs `clock/clock_nobook.json` (book off) | NEW (method) |
| S-F5 | 7 | NOT a fault, checked and clean: the one unchecked multiply in the clock plan (`clock_plan.hpp`, `hard = min(available*4/5, soft*4)`) does not overflow under ASan+UBSan even at `wtime 9223372036854775807 movestogo 1`; the search simply runs its (huge) budget with 22 depth lines and no `runtime error` line | `forge-combo29/swarm/17/job1/clock/clock_extreme_nobook.json` | NEGATIVE |
| S-F6 | 7 | NOT a fault, deep-search stack safety on record: under ASan+UBSan, `go nodes 2000000` reaching seldepth 64 in two positions and seldepth 48 on startpos produced 0 sanitizer lines; the two `bestmove 0000` answers in that batch are correct terminal roots (verified with python-chess: one is checkmate, one is STALEMATE with 0 legal moves), i.e. the known case, not a fault | `forge-combo29/swarm/17/job1/maxply/maxply2.json` | NEGATIVE |
