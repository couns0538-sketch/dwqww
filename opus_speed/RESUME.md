# Forge speed job - RESUME (read this first after a /clear, restart or usage stop)

- Clone: `F:\ospd\wt` (partial + sparse: /opus_speed/ /skills/), branch `opus-speed-20261105`, upstream unset,
  `core.autocrlf=false`, clean filter `novendor` for .md/.txt (code files are linted instead). Commit + push ONLY via
  `bash /f/ospd/wt/opus_speed/tools/commit_push.sh <msgfile>` (lint, control bytes, PS 5.1 parse gates; run it in the
  background, it can take > 2 min under load). `git rm` is refused: unstage with `git restore --staged`.
- AFTER A RESTART: the new session process starts at 0xFFFF / Normal -> pin it: `$p = Get-Process -Id <pid>;
  $p.ProcessorAffinity = 0x3; $p.PriorityClass = 'Idle'`. Own jobs started before a restart keep running (check
  `Get-CimInstance Win32_Process` command lines). Workers: all finished (b1tt, b2mg, jobc); toolrev (independent tool
  review, read-only) running until ~11:30 -> F:\ospd\wt\opus_speed\REVIEW_TOOLS_INDEPENDENT.md.
- Scratch: `F:\ospd\` = src\lock (exact lock source), src\b1_* / b2_* (change copies), src\r14_speed2 (SPEED2 port),
  src\trial_stack3 (4-patch stack: its switch-0 build = FD3A5190 byte for byte), builds\, packs\, abba\ (q2\ variant
  queue, results_q2.tsv, abba_history.log), ref\fd3a5190\ (L1/L2 sig, L3 n2000 + n12000 references; msvc_asan_b16_*),
  logs\. F: >= 50 GB free; F:\ospd <= 8 GB.
- A/A reference for this session: `F:\ospd\abba\aa_lock_d20_s3\runs.csv` (balanced ABBA/BAAB, d20).
- Pitfalls fixed today (details in skills/forge-speed-lock-path): placement-only FENs rejected by the lock; MSVC
  std::sort != libstdc++ (L4 ASan must compare with the MSVC build of the lock source); PS output-stream pollution in
  functions; Start-Process stdin file locking; heredoc backslash collapse; reference-cache race.

## Running at 12:41 (logs in F:\ospd\logs; ABBA runs serialise on the timing mutex, one at a time on CPU 2)
- Done: TT re-time (pooled WIN +2.86 %), slider re-time (pooled WIN +1.52 %), stack_w1 ABBA (+7.31 % WIN) and its
  full 12k, QA kit rebuilds of stack_w2 / stack_w1 / trial_w6 (= pack exes), L4 MSVC ASan of the PEXT builds (PASS).
- Still running: re-times `F:\ospd\abba\retime_b1_prefetch_early_d20_r16`, `retime_b2_nnue_zmm_d20_r16`; b2_nzm1
  ABBA; trial_w6 ABBA then its full 12k (`bx_trial_w6_full12k.out`); direct ABBA trial_w6 vs stack_w2
  (`F:\ospd\abba\direct_w6_vs_w2_d20`, starts after both re-times); worker patchrev (independent patch review ->
  `opus_speed/REVIEW_PATCHES_INDEPENDENT.md`, due 13:20).
- Decide the final winners stack from the pooled re-times: all six winners -> trial_w6 is it; otherwise pack the
  subset from `F:\ospd\src\trial_w6` with `speed_pack -Define` (only the winners' switches), -Quick, then full 12k.
- After the timing queue: re-run tests/test_cr_637b.ps1 and tests/test_moveorder_mutant.ps1 (builds; not during ABBA).

## Re-run recipe for a pack whose L1-L3 passed but L4 used the old MSVC comparison
`speed_pack.ps1 -SrcDir F:/ospd/src/<src> -Name <name>_b -Define <SW>=<v> -Quick -AaCsv F:\ospd\abba\aa_lock_d20_s3\runs.csv
 -ReuseBuildDirs F:\ospd\builds\pack_<name>_lp_v1_pc1,F:\ospd\builds\pack_<name>_lp_v1_pc2 -PriorBitexact F:\ospd\packs\<name>\bitexact`

## Next steps
1. When the re-times land: `python -I -B opus_speed/tools/abba_table.py` over the retime folders; a change whose
   16-round WALL verdict is WIN counts as a protocol winner. Fill FINAL_REPORT section 3 (PENDING_B_TABLE ->
   `pack_table.py --only ...` output + re-time table) and section 5 (which stack QA times first).
2. FINAL_REPORT.md by 14:08; STATUS.md; memory file; final push via commit_push.sh; stop by 14:38.
