# SEAT 03 STATUS

- seat: 03
- area: 3 (MOVE GENERATION against python-chess)
- branch: for-fable-and-opus/swarm-03
- seed: 301

## 2026-11-16T21:06:34Z

seat claimed, starting STEP 2 build

## 2026-11-16T21:14Z

HONESTY: all four pins MATCH (bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609).
Build: /home/ubuntu/build-rel/forge, g++ 13.3.0, -DFORGE_MARCH=native, sha256 68825bd5...

## 2026-11-16T21:35Z

Job 1 DONE (S-F1); job 2 DONE (S-F2, S-F3). HARNESS_AUDIT vs 19-F12 (pipelined quit): my perft/bench numbers
immune (inline in the UCI loop) and re-proved with honesty2.py.

## 2026-11-16T21:37Z

PARSE_AUDIT vs seat 19's NaN warning: `assert_measured.py` fails loudly on a missing/NaN/zero result, with
negative controls that both fail. Two real defects of mine found and recorded.

## 2026-11-16T21:50Z

- **03-C1: CONFIRMS seat 13's S-F1** — both halves measured with my own harness on their R_1301 set:
  their engine file vs my engine run 20,000/20,000 equal; my python-chess run vs my engine run 20,000/20,000 equal
  (sums 113,231 / 2,678,512 / 77,182,397 / 2,260,227,623). Their raw_ref.txt being byte-identical to raw_engine.txt
  is the expected consequence of 0 differences (run1 ref killed, exit 143; run2/ref_par.py regenerated in 616.8 s).
- **S-F4**: 320 constructed en-passant-pin positions — engine root move set = python-chess 320/320, plus a
  slider-removal control passing 320/320 (delete the pinner -> the same ep capture becomes legal, engine still
  matches). Goes beyond 23-F6's three hand-built cases.

## 2026-11-16T21:52Z — WARM-STATE AUDIT (seat 10's report)

Reproduced seat 10 (three `go depth 12` in one process: 56,720 / 4,951 / 4,516). Measured that it cannot reach my
tables: `go perft 4` on a mid-game position gives **1,110,595** ten times in ONE process, the same after
`ucinewgame`, the same after `Clear Hash`, and the same in ten separate processes — constant all three ways, while
the same harness shows the depth effect as a control. `Clear Hash` was never used by me (grep: zero occurrences).
Write-up: WARM_STATE_AUDIT.md, raw job0/warm_state.*.raw.

## 2026-11-16T22:10Z — JOB 3 COMPLETE (S-F5)

perft 1..5 on 230 positions (200 R + first 30 of G): **1,150 of 1,150 values equal to python-chess**, perft-5 sum
**3,925,995,728 on both sides**, 0 refused FENs, 0 crashes, 0 error lines; perft-1 move sets identical.
python side 1130.6 s. Files: job3/job3_table.txt, job3/job3_diffs.txt (0 lines), job3/py_all230.json.
A 60-position subset measured separately agrees too (sums incl. perft-5 1,552,941,785).

Runs: job1b (cycle step 2c, SEED 311) python perft 1..4 on 5,000 positions — engine half already done
(sums 112,193 / 2,606,301 / 74,557,281 / 2,159,914,969; 0 duplicate FENs vs the SEED-301 set).
Next: compare job1b; if it does not land by 22:30, push the engine half with the comparison marked incomplete and
the exact next command.

Next command:
`cd /agent/repos/dwqww/forge-combo29/swarm/03/job1b && tail -1 py.log && python3 ../assert_measured.py perft py.json 4 5000 && python3 ../job1/compare.py eng.json py.json diffs.txt | head -12`

## 2026-11-16T22:19:10Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:10Z

Seat kept: 03 (from ~/swarm_seat.txt). Branch for-fable-and-opus/swarm-03. Area 3 still.
Done so far: S-F1..S-F5, 03-C1, HARNESS_AUDIT, PARSE_AUDIT, WARM_STATE_AUDIT (see FINDINGS.md).
Next, per the owner's TEXT 2: read soak_all/FABLE_TO_swarm_5.md, build the PC build in a separate copy with
-DFORGE_MATE_ALPHA_GUARD=1, check its known bench numbers, then re-run my perft sets on it and compare node counts
to the base build.

## 2026-11-16T22:21Z

Read FABLE_TO_swarm_2, _3, _4, _5 (all five now). File 5's PC source built and verified:
- patch extracted from lines 56..2374 of file 5, sha256 d6bd72c531f785f4… = the published prefix (an earlier
  extraction at 57..2374 gave 83ce05d8… — recorded, because a wrong extraction yields a silently different engine)
- applied with `patch -p1` in a SEPARATE worktree /agent/repos/pccopy (11 files, no fuzz), built with
  -DFORGE_MATE_ALPHA_GUARD=1 -> /home/ubuntu/build-pc/forge
- **all eight published numbers MATCH**: none-regime 312866 / 862329 / 3024920 / 4865609; S14 242796 / 656517;
  PC20 278024 / 587276. MateAlphaGuard verified present in the exe's own uci list before sending it.
- job1b (SEED 311) COMPLETE: 20,000/20,000 equal, move sets identical, 0 duplicate FENs vs SEED 301.
- job4 (PC build perft) under way: sets A and B done — **40,000 of 40,000 values identical to the base build**
  (perft-4 sums 2,196,757,662 and 2,159,914,969 exactly equal). Set D (perft 5) running.

Swarm rule Threads 1 (22:20Z): perft does not use threads or the hash at all — `Board::perft`
(src/board.cpp:1205-1222) is a plain recursive walk with no hash probe — but I now state `setoption name
Threads value 1` (and Hash 16) explicitly in job4/engine_perft_t1.py so no table of mine can be misread.
