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
