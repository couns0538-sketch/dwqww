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
- Bug-hunt pass 20:08-20:10 (own): one whitespace glitch fixed (`CYCLE =[` in warm_identity.py); re-run 14 / 14 PASS
  (20261105-200930-9164). Two LOWs left as notes (`CR_SHOULD_W8.md`). Jobs 1, 2, 3a, 3b, 3c are all done.
- Extras 20:12-20:15:
  - pin_check of the default lock exe trial_w6: PASS (d11-d22 + perft5 = the pin tables).
  - test_stack_poison.ps1 takes `-Py`.
  - Skill rows added.
  - test_cr_637b re-run: 13 / 13 PASS (20261105-201312-4460; o3 builds, no ABBA). Details in `CR_SHOULD_W8.md`.
  - Nothing of the job is running.
KING_LINES and bundles a-d were not retimed or locked.

## Hunt vs the live lock trial_w6 (owner /plan brief, from 2026-11-05 20:41 PC clock; plan `PLAN_HUNT.md`)
Start tip 3ca407b3. One new bit-exact switch per idea on top of trial_w6 (six switches ON), timed against trial_w6
(4181A589..., `forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`) by wall nps (d20, 10 rounds ABBA/BAAB, CPU 2).
Screening only: nothing is locked or published; QA re-times. Hunt scratch `C:\ospd_hunt\` (ABBA, identity builds,
profiles); packs stay in `F:\ospd\packs\h<N>_*`.

| # | idea | define | bit-exact net on / net off | wall vs trial_w6 | cpu vs trial_w6 | exe sha256 | verdict |
|---|---|---|---|---|---|---|---|
| - | session A/A 1 trial_w6 vs itself (20:42-20:47) | - | - | 0.9961 [0.9730, 1.0319] sd 4.10 %, per-round range 11.7 % | 0.9995 [0.9825, 1.0225] sd 2.79 % | 4181a589 | NOT SANE (range > 4 %): live trainer PID 3940 (Idle, 0xF, ~73 % of a CPU) shares CPUs 2-3; re-run before any decision |
| H1 | TT in 2 MB pages (silent fallback to the lock's allocation) | FORGE_SPD_LARGEPAGES=1 | identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 21:04: L1 net on d11-d22 + net off d11-d22 = pins, L2 perft, L3 2,000 / 2,000, L4 ASan + UBSan | run 1 (21:39-21:45, CPU 2 / 3 at 72-100 %, trainer restart): 1.0139 [0.9886, 1.0304] sd 2.90 % NO-WIN; runs.csv b9d82cba | 1.0104 [0.9891, 1.0183] NO-WIN | cecc4d92 (pc1 = pc2) | run 1 measured the 4 KB FALLBACK (large pages failed with error 1450 in 5 / 5 abba-pattern processes at 21:51): not a large-page result; the re-time runs only if the probe succeeds (runner v3 abba_lp) |
| H2 | record_move writes the dirty pieces in place (no wide reload of fresh narrow stores) | FORGE_SPD_DIRTY_INPLACE=1 | harness 18.9M moves 0 mismatches (mutant FAIL); identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 21:12 (L1 net on + net off = pins, L2, L3 2,000, L4); the built exe has no wide reload left in search / record_move | queued (timing block) | | 8c3f2747 (pc1 = pc2) | pending ABBA |
| H3 | net update takes both perspectives' columns from integer arithmetic (no byte spill reloaded as qword) | FORGE_SPD_NNUE_COLUMNS=1 | harness 2.03M updates = refresh() byte for byte (mutant FAIL); identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 21:20 (L1 net on + net off = pins, L2, L3 2,000, L4) | queued (timing block) | | 9bcdef73 (pc1 = pc2) | pending ABBA |
| H4 | slider entries as 16 bits (PEXT over the empty-board rays), rebuilt with PDEP (rook table 800 -> 200 KB) | FORGE_SPD_SLIDER_PDEP16=1 | harness 4.43M lookups = ray walk (mutant FAIL); identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 21:33 (L1 net on + net off = pins, L2, L3 2,000, L4) | queued (timing block) | | dcc1e022 (pc1 = pc2) | pending ABBA |
| H5 | the move generator writes each Move with one 32-bit store (the picker's 32-bit reloads can forward) | FORGE_SPD_MOVE_STORE32=1 | harness: switch 0 and 1 give the same lists (4.75M lists, 106.5M moves, hash 730f33eb; mutant changes it); identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 21:52 (L1 net on + net off = pins, L2, L3 2,000, L4) | queued (runner v3) | | 5dec3fa7 (pc1 = pc2) | pending ABBA |
| H6 | the scoring pass remembers the first maximum; the first pick of a list takes it instead of scanning | FORGE_SPD_PICK_FIRST=1 | verify build (scan run next to it at every first pick): bench 13 / 16 = pins, 1,732,892 first picks, 0 mismatches; identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 21:58 (L1 net on + net off = pins, L2, L3 2,000, L4) | queued (runner v3) | | 921d1cf7 (pc1 = pc2) | pending ABBA |
| - | session A/A 2 trial_w6 vs itself (21:20-21:26) | - | - | 0.9945 [0.9828, 1.0026] sd 1.40 %, per-round range 4.32 % | 0.9968 [0.9891, 1.0022] sd 0.92 % | 4181a589 | median sane, range just over 4.0 % (one round 0.9657): A/A 3 runs before the ABBAs |
| H7 | large pages mode 2: TT + net weights w1 (768 KB) + one block per worker for the six history / correction tables (1.68 MB) | FORGE_SPD_LARGEPAGES=2 | tree ready (new header large_pages.hpp holds the switch); queued | | | | pending |
| H8 | evaluate_pieces accumulates attacked_by / attacked_twice / king-attack counters in locals (the lock build had memory RMW chains) | FORGE_SPD_HCE_LOCALS=1 | harness: switch 0 and 1 give the same HCE (1.58M evaluations incl. traced coefficients, hash 6ff95740; mutant changes it); queued | | | | pending |
| H9 | piece_type() by arithmetic (p > 6 ? p - 6 : p) instead of SPEED2's 16-entry table load | FORGE_SPD_PTYPE_ARITH=1 | compile-time static_assert: equal to the table for all 13 Piece values; tree ready, queued | | | | pending |
| - | session A/A 3 trial_w6 vs itself (21:34-21:39) | - | - | 0.9924 [0.9683, 1.0081] sd 2.82 %, per-round range 8.36 % | 0.9902 [0.9703, 1.0010] sd 2.17 % | 4181a589 | NOT SANE: CPU 2 71-79 % and CPU 3 62-67 % busy before / after the run; the live trainer restarted 21:39:04 (new PID 9380, Idle, 0xF, ~190-200 % CPU) - not touched. Timing moved behind the H5-H9 CPU steps; A/A 4 first, A/A 5 brackets the block |
