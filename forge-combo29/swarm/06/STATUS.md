## 2026-11-16T (seat block)
seat: 06
area: 6 (SYMMETRY)
branch: for-fable-and-opus/swarm-06
seed: 601
done: seat claimed, toolchain checked (gcc 13.3.0, cmake 3.28.3, python-chess 1.11.2, 4 cores)
next: build engine at 6b98f217 outside work tree, honesty check
## 2026-11-16T21:15Z
seat 06, area 6 (SYMMETRY), branch for-fable-and-opus/swarm-06, seed 601
done: STEP1 seat; STEP2 build + honesty 4/4 (312866/862329/3024920/4865609);
      job1 static eval vs colour mirror: 0 diffs in 8,103 pairs, 4 configs, both controls good;
      job2 left-right mirror: hce differs on 98.2%/98.8%, proven to be ONLY the tuned PSQT table
      (diagnostic symmetrised build: 0 of 334 and 0 of 430 differ, perft 5 unchanged);
      corrected job1 report (net IS residual, total = clamp(hce+nnue)).
findings: S-F1..S-F5 in FINDINGS.md.
next: area 6 job 3 - search depth 10, S14, each G position vs its colour mirror: bestmove (mirrored)
      equal, score equal. Next command:
      cd /agent/repos/dwqww/forge-combo29/swarm/06/job3 && python3 harness_search.py ~/bld/release/forge G_353.fens out_search.txt meta_search.txt
## 2026-11-16T22:02Z
seat 06, area 6 (SYMMETRY), branch for-fable-and-opus/swarm-06, seed 601, area jobs 1-3 DONE
done since last block:
  - fix/REPORT_next.md now has THREE addenda: (1) tie-break variants A/B/C REFUTED (101->114/104/117),
    plus seat 19's 19-F15 as the closing explanation of why no tie-break could ever keep the pins;
    (2) root-window purity D refuted (101->149 at 31.4x nodes), continuation-history colour index E
    refuted (101->108, depth-1 unchanged), state probe = outcome B (all 3 modes identical, my harness
    exonerated); (3) instrumented per-root-move vectors (patch F, pins unchanged): 19 of 20 positions
    differ per root move, 2 have identical totals while per-move counts differ; TT-clear-per-root-move
    G refuted (depth-1 unchanged 25 vs 30).
  - corrected my own S-F12 (searchmoves probe was depth-1-only and root_restricted_ branches 4 ways).
  - S-F21: scoped the 28.6% rate - G 28.6% (24.1-33.5 CI), R601 19.5%, R611 21.5%, seat 20's 10.0%
    overlaps and seat 20's own S-C16 reproduces 101/353 exactly. 101 unchanged.
findings S-F1..S-F21, S-C1 closed, S-C1/S-F8/S-F12 self-corrections recorded.
all patches in fix/ are EVIDENCE ONLY (every variant fails the honesty pins); none is a candidate.
next: read board for NEW unconfirmed finds (cycle step 2a), else area 6 job 1 third seed (SEED 621).
Next command:
  cd /agent/repos/dwqww && for s in 01 03 05 11 16 20 21 27 28; do git fetch -q --depth 1 origin for-fable-and-opus/swarm-$s && git show FETCH_HEAD:forge-combo29/swarm/$s/FINDINGS.md | grep -c 'NEW'; done
## 2026-11-16T22:19:32Z CONTINUE: 12 more hours, ends at 2026-11-17T10:19:32Z
seat 06, area 6 (SYMMETRY), branch for-fable-and-opus/swarm-06, area jobs 1-3 complete
plan for the 12 h: (a) read FABLE files 4 and 5, (b) build the PC engine from FABLE 5 with
-DFORGE_MATE_ALPHA_GUARD=1 in a separate copy and check its bench numbers, (c) re-run my own
finds on the PC build under PC20 and restate every finding line with build + settings,
(d) then THE CYCLE: confirm other seats' NEW finds, then area 6 job 1 again with the next seed.
next command: git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_4.md
## 2026-11-16T22:35Z
- read FABLE files 4 and 5 (all five now read).
- PC r15 build: patch sha256 matches d6bd72c531f785f4, 11 files, patch -p1 no fuzz, g++-13 Release
  -DFORGE_MARCH=x86-64-v4 -DFORGE_MATE_ALPHA_GUARD=1, separate copy /tmp/pc + /tmp/bld/pc.
- PIN CHECK 7/7 exact: none 312866/862329/3024920/4865609; S14 242796/656517; PC20 278024/587276.
  New numbers recorded: bench 16 2155620 (S14) and 2343893 (PC20); perft 5 4865609 both.
- THREADS AUDIT: every harness of mine uses Threads 1; no score of mine is provisional.
- PC20 rerun of my own finds: S-F1 HOLDS (0/353 eval pairs differ). S-F6 NOT REPAIRED
  (120/353 = 34.0% bestmoves, 331/353 = 93.8% scores, vs base 101/28.6% and 334/94.6%).
- findings S-F23..S-F26 added with build + settings in every line.
next: THE CYCLE - read the board for other seats' NEW unconfirmed finds, confirm one with my own
harness on the same build/settings; then area 6 job 1 with SEED 621 on the PC build under PC20.
## 2026-11-16T22:52Z
- CAUSE THREAD: one-position dump complete (cause/REPORT_cause.md). Key data: the move generator's
  EMISSION ORDER differs under a colour mirror (root_effort_moves_ comes straight from legal_moves(),
  search.cpp:2203-2207, so its slot order is the generator's order). On the clearest mismatching
  position at depth 4 the SCORE and PV are identical (-1861, same line) but per-root-move node counts
  diverge (e6f6 182 vs 154, e6f7 170 vs 30) while 4 of 6 root moves cost exactly the same. The two
  differing subtrees are structurally identical (22 replies each, no captures, no check). So by the
  brief's own branch rule - scores agree, node counts diverge - it is ORDERING, not evaluation.
- variant H (canonicalise the generator's emission order, not the sort) BUILT: it does make emission
  order mirror-invariant on all 3 test positions, perft 5 unchanged at 4865609 (pure reorder), benches
  move as any order change must. Full asymmetry measurement not yet run.
- PRIORITY INTERRUPT: the reported wrong-move defect on the PC build is now the active job. Independent
  harness wrongmove/repro_wrongmove.py written from the report's sentence only; runs in flight for
  c6c7 and c6d6 at depths 16/18/20 on the PC build (searchmoves separately, fresh process each,
  Threads 1). Base build and the lone-king control next.
next command: cat forge-combo29/swarm/06/wrongmove/out_pc.txt
