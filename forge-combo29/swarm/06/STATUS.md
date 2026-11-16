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
