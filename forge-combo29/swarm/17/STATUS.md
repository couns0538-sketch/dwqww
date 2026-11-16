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
