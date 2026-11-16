## 2026-11-16T21:07Z (block 1)

- seat: 17
- branch: for-fable-and-opus/swarm-17
- area: 7 (READING THE CODE for faults)
- seed: 1701

Done: STEP 1 seat claimed (SEAT.txt pushed), repository check passed (couns0538-sketch/dwqww).
Running: STEP 2 engine build at 6b98f217 in ../base worktree.
Next: release build, then the honesty check (bench 11/13/16, go perft 5).

## 2026-11-16T21:34Z (block 4)

seat 17 | area 7 (READING THE CODE for faults) | branch for-fable-and-opus/swarm-17 | seed 1701

DONE
- STEP 1 seat, STEP 2 build + honesty (all four pins match: 312866 / 862329 / 3024920 / 4865609).
- ASan+UBSan builds of engine + planted-fault copies; sanitizer proof both ways (planted heap over-read
  2 lines, planted signed overflow 1 line, both counted by the SAME runner; real build 0 lines).
- valgrind memcheck harness (portable build; AVX-512 exe cannot run under valgrind).
- S-F1 / S-F2: `go ... searchmoves <no legal match>` answers `bestmove 0000` on a position with legal
  moves; source `src/search.cpp:2640` reads `front()` of an empty MoveList.
- Harness check vs broadcast 19-F12: CONFIRMED on my engine; the one pipelined runner I had
  (proof_runner.py) was fixed, its proof re-run, FINDINGS records which results were affected.

RUNNING
- 218-legal-move position under release + ASan (perft 1 and depth 6): checks the unclamped
  `root_effort_moves_[256]` / `assert`-compiled-out suspicion. Not finished yet.

NEXT COMMAND
cd /agent/repos/dwqww/forge-combo29/swarm/17/job1 && python3 run_asan.py /agent/repos/base/forge-combo29/build-asan/forge G.epd 21 20 16 asan_G_21_40
## 2026-11-16T21:43Z (block 5) — checkpoint push

seat 17 | area 7 (READING THE CODE for faults) | branch for-fable-and-opus/swarm-17 | seed 1701

DONE (all pushed)
- Step 1 seat, Step 2 build + honesty: 312866 / 862329 / 3024920 / 4865609 all match.
- Sanitizer proofs with planted faults, re-run through a de-pipelined runner after 19-F12.
- Measurement-integrity audit after the seat 19 warning: three guards added and each shown failing.
- ASan+UBSan sweeps: G 1-12 depth 14, G 21-40 depth 16, and MultiPV 3 / MultiPV 8 / mate 2 / Threads 4
  (24 searches). Every search measured (not_measured 0), 0 sanitizer lines in all of them.
- Checks of other seats: S-C0 (CONFIRMS 19-F12), S-C1 (CONFIRMS 07-R1), S-C2 (CONFIRMS 07-F1),
  S-C4 (CONFIRMS 27-F2), S-C5/S-C6 (CONFIRMS + strengthens 27-F4).
- Own findings: S-F1 (`bestmove 0000` on a position with 20 legal moves); S-F2 WITHDRAWN (my stated
  source was wrong - line 2640 is unreachable with an empty list, proved with control-flow markers);
  S-F3 negative control (bench 13 pin is immune to the history drift).

RUNNING
- max_moves.py: the 218-legal-move record position under release+ASan. Slow; time-boxed, may be abandoned.

NEXT COMMAND
cd /agent/repos/dwqww/forge-combo29/swarm/17/job1 && python3 run_asan.py /agent/repos/base/forge-combo29/build-asan/forge G.epd 41 20 16 asan_G_41_60
## 2026-11-16T21:57Z (block 6)

seat 17 | area 7 | branch for-fable-and-opus/swarm-17 | seed 1701

DONE since block 5
- REPORT_job1.md pushed; job 2 (move picker + histories) done, REPORT_job2.md pushed with it.
- NEW: S-F7 (history tunables at both advertised extremes under ASan: 0 lines, 40x node spread proves applied),
  S-F8 (no-legal-match searchmoves ignores node/movetime budgets: 64 depth lines all nodes 0), S-F4 (OwnBook
  default true voided my first clock run - methodological trap), S-F3/S-F5/S-F6 negatives.
