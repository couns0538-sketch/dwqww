## 2026-11-16T21:10Z
seat: 16
area: 6 (SYMMETRY)
branch: for-fable-and-opus/swarm-16
seed: 1601
- STEP 1 done: seat claimed, SEAT.txt pushed.
- next: STEP 2 engine build (worktree ../base) + honesty check.

## 2026-11-16T21:08Z
- STEP 2 done: release build at /home/ubuntu/builds/bld-release/forge, sha256 e06310ec..., id name "Chess Engine Forge 6.4.24 candidate".
- HONESTY 4/4 equal (312866 / 862329 / 3024920 / 4865609).
- next: THE CYCLE step 1 (read board) then area 6 job 1.

## 2026-11-16T21:14Z
- job1 (area 6) done: static `eval` of 353 G + 500 R positions vs python-chess colour mirror →
  853/853 identical in hce, nnue and total; controls: self 0 diffs, three true pairs 0 diffs,
  forced asymmetry 3 fields differ (harness can see a difference).
- files: job1/, REPORT_job1.md, FINDINGS.md (empty, negative result).
- next: cycle 2 — read board; then area 6 job 2 (left-right mirror on positions without castling).
