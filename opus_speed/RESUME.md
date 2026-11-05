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

## State at 13:25 (job finishing; nothing of the job runs after the final push)
- All timing done (abba_history.log has every run): singles, four 16-round re-times (pooled decisions in
  FINAL_REPORT 3b), stacks w1-w5 + trial_w6 vs the lock, direct trial_w6 vs stack_w2 (+4.39 % WIN).
- Proofs: every stack bit-exact L1-L4 + full 12k (stack_w5's 12k was the last run, 13:24 -> ~13:36,
  `F:\ospd\logs\bx_stack_w5_full12k.out`); QA's own kit rebuilt all six stack exes byte for byte (`F:\ospd\qakit`).
- Warm-table identity (`tools/warm_identity.py`, 1,000 FENs, go nodes 20000, no ucinewgame, 40 option changes):
  all six stacks IDENTICAL to the lock (`F:\ospd\logs\warm2_<stack>.out`, transcripts `F:\ospd\warm2\<stack>\`).
  The first attempt (`F:\ospd\warm\`, 13:21) hung on a wrong output pattern; its three idle processes (python PIDs
  11168 / 7524, lock exe PID 11900) were left running under the no-kill rule (FINAL_REPORT section 8).
- FINAL_REPORT.md is FINAL (13:36).
- Independent patch review done (`REVIEW_PATCHES_INDEPENDENT.md`: no BLOCKER / SHOULD, 5 LOW).
- Tests re-run after the timing queue: CR 13/13, move-order mutant 3/3.
- If a later session continues: QA items are in FINAL_REPORT section 5 and the patch review's section 4.

## Re-run recipe for a pack whose L1-L3 passed but L4 used the old MSVC comparison
`speed_pack.ps1 -SrcDir F:/ospd/src/<src> -Name <name>_b -Define <SW>=<v> -Quick -AaCsv F:\ospd\abba\aa_lock_d20_s3\runs.csv
 -ReuseBuildDirs F:\ospd\builds\pack_<name>_lp_v1_pc1,F:\ospd\builds\pack_<name>_lp_v1_pc2 -PriorBitexact F:\ospd\packs\<name>\bitexact`

## Next steps (owner / QA; this job locks nothing)
1. QA times stack_w2 first, then trial_w6 (or stack_w5 without the weak NNUE_ZMM) on QA's own cores.
2. QA tests from the patch review's section 4 that were not run here (test 1's game-continuation replay at go depth
   10, stop / ponder, Threads soak, poison build of the stacked source, extreme positions under ASan, net-off 2k
   subset).
3. Owner items in FINAL_REPORT section 8 (CR 637B LOW notes text, kit -Kit preflight, lock bad_captures_ bound,
   GPU guard date filter).
