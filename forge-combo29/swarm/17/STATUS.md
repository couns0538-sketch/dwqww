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
