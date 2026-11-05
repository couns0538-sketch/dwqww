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

## Running at 10:25 (each writes F:\ospd\logs\pack_<name>.out; a monitor greps verdicts)
- ABBA queue q2 (variants vs lock): remaining ipapta, part1, pvw256, wnonet, wmix, w12k.
- Packs: r14_speed2 (chain 1), b1_prefetch_early (chain 2), locklock_v1b + b2_nnue_zmm_b (L3; L4 will FAIL on the
  old MSVC comparison -> re-run with -ReuseBuildDirs + -PriorBitexact), b1_tt_notls_b (L4 re-run with the fix),
  chain 4: b2_nzm2 -> b2_matkey_fast -> b2_slider_pext -> b2_nzm1, chain 5: b2_pickbest1 -> b2_pickbest2.
- Orphan full 12k lock-copy check (since 09:27): F:\ospd\logs\bx_lockcopy_full12k.out.

## Re-run recipe for a pack whose L1-L3 passed but L4 used the old MSVC comparison
`speed_pack.ps1 -SrcDir F:/ospd/src/<src> -Name <name>_b -Define <SW>=<v> -Quick -AaCsv F:\ospd\abba\aa_lock_d20_s3\runs.csv
 -ReuseBuildDirs F:\ospd\builds\pack_<name>_lp_v1_pc1,F:\ospd\builds\pack_<name>_lp_v1_pc2 -PriorBitexact F:\ospd\packs\<name>\bitexact`

## Next steps
1. Winners (ABBA WIN, bit-exact) -> `make_stack.sh stack_final <patches>` -> switch-0 build = FD3A5190 check ->
   speed_pack of the stack with all winner switches ON, FULL 12k (no -Quick) -> ABBA vs lock.
2. Job A test 3: best flag / workload variant from q2 -> full pack (no -Quick), report its ratio whatever it is.
3. FINAL_REPORT.md (draft exists) by 14:08; skills update; memory; final push; stop by 14:38.
