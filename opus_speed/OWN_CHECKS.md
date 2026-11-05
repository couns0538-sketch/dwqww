# Own review pass of the speed job (coordinator, 2026-11-05 from 12:1x; NOT independent)

This is the coordinator re-checking its own work. It does not replace the independent tool review
(`REVIEW_TOOLS_INDEPENDENT.md`, worker toolrev) or QA's own timing. Each line: what was checked, how, result.

| # | check | how | result |
|---|---|---|---|
| 1 | Every headline ABBA summary is what its runs.csv says | `tools/abba_recheck.py` (new): per-round (B1 + B2) / (A1 + A2), median, 95 % Student-t interval of the mean log ratio with an EXACT t quantile (numeric integration; abba.ps1 uses a short series, 2.2584 vs 2.2622 at df 9), WIN rule, one md5 + one node count per arm | 10 folders (stack_w2, stack_w3, b2_nzm2, r14_speed2_b, b1_tt_notls_b, b1_prefetch_early, b2_slider_pext, b2_nnue_zmm_c, locklock_v1c, A/A aa_lock_d20_s3) x wall + cpu: max difference 0.00005, no verdict changes: PASS |
| 2 | The committed stack patches rebuild the timed sources | `diff -ruN lock <tree>` hunks vs `opus_speed/patches/<stack>.patch` (header lines ignored) | trial_w2, trial_w3, trial_w6, stack_w1src: 4 / 4 identical |
| 3 | QA's kit source differs from the patched tree only in the switch defaults | `diff -r src/trial_w2 packs/stack_w2/src_kit` | exactly 3 lines: SPEED2 0->1, NO_ZERO_MOVELISTS 0->2, TT_NOTLS 0->1 |
| 4 | The default build of every stacked tree is the lock | kit lp_v1 build with all switches at 0 | trial_w2 (w2off), trial_stack3, trial_w6 (w6off, 12:13): each = FD3A5190 byte for byte |
| 5 | TT_NOTLS cannot skip a needed lock under several threads | re-read the design (`jobb/b1_tt_notls.md`) against the patch | the owned path is taken only when this `Searcher::search` holds the exclusive lease AND runs one worker on that thread; helpers exist only without a lease and never set the flag; all other callers keep `lock_stripe` -> no change for Threads > 1 |
| 6 | ASan coverage of the PEXT sources | the L4 ASan of slider_pext / trial_w6 was N/A: the source's `#error` guard needs `__BMI2__`, which MSVC never defines | bitexact_check now passes `/D__BMI2__=1` to MSVC for sources that mention the macro (the lock source does not, so its cached reference is unchanged). L4-only re-runs 12:24-12:27: trial_w6 and b2_slider_pext both MSVC ASan bench 16 = 2587341 (= the lock source under MSVC ASan), 0 reports, and UBSan 3024920, 0 reports: PASS (`F:\ospd\packs\<pack>\bitexact_l4_bmi2\bitexact.log`; those two logs end with the old verdict text "BIT-EXACT (L1-L4; L3 on 0 FENs)" - they prove L4 only; an -OnlyL4 run now prints "VERDICT L4 PASS ... L1-L3 NOT run here") |
| 7 | Re-timing borderline results is not cherry-picking | each borderline single got ONE 16-round re-time; decisions use the pooled rounds (`abba_recheck.py --pool`) | see FINAL_REPORT section 3 |

Pending lines are filled in below as the runs finish.
