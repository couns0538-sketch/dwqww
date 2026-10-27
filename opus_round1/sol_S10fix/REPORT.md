# S10fix [Sol fix-ups S10-1..6] search ideas batch — DONE

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, items S10-1..S10-6. Branch `opus-sol-S10fix` = `d4f4312` + CI baseline
`0d99f02` cherry-picked (`5c67adfb`) + `ab6341e6` (this job's files) + the REPORT commit. Tool/evidence job
(`[skip ci]`): no engine change on the branch; the one engine re-run (S10-3) used a scratch build of Sol's base B.
Sol's files (`17aa0cae`) were only read. No Elo, speed or strength claim. Machine exclusive: no.

## Acceptance
| item | command | result |
|---|---|---|
| **S10-1** (process) WAC < 283/300 or the 20% node guard = FAIL; skip B qualification | `opus_s10_screen_verdict.py --sol-consolidated <Sol's consolidated results v2>`; the rule: `S10_screen_rule_v2.md` | **DONE**. All four ideas FAIL on the Lprime screen: QuietCheckLmpSurvival (WAC 269), ImprovingRazorGuard (WAC 270; guard d20 -24.3%), SingularSiblingLmr (WAC 263; guard d20 +24.7%), CaptureHistoryLmp (WAC 258; guard d20 -30.8%, d22 -23.9%), so B qualification is SKIPPED for all four (Sol ran B for all four). A missing number counts as FAIL; cheap gates (d11 activation, node guard, WAC) come before full Std/ASan. `s10_screen_verdicts.json`, `logs/step6` |
| **S10-2** one line "why it likely failed" per rejected idea; which WAC positions flipped vs OFF | `opus_s10_wac_flips.py`: each idea's single Lprime `wac_ON` run vs Sol's S07 OFF run of the Lprime build (same tool, 1000 ms, 271/300) | **DONE**: `s10_wac_flips.md` (flips, depth/score of OFF and ON per flipped position, key-move kind, cross-idea view) and `s10_why_rejected_v2.md` (table below). Sol's solved flags re-checked with python-chess on all 1,500 results: 0 disagreements. `logs/step5` |
| **S10-3** rerun ImprovingRazorGuard base B OFF d22 once with a longer deadline; log time (harness timeout vs hang) | `opus_s10_rebuild_baseB.py`, `build_pc.sh … -DFORGE_S10_IMPROVING_RAZOR=1`, `opus_s10_bench_rerun.py --depth 22 --option ImprovingRazorGuard=false --deadline 3600 --expect-nodes 31111774` | **DONE: a harness timeout, not a hang.** Base B rebuilt from git objects: 73/78 files byte-exact to Sol's sha256 freeze (missing only IDEA_SOURCE.md, README.md, tests/tests.cpp, tools/rerecord_pins.py/.sh, none compiled into the engine); after the patch's engine part all 73 match Sol's post-patch B freeze. Build `ac237e0b…` (box recipe g++ 15.2, compile switch ON), FMA 0, 0 warnings; bare bench 11 = 308,972. Same UCI sequence as Sol's controller (ImprovingRazorGuard advertised, set false): **bench 22 = 31,111,774 nodes (= reference), bench line after 21.8 s wall**, engine CPU 19.0 s (21,724 ms, 1.43M NPS engine-reported), CPU time grew 4.3-4.5 s per 5 s sample (no stall), run at Idle with the PC at 98.8-99.2% CPU. Sol's same-source OFF d22 runs took 76.4-165.8 s (7 runs, 188k-407k NPS) under the same 180 s observer, and his B OFF d20 for this patch ran at 188k NPS, about 165 s for d22 before start-up: his 181.7 s timeout was the deadline, not the engine. `logs/step1`-`step4` |
| **S10-4** no `_before_<fix>` copies (keep finals + one diff log) | `opus_s10_hygiene_check.py --dir` / `--git … --tree 17aa0cae` | **DONE**. This folder: 0 `_before_` copies, 0 duplicate files (gate exit 0). Sol's S10 delivery (201 files, 59,314,607 B): 1 `_before_` copy (`validation/…/forge_sol_S10_activation_before_guard_20261026.py`) and 17 groups of byte-identical files (96,749 extra bytes: the seal script x5, every checkpoint .md x2, every patch x2, …). One diff log, `s10_superseded_vs_final.diff`: before_guard vs final activation script, closed report v1 vs v2, consolidated results v1 vs v2. Nothing of Sol's was edited or deleted. `logs/step7`, `logs/step10` |
| **S10-5** list every .tar.gz size | same tool | **DONE**. Sol's S10: capture_history_lmp 16,616,405; improving_razor 8,430,332; quiet_check_survival 16,617,977; singular_siblings 16,620,161 (58,284,875 B; sha256 match his report). Input also read: S07 native evidence 210,313 B. This job: "Archives" below. |
| **S10-6** record "machine exclusive" in every screen; never push during a screen | `opus_s10_bench_rerun.py` writes it with load samples and the busiest processes | **DONE** for this job's screen: `machine_exclusive: no`, system CPU 98.8-99.2%, RAM and busiest processes logged; the screens ran 21:35:20-21:35:57 UTC, the first push of this session was 22:02 UTC. Sol's screens: recorded only for CaptureHistoryLmp ("no": a git upload may have overlapped its start); the NPS of the final info lines shows his WAC runs ran 14% slower to 9% faster than his OFF run. |
| tests / planted bugs | `test_opus_s10fix.py`, `opus_s10_mutants.py` | **12/12 PASS**; **5/5 mutants killed** (guard sign, WAC boundary, lost/gained swap, duplicate groups, bench Hash option). `logs/step8_9` |

## S10-2: why each idea likely failed (OFF reference 271/300)
| idea | WAC ON | node guard d20 / d22 | why it likely failed |
|---|---|---|---|
| QuietCheckLmpSurvival | 269 (-2) | PASS (-7.9% / -12.1%) | No measurable tactical loss: -2 is inside the 1-3 point noise (11 lost / 9 gained; 6 of the 11 losses are also lost by other ideas; its run was 11% slower than OFF's); it failed only the absolute 283 floor, which the OFF build itself misses on that box (271). Its own 3 losses (WAC.080, .089, .169) are quiet key moves, as expected if keeping quiet checks spends the late-move budget. |
| ImprovingRazorGuard | 270 (-1) | FAIL (-24.3% / -18.5%) | Failed on the node guard, not on tactics: -1 is noise (8 lost / 7 gained); turning razoring off for improving nodes swings the tree size with depth (+15.9% d16, -24.3% d20, -18.5% d22). Its B "failure" was the 180 s deadline (S10-3). |
| SingularSiblingLmr | 263 (-8) | FAIL (+24.7% / +3.8%) | A real loss: 8 losses only for this idea (WAC.046, .082, .119, .191, .194, .236, .238, .264; checks .082/.194, captures .119/.238) where ON reaches only d9-d15 and OFF d15-d18 (one mate); matches +24.7% nodes at d20: the extra sibling reduction likely costs re-searches in exactly these tactical trees. |
| CaptureHistoryLmp | 258 (-13) | FAIL (-30.8% / -23.9%) | A real loss: 15 lost / 2 gained; 4 of its 6 own losses are forcing check/mate solutions (WAC.239 f2f1, .250 e3e8 mate 8, .282 h1h8 mate 4, .288 h5f6) where ON stops at d4-d13 with a quiet move; pruning late losing captures with negative history likely cuts the sacrifice lines they need. Its run was also 14% slower (git upload overlap noted by Sol), which explains part of the 6 shared losses. |

## Findings
1. The 283 floor was not reachable on Sol's box even for OFF: the same harness scored the Lprime OFF build 271/300 (S07).
   QuietCheckLmpSurvival (-2) and ImprovingRazorGuard (-1) are within noise of OFF; SingularSiblingLmr (-8) and
   CaptureHistoryLmp (-13) are real losses. The rule stays as QA wrote it (all four FAIL); a floor relative to a
   same-session OFF run would separate noise from loss.
2. Ten positions flip the same way in 3-4 of the 4 ideas (WAC.033/.101/.165/.190 gained; .071/.081/.193/.229/.243/.297
   lost): run-to-run noise of the single OFF run at 1000 ms, not effects of one idea.
3. The B OFF d22 "FAIL" was a deadline set too tight for a loaded box (180 s vs 76-166 s observed for the same work).
4. Rebuilding base B needs `git -c core.autocrlf=false apply` (the PC's system git has autocrlf=true and wrote CRLF,
   changing every hash) and only the engine part of the patch (B's IDEA_SOURCE.md/README.md are not in this repo).
5. Sol's delivery repeats files (the seal script 5x, checkpoints in two folders) and keeps a `_before_guard` copy;
   the hygiene tool flags both and exits 1 on any `_before_` copy.

## Left / UNVERIFIED
- A Linux/GCC 14.2 rerun of Sol's exact B binary is not possible here (PC build: g++ 15.2 znver5, node counts
  identical); a Linux-only hang is not excluded, but nothing points to one.
- 5 of base B's 78 files (docs/tests/tools) are not in this repository; not needed for the bench.
- S10-2 rests on one OFF and one ON WAC run per idea (existing logs, as asked); no WAC re-run.
- All four ideas stay rejected and OFF; no Elo, speed or strength claim.

supervisor.log: 7 "adopted running job" lines before and after (no NNUE work in this job).

## Archives (every .tar.gz with its size, 9 files, 22,037 B)
`logs/`: step1_rebuild_baseB 6,471; step2_build_baseB_improving_razor 414; step3_bare_d11 1,328;
step4_B_OFF_d22_rerun 5,425; step5_wac_flips 5,261; step6_screen_verdicts 713; step7_sol_hygiene 1,457;
step8_9_tests_and_mutants 577; step10_own_hygiene 391.
