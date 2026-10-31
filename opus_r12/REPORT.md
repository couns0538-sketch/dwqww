# R12 - LTO+PGO profile with the HalfKA net path — IN PROGRESS (checkpoint)

Branch `opus-r12-pgo-net` = 7f79c349 (r10fix1, engine unchanged) + R12 commits (kit, tools, report). No Elo or gate
claim; QA gates. Machine exclusive: no (gates, NNUE trainer w4_s4 and self-play kept running).

## State at this checkpoint
- Done: kit v2.4 (`kit_v24/`): frozen workload v2 + `tools/train_driver.py`, `-Workload v2`, `-PartialTraining` (item 2b),
  `-CheckOptPins`; R12 tools `r12_build_chain.py`, `r12_speed.py`, `r12_fens12k.py`, `exe_func_diff.py`; skill
  `forge-ltopgo-pgo`. Script parses with 0 errors in PowerShell 5.1 and 7; a dry run (empty source) bound every new
  parameter; train_driver smoke on plain D8D90B68 OK.
- Source: `F:\opus_scratch\r12\src_r10fix1` = QA's `cands\r10fix1\forge_r10fix1_src`, byte-identical to git 7f79c349
  (src/, include/, CMakeLists.txt: 23 files).
- Waiting (since 20:02 PC clock): no CPU pair free for profiling/timing (trainer 0x000F Idle on 0-3, gate 0xFFF0,
  self-play 3-CPU masks inside 4-15; QA's own qa_x_check ran on 0x0003 until ~20:03). Two background runners wait:
  the build chain (`F:\opus_scratch\r12\logs\chain.log`, strict: starts when no gate / trainer / self-play / QA process
  holds a pair, e.g. after QA narrows the trainer mask as in speed4) and `r12_phase2.py`
  (`F:\opus_scratch\r12\phase2\phase2.log`: binding check, 12k identity, speed; starts after the chain). Nothing heavy
  has run yet. If QA frees 0/1 without changing the trainer mask: start
  `r12_build_chain.py ... --pair 0x3 --ignore-idle --log F:/opus_scratch/r12/logs/chain2.log` and
  `r12_phase2.py ... --chain-log F:/opus_scratch/r12/logs/chain2.log --ignore-idle` (the first chain then stops at
  its first build because the tag exists; one phase2 owns the output folder).

## Next steps (if QA picks this up)
1. `r12_build_chain.py` builds A = workload v2 (tags r10fix1_w2_pc1/pc2) and B = v2 + `-PartialTraining`
   (r10fix1_w2pt_pc1/pc2) with `-Expose`, znver5, FMA 0; binding check: pc1 = pc2 forge_ltopgo sha256 per variant.
2. Identity: kit OFF pins + net pins (e19 373062/.../4115992, e9 287095/.../2816047 = plain D8D90B68's counts),
   `r12_fens12k.py` 12000/12000 vs D8D90B68 for both nets.
3. Speed (`r12_speed.py`, one CPU of the freed pair, sibling idle): net: A, B vs D8D90B68 and 9E5CB644, d16 + d20,
   7 palindromic blocks + 3 A/A blocks; no net: A, B vs FD3A5190. Median + bootstrap one-sided 95% lower bound.
