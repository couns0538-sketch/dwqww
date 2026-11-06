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

## State 19:43 PC clock - CR leftovers (4 SHOULD, independent CR of 73f4041d..00d19e56), start tip 00d19e56
- Live lock = trial_w6, sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0 (QA's publish;
  CURRENT_LOCK.json / gates / queue untouched). FD3A5190 = the old lock, still the search-identity reference.
- DONE (19:47): SHOULD 4 (patchrev_qa LOCK = trial_w6), 2 (skill verdict rules + mirror), 3 (FINAL_REPORT QA owner
  item), 1 (warm_identity self-pin + read-back). `tests/test_cr_should_w8.ps1` 8 / 8 PASS from Git Bash (run
  20261105-194720-5676). Nothing of this follow-up is running.

## State 20:02 PC clock - leftover jobs 1-3 (start tip 38559f1b)
- Job 1 DONE: `tools/uci_lib.ps1` defaults = the live lock trial_w6 (`$OspdLockExe` / `$OspdLockSha`). FD3A5190 stays
  as `$OspdOldLockExe` / `$OspdLockSrc` (search identity). Labels in abba_queue, bitexact_check and speed_pack were
  updated. Test W6a and W4b now use these.
- Job 2 DONE 20:03: `tests/warm_refusal_check.py` (W5a-e) + W6a. `tests/test_cr_should_w8.ps1` 14 / 14 PASS (run
  20261105-200352-9252).
- Job 3 DONE 20:07:
  - 3a: patchrev_qa: mask range check, then the timing mutex, then placement.
  - 3b: K3 comment at `is_legal` in the trial_w9 / w9dev board.hpp. `patches/trial_w9.patch` (8bf44bab) and
    `b4_king_lines_after_w8.patch` (d680f9bf) were regenerated with `diff -ruN` in F:/ospd/src. Proof:
    `F:\ospd\tmp\k3proof_20261105-200606`.
  - 3c: the test takes `-Py`.