- CONFIRMS: 10 (warm/cold rule, all four parts reproduced exactly), 07-R1, 07-F1, 27-F2, 27-F4 (re-labelled),
  19-F12. My own S-F2 WITHDRAWN (my source attribution was wrong; the observable S-F1 stands).

CORRECTION on record
- After seat 10's rule: my S-C6 baseline was a fresh process vs a post-Clear-Hash search, which conflates warm
  drift with a TT clear. FINDINGS now says so and keeps only the narrower surviving claim (hashfull -> 0, so
  the residual drift is the histories). All my ASan sweeps are one-search-per-process, so they are unaffected.

NEXT
- Check remaining seat findings; finish area 7 job 3 (transposition table) as far as time allows.
## 2026-11-16T22:05Z (block 7) — checkpoint

seat 17 | area 7 | branch for-fable-and-opus/swarm-17 | seed 1701

DONE since block 6
- NOTE_select_readline_artifact.md: standalone note on the select+readline artefact (failure signature,
  the rule for harness authors, both working patterns, evidence table).
- S-F8 follow-up, corrected: the no-legal-match searchmoves root does NOT hang and is NOT unbounded -
  bestmove 0000 in 18-19 ms on both `go movetime 100` and `go wtime 1000 btime 1000`, confirmed 3 ways
  including a plain shell pipe. What survives is narrower: 64 info depth lines all reporting nodes 0 time 0,
  i.e. a search report for a search that never ran. S-F11 records the harness root cause.
- S-C9 CONFIRMS 21-F2 (refused FEN still answers readyok, old board stays), S-C10 CONFIRMS 21-F8
  (fullmove 0 refused while python-chess accepts it: 5 legal moves -> engine plays the old board with 20).
- ASan sweep G 61-90 depth 14: 30 measured, 0 sanitizer lines. Running total 106 measured ASan searches.
- TT resize verified (S-F9): Hash 1/8/32/512/2048 -> hashfull 440/58/10/0/0, nodes converge, same bestmove.

NEXT
- Final STATUS + FINDINGS push at 22:30, then stop. Area 7 job 3 report if time remains.
## 2026-11-16T22:10Z (block 8) — FINAL

seat 17 | area 7 (READING THE CODE for faults) | branch for-fable-and-opus/swarm-17 | seed 1701

FINAL STATE — everything is pushed. Stopping here per the 22:30 deadline.

Deliverables in this folder
- HONESTY.txt (+ honesty/): all four pins match (312866 / 862329 / 3024920 / 4865609).
- REPORT_job1.md, REPORT_job2.md, REPORT_job3.md (each: asked / answer / how sure, honesty numbers,
  step table, findings with a re-run command, suspicions separate, what I did not do, uncertainties, times).
- NOTE_select_readline_artifact.md: standalone note on the select+readline artefact with the one-line rule.
- FINDINGS.md: 12 lines of my own (S-F*) and 12 checks of other seats (S-C*).

Findings of my own still standing
- S-F1  `bestmove 0000` returned on a position with 20 legal moves (no legal `searchmoves` match).
- S-F4  `OwnBook` defaults TRUE, so clock measurements from the initial position measure nothing.
- S-F7  history/LMR tunables at both advertised extremes: 0 sanitizer lines, 40x node spread proves applied.
- S-F8  no-match `searchmoves` prints 64 depth lines of `nodes 0 time 0` - a search report for a search that
        never ran. NOT a hang and NOT unbounded (bestmove 0000 in 18-19 ms; my first harness was wrong).
- S-F11 the select()+buffered readline() artefact that produced that wrong first answer.
- S-F3/S-F5/S-F6/S-F9 negatives; S-F2 WITHDRAWN by me (wrong source attribution).

Best result of the session (a check, not my own finding)
- S-C12: independently confirmed and severity-assessed seat 21's 21-F9 - at halfmove 100 the engine returns
  `f2f3` with `cp 0 nodes 0` and MISSES a mate in 1 that it finds at halfmove 99. Mechanism at
  src/search.cpp:2251 (>= 100 treated as a drawn root, no claim modelled, no search performed).

Measurement totals
- 106 measured ASan+UBSan searches, 0 sanitizer lines, every one asserted to have actually searched.
- Sanitizer proof both ways with planted faults, counted by the same runner.

NEXT COMMAND (if resumed)
cd /agent/repos/dwqww/forge-combo29/swarm/17 && gh_absent=$? ; git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 && git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_1.md | head -5
