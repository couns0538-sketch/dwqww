# Forge speed job - STATUS

Owner Couns. Job window 2026-11-05 08:38 -> 14:38 (PC clock = Vienna time); FINAL_REPORT due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Plan: `opus_speed/PLAN.md`. Scratch `F:\ospd\` (<= 8 GB).
Lock: exe FD3A5190 (`forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`), source = exact copy `F:\ospd\src\lock` (20 files):
the job's reference and the search-identity pins. **Live lock since QA's publish: trial_w6, sha256
4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0** (`F:\ospd\packs\trial_w6\forge_trial_w6.exe` = these
bytes); every lock decision is against trial_w6.
Session restart at ~09:32 (application restart by the owner); workers resumed 09:35; jobs started before it kept running.

| job | state | candidates | last update |
|---|---|---|---|
| CR 637B (owner, done first after the restart) | DONE except the 3 LOW notes (note file not on the PC): BLOCKER pin DIFF fail-closed, SHOULD 1-3, test 13/13 PASS (be0e4e37); report `CR_637B_REPORT.md` | - | 09:47 |
| A speed-only lock path (tools) | DONE: tools + tests (re-run 13:18-13:23: CR 13/13, move-order mutant 3/3) (kit self-test, test 1 lock-vs-lock pack inside the A/A band, test 2 mutant, test 3 lp_part1 full pack NO-WIN, CR 13/13, move-order mutant 3/3); variant screen complete (no flag beats the lock recipe; net-off PGO workload -29 %); independent review: no BLOCKER, SHOULD 1-4 + LOW 1-11 fixed (REVIEW_FIXES.md); protocol verdict = wall (cpu advisory) | var_lp_part1, locklock_v1c | 12:08 |
| B bit-exact hot-path changes | DONE. Protocol = wall nps. Winners: NZM2 +3.6 % (NZM1 +3.3 %), SPEED2 +3.2 %; on 26 pooled rounds TT_NOTLS +2.9 %, SLIDER_PEXT +1.5 %, PREFETCH_EARLY +1.4 %, NNUE_ZMM +1.4 % (weak: re-time alone and pooled cpu NO-WIN); losers PICKBEST 1/2, MATKEY_FAST. Stacks vs lock (own session each, all WIN, all bit-exact incl. full 12k, all rebuilt byte for byte by QA's kit): stack_w1 +7.31 %, stack_w2 +11.48 % (QA first), stack_w3 +11.42 %, stack_w4 +12.04 %, stack_w5 +11.94 % (all but ZMM), trial_w6 +14.92 % (all six = largest winners-only stack, QA second); direct trial_w6 vs stack_w2 in one session +4.39 % WIN. Independent patch review: no BLOCKER / SHOULD, 5 LOW. Warm-table identity (1,000 searches, 40 option changes, no ucinewgame): all six stacks IDENTICAL to the lock; QA kit rebuilds all six byte for byte; 0 FMA | stack_w2, then trial_w6 (or stack_w5) | 13:36 |
| C gate wall time | DONE 09:59 (worker jobc): 7 tools in opus_speed/jobc/tools, README + RESULTS; tests ALL PASS (13/13 gate replays = recorded verdict, 18/18 corrupt / truncated PGNs -> error, 111-row formula check); coordinator re-run 10:01 ALL PASS (jobc/results/tests_20261105_100109_coordinator_rerun.md) | - | 10:03 |
| D net pipeline | DONE 11:54 (worker jobd, plans + read-only log tools only, no GPU): opus_speed/jobd/PLAN.md; D1 owner item (coordinator re-checked): the GPU guard drops HWiNFO rows with a one-digit day since 2026-11-01 and throttles on the ADLX fallback (run_frac 0.33-0.64 vs 0.90-1.00 in October); D2 RAM-floor aborts repeat epochs | - | 12:08 |

FINAL_REPORT.md: FINAL 13:36 (all runs finished). QA order: stack_w2 first, then trial_w6 or stack_w5.

CR leftovers (independent CR of 73f4041d..00d19e56: APPROVE, 0 BLOCKER, 4 SHOULD), 19:43-19:47 PC clock, start tip
00d19e56, WIP 8b170996: all 4 DONE. SHOULD 4: patchrev_qa LOCK = trial_w6. SHOULD 2: skill verdict rules. SHOULD 3:
FINAL_REPORT QA owner item. SHOULD 1: warm_identity self-pin + read-back. Test 8 / 8 PASS (run
20261105-194720-5676). KING_LINES (W9) and bundles a-d were not retimed or locked. Details: `CR_SHOULD_W8.md`.

Leftover jobs 1-3 (owner brief, from 19:5x PC clock, start tip 38559f1b; live lock trial_w6 4181A589...):
- Job 1 (tool defaults = trial_w6): DONE 20:02.
- Job 2 (warm_identity refusal test): DONE 20:03. Fault injection `tests/warm_refusal_check.py`, W5a-e; test 14 / 14
  PASS (run 20261105-200352-9252).
- Job 3 (CR NITs): DONE 20:07.
  - 3a: patchrev_qa takes the timing mutex before it moves onto the mask.
  - 3b: K3 comment at `is_legal` in the trial_w9 / w9dev board.hpp. The patches were regenerated (trial_w9 8bf44bab,
    b4 d680f9bf); the apply proofs are identical.
  - 3c: the test takes `-Py` / OSPD_PY and fails closed without one.
  - Test 14 / 14 PASS (run 20261105-200713-5164).
KING_LINES and bundles a-d were not retimed or locked.