- Test run: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File opus_speed\tests\test_cr_should_w8.ps1 -Py
  C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe` (or set OSPD_PY): 14 / 14 PASS (20261105-200713-5164;
  after the 20:09 whitespace fix again 14 / 14, 20261105-200930-9164).
- 20:15 extras:
  - pin_check of the default lock exe: PASS.
  - test_stack_poison.ps1 takes `-Py`.
  - `tests/test_cr_637b.ps1` re-run (o3 builds on CPUs 0-1 Idle, no ABBA): 13 / 13 PASS (20261105-201312-4460).
    Output: `F:\ospd\logs\test_cr_637b_after_leftovers.out`.
  - Nothing is running now.
- State 20:10: leftover jobs 1-3 are DONE. Open for QA / owner:
  - L3b warm_identity, a Threads 2-4 soak and an independent ABBA vs trial_w6 before any lock;
  - the LOW notes in `CR_SHOULD_W8.md`.
- Not done on purpose: no ABBA / soak / 12k / L3b; KING_LINES and bundles a-d untouched.
- Not done on purpose: no ABBA / soak / 12k; KING_LINES and bundles a-d untouched (QA owns their timings).

## State 20:41 PC clock - bit-exact speed hunt vs trial_w6 (owner /plan brief; plan `opus_speed/PLAN_HUNT.md`)
- Start tip 3ca407b3. Live lock trial_w6 4181A589... (both paths checked); FD3A5190 = search-identity reference.
- Hunt scratch `C:\ospd_hunt\` (abba\, builds\, ctl\, prof\, harness\, logs\); packs `F:\ospd\packs\h<N>_*`,
  trees `F:\ospd\src\h<N>_*` (make_stack.sh trial_w6.patch + `patches/h<N>_*_after_w6.patch`).
- Per idea: identity builds (all 0 = FD3A5190, six ON + new OFF = 4181A589) -> speed_pack -Quick -SkipAbba (the six +
  the new define) -> abba.ps1 alone vs trial_w6 into `C:\ospd_hunt\abba\` -> WIN: full 12k + pack.
- Session A/A: `C:\ospd_hunt\abba\aa_w6_d20_s1` (started 20:42).
- 20:57: profile done (`C:\ospd_hunt\prof\w6_b20_r1`, rip_sampler; table in FINAL_REPORT 9.1). H1 `h1_largepages`
  (FORGE_SPD_LARGEPAGES=1): identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; speed_pack -Quick -SkipAbba
  running (log `C:\ospd_hunt\logs\h1_largepages.out`). H2 `h2_dirty_inplace` (FORGE_SPD_DIRTY_INPLACE=1): tree ready,
  harness `tests/dirty_inplace_diff.cpp` PASS (18.9M moves, 0 mismatches; mutant FAIL); its hunt_candidate.sh is next.
  Then: A/A 2 (alone) and the ABBAs of H1 / H2 (alone, `C:\ospd_hunt\abba`).
- 21:22: pipeline state. Packs BIT-EXACT: h1_largepages (cecc4d92), h2_dirty_inplace (8c3f2747), h3_nnue_columns
  (9bcdef73). Timing block 1 runs from the private queue `C:\ospd_hunt\logs\queue2.sh` (log `queue2.out`): A/A 2
  `C:\ospd_hunt\abba\aa_w6_d20_s2`, then ABBA `C:\ospd_hunt\abba\h1_largepages_d20`, `h2_..._d20`, `h3_..._d20`,
  then H4's CPU steps. After it the task runner `C:\ospd_hunt\logs\hunt_runner.sh` (log `hunt_runner.out`) works
  through `C:\ospd_hunt\logs\tasks.txt` (cpu h5, cpu h6, aa s3, abba h4-h6); append lines to add work, a line
  `stop` ends it (cooperative; never kill). Trees h4_slider_pdep16, h5_move_store32, h6_pick_first are ready.
- Harnesses (tests/): dirty_inplace_diff.cpp (H2), nnue_update_diff.cpp (H3), slider_pdep16_diff.cpp (H4),
  movegen_hash.cpp (H5); H6 = scratch verify copy `C:\ospd_hunt\harness\h6verify` (not a patch).
- Stacking note: H2 and H3 both insert after the NNUE_ZMM block in nnue.hpp, so a stack of both needs a hand-merged
  patch (make_stack applies with -F0, no fuzz).
- 21:56: runner v2 (`C:\ospd_hunt\logs\hunt_runner2.sh`, tasks2.txt) builds + proves H6-H9, then reads its `stop`
  line; runner v3 (`hunt_runner3.sh`, tasks3.txt, log hunt_runner3.out) then runs the timing block: `aa_gate s4 3 8`
  (A/A until `tools/aa_sane.py` says SANE, max 3, 8 min apart), ABBA H2, H3, H6, H5, H8, H9, H4, `abba_lp` H1 (16
  rounds = its one re-time) / H7 only if `tests/lp_probe` gets large pages at that moment, A/A 5 to bracket.
- Large pages fail since the trainer restart (error 1450): H1 run 1 measured the fallback. CPU sampler log
  `C:\ospd_hunt\logs\cpu_sampler.log` (ends by itself after 240 min).
- Scratch merge of the seven non-LP switches on trial_w6 (`C:\ospd_hunt\merge\m1`): all patches apply (H3 fuzz 1 in
  nnue.hpp, checked), all-on and six-only compile. A stack of winners = only the winners' patches on trial_w6, then
  make_stack + hunt_candidate with the comma-joined new defines.

## State 00:02 PC clock - hunt finished (DONE-QUIET written; final table in STATUS.md, summary FINAL_REPORT 9.0)
- Screening WIN: H5 `h5_move_store32` (FORGE_SPD_MOVE_STORE32=1, exe 5dec3fa7, pack `F:\ospd\packs\h5_move_store32`,
  quiet ABBA `C:\ospd_hunt\abba\h5_move_store32_q_d20`). Full 12k L3 vs trial_w6 runs from runner v3 (`full`); its
  result goes to `F:\ospd\packs\h5_move_store32\bitexact_full12k` and FINAL_REPORT 9.6.
- H1 (large pages) needs a quiet re-time with large pages available (its run was under the returned trainer and the
  pages failed partway); H7 was not timed. Both are BIT-EXACT packs.
- Owed to QA for H5 before any lock: own re-time vs trial_w6, L3b warm_identity, Threads 2-4 soak (skill lock path).
- Runner v3 ends with a `stop` line after the two full 12k runs; the CPU sampler ends by itself (240 min from 21:52).

## State 00:41 PC clock - FINAL (hunt finished, DONE-QUIET written twice; last at 00:41)
- One screening WIN: H5 FORGE_SPD_MOVE_STORE32 (pack `F:\ospd\packs\h5_move_store32`, exe 5dec3fa7, full 12k BIT-EXACT,
  quiet ABBA +1.21 % wall / +1.25 % cpu vs trial_w6). Everything else NO-WIN (STATUS.md final table; FINAL_REPORT 9).
- H1 / H7 large pages re-timed in the second quiet window with large pages proven available: NO-WIN (-0.19 %, +0.61 %).
- Runners v3 / v4 stopped; nothing of the hunt runs except the read-only CPU sampler (ends by itself ~01:52).
- Next (QA): own re-time of H5 vs trial_w6 on QA's cores, L3b warm_identity, Threads 2-4 soak; optional re-times of H2 /
  H3 (intervals above 1.000, medians +0.53 % / +0.81 %); a lock decision is QA's.
