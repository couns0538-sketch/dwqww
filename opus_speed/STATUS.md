# Forge speed job - STATUS

Owner Couns. Job window 2026-11-05 08:38 -> 14:38 (PC clock = Vienna time); FINAL_REPORT due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Plan: `opus_speed/PLAN.md`. Scratch `F:\ospd\` (<= 8 GB).
Lock: exe FD3A5190 (`forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`), source = exact copy `F:\ospd\src\lock` (20 files):
the job's reference and the search-identity pins. **Live lock since QA's publish: trial_w6, sha256
4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0** (`F:\ospd\packs\trial_w6\forge_trial_w6.exe` = these
bytes); every lock decision is against trial_w6.
Session restart at ~09:32 (application restart by the owner); workers resumed 09:35; jobs started before it kept running.

## 2026-11-06 5-hour brief: jobs 2-4 (pointers; each pack has its own STATUS.md)
- **Job 2, int8 VNNI:** DONE through 2e. Branch `opus-nnue-int8-vnni-20261106`, tip 84489e36.
  - Identity lp_v1 = 4181a589 (pc1 = pc2). Gate 81741f2b: ON d16 3282449.
  - CR / QA item: the gate's PGO workload trains OFF only, so the ON path is cold (see BENCH.md).
- **Job 3, TtReplaceCache:** DONE. Branch `opus-tt-replace-cache-20261106`, tip 87bf3c7e.
  - Identity = 4181a589. Gate ec1cb55e: ON node-identical.
- **Job 4, KING_LINES on trial_w6: DONE** (owner follow-up, 17:1x-18:10 PC clock). Branch `opus-king-lines-20261106`,
  tip c228b7c5, pack `opus_king_lines/`.
  - Source: the committed b4 patch d680f9bf on trial_w6, clean.
  - OFF build = 4181a589 (pc1 = pc2). ON build 44fd0137 (pc1 = pc2): all pins + perft.
  - Full 12k BIT-EXACT, net on and net off.
  - Net-off step on C: (owner), because F: fell below its 50 GB floor from other jobs.
  - Not a lock: L3b warm_identity, the Threads 2-4 soak and the ABBA are left to QA.

## 2026-11-06 runner audit (owner 5-hour brief, job 1) - DONE 16:42 PC clock; hand to Code Review
- **Done:**
  - `opus_speed/tools/bitexact_check.ps1` = CR-approved 4d1c8d52 on all four tips (tools-only commits):
    - speed deefef64 (was 5038452d)
    - cnl 0e796eb2 (was f382cdc2)
    - tcn 8b7b728e (was f382cdc2)
    - ntc a8f00c42 (was f382cdc2)
  - Resume proof: 22 cases, see `logs/RESUME_LEDGER.md`.
    - Required REJECT 17 / 17 with the expected guard text; controls ACCEPT 3 / 3.
    - Ledger total: 18 REJECT, 4 ACCEPT.
    - Extra probe X1 (`11999 / 12000 ... PASS`, hand-edited) is ACCEPTED: a CR finding, no guard (not a required case).
    - No guard was added, so the shipped md5 = 4d1c8d52 everywhere.
  - New tool `tools/resume_cases.sh` (makes the cases, runs the shipped runner with -ResumeFrom -SkipSan).
- **In progress:** none.
- **Exact next step:** Code Review of the deploy plus ledger findings 2-5. QA owns any queue use. Nothing was queued.
- **Resume / re-check:** `bash opus_speed/tools/resume_cases.sh D:/opus_5h/runner_audit_rerun` (writes a new folder only).
- **Unproven / not claimed:**
  - k == n is not checked on resume (X1).
  - The case-insensitive option compare was not tested.
  - Not tested: resume for a -Quick prior (it reports "= quick subset").

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
| H7 | large pages mode 2: TT + net weights w1 (768 KB) + one block per worker for the six history / correction tables (1.68 MB) | FORGE_SPD_LARGEPAGES=2 | new header large_pages.hpp holds the switch; identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 22:05 (L1 net on + net off = pins, L2, L3 2,000, L4) | only if large pages can be had (runner v3 abba_lp) | | 344e6113 (pc1 = pc2) | pending |
| H8 | evaluate_pieces accumulates attacked_by / attacked_twice / king-attack counters in locals (the lock build had memory RMW chains) | FORGE_SPD_HCE_LOCALS=1 | harness: switch 0 and 1 give the same HCE (1.58M evaluations incl. traced coefficients, hash 6ff95740; mutant changes it); identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 22:11 (L1 net on + net off = pins, L2, L3 2,000, L4) | queued (runner v3) | | 89ac3f1f (pc1 = pc2) | pending ABBA |
| H9 | piece_type() by arithmetic (p > 6 ? p - 6 : p) instead of SPEED2's 16-entry table load | FORGE_SPD_PTYPE_ARITH=1 | compile-time static_assert: equal to the table for all 13 Piece values; identity all-0 = FD3A5190 OK, six ON + new OFF = 4181A589 OK; BIT-EXACT 22:18 (L1 net on + net off = pins, L2, L3 2,000, L4) | queued (runner v3) | | 96004e91 (pc1 = pc2) | pending ABBA |
| - | session A/A 3 trial_w6 vs itself (21:34-21:39) | - | - | 0.9924 [0.9683, 1.0081] sd 2.82 %, per-round range 8.36 % | 0.9902 [0.9703, 1.0010] sd 2.17 % | 4181a589 | NOT SANE: CPU 2 71-79 % and CPU 3 62-67 % busy before / after the run; the live trainer restarted 21:39:04 (new PID 9380, Idle, 0xF, ~190-200 % CPU) - not touched. Timing moved behind the H5-H9 CPU steps; A/A 4 first, A/A 5 brackets the block |
| - | session A/A 4a (22:18-22:24, gate try 1) | - | - | 0.9982 [0.9735, 1.0191] sd 3.20 %, per-round range 11.34 % | 0.9966 [0.9815, 1.0133] sd 2.23 % | 4181a589 | NOT SANE: the trainer stopped ~22:19 (CPU 2 / 3 at 3 / 5 % at the start) and came back mid-run at ~190-200 % (new PIDs); the gate waits 8 min and tries again |
| - | session A/A 4b (22:32-22:37, gate try 2) | - | - | 0.9898 [0.9624, 1.0094] sd 3.33 %, per-round range 12.58 % | 0.9957 [0.9579, 1.0096] sd 3.67 % | 4181a589 | NOT SANE with the trainer steady at ~190-220 % (no restart in the run): the current trainer regime itself makes CPU 2 timing noisy (~3 % / round) |

### Quiet window (QA update, Couns-approved, received 22:57 PC clock): NNUE training, gates and self-play paused for this hunt
CPUs 0-6 + GPU free for the hunt until usage runs out. Timing stays on CPU 2 with its SMT sibling CPU 3 idle (one
ABBA at a time, no other own load beside it), strict protocol (d20, 10 rounds, A/A gate with the normal rule first).
Large pages: probe 6 / 6 OK at 22:57 (0.19-2.5 ms) -> H1 / H7 get timed (probe repeated right before each). "DONE-QUIET"
is written here when the hunt ends or usage is nearly out, so QA restarts production.
| - | H2 run 1 (22:51-22:56, before the pause took effect: cpu2 / 3 78 / 72 % at the start) | - | - | 1.0048 [0.9784, 1.0271] sd 3.39 % | 1.0047 [0.9946, 1.0248] sd 2.09 % | 8c3f2747 | information (taken next to a failed A/A); runs.csv 77ccf5f5 |
| - | H3 run 1 (22:56-23:01, quiet PC: total load 1-4 %, before the quiet A/A gate) | - | - | 1.0057 [0.9862, 1.0120] sd 1.80 % | 1.0048 [0.9835, 1.0119] sd 1.99 % | 9bcdef73 | NO-WIN / NO-WIN (information: before the gate); runs.csv d4df0016 |
| - | quiet A/A qa (23:01-23:06, gate try 1; total load 2-8 %) | - | - | 1.0003 [0.9919, 1.0175] sd 1.78 %, per-round range 6.50 % (interval width 2.56 %) | 1.0000 [0.9909, 1.0154] sd 1.71 % | 4181a589 | NOT SANE by the per-round-range reading, SANE by the interval-width reading (see FINAL_REPORT 9.3): the protocol's fresh copies per round give ~1.8 % / round even on the quiet PC |
QA rule (received 23:14 PC clock): A/A SANE = |median| <= 0.5 % and width of its 95 % interval <= 4.0 % (per-round spread =
information only); candidate WIN only if its 95 % interval lies fully above 1.000 AND its median gain beats the A/A
width / 2 (`tools/aa_sane.py`, `tools/qa_verdict.py`, wall = verdict, the same test on cpu must not contradict).
Under it: A/A 1-4c NOT SANE (median or width), quiet A/A qa SANE (+0.03 %, width 2.56 %), qb SANE (+0.18 %, width 1.92 %);
H1 run 1, H2 run 1, H3 run 1 NO-WIN (information, before the quiet gate).
| - | quiet A/A qb (23:08-23:13, gate try 2) | - | - | 1.0018 [0.9920, 1.0112] sd 1.34 %, width 1.92 % (spread 4.23 %) | 1.0019 [0.9918, 1.0129] | 4181a589 | SANE by the QA rule (its gate check ran on the old reading; qc runs anyway) |
| - | quiet A/A qc (23:15-23:20, gate try 3) | - | - | 1.0003 [0.9891, 1.0082] sd 1.34 %, width 1.91 % | (see summary) | 4181a589 | SANE (QA rule) -> gate open; the band of the quiet decision block (WIN needs low > 1.000 and gain > 0.96 %) |
| H2 | h2_dirty_inplace quiet decision run (23:20-23:25, cpu2 / cpu3 2 / 1 -> 1 / 1 %) | - | BIT-EXACT (pack) | 1.0053 (+0.53 %) [1.0006, 1.0151] sd 1.01 % | 1.0019 (+0.19 %) [0.9981, 1.0135] sd 1.07 % | 8c3f2747 | NO-WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN; runs.csv 832eaf3b |
| H3 | h3_nnue_columns quiet decision run (23:25-23:30, cpu2 / cpu3 3 / 1 -> 0 / 1 %) | - | BIT-EXACT (pack) | 1.0081 (+0.81 %) [1.0009, 1.0262] sd 1.74 % | 1.0086 (+0.86 %) [1.0017, 1.0254] sd 1.64 % | 9bcdef73 | NO-WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN; runs.csv e8c5ead1 |
| H6 | h6_pick_first quiet decision run (23:30-23:35, cpu2 / cpu3 1 / 0 -> 3 / 0 %) | - | BIT-EXACT (pack) | 1.0060 (+0.60 %) [0.9994, 1.0248] sd 1.75 % | 1.0067 (+0.67 %) [0.9969, 1.0259] sd 2.00 % | 921d1cf7 | NO-WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN; runs.csv 77befd39 |
| H5 | h5_move_store32 quiet decision run (23:35-23:40, cpu2 / cpu3 2 / 0 -> 1 / 0 %) | - | BIT-EXACT (pack) | 1.0121 (+1.21 %) [1.0024, 1.0194] sd 1.18 % | 1.0125 (+1.25 %) [1.0033, 1.0213] sd 1.25 % | 5dec3fa7 | WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall WIN / cpu WIN; runs.csv 552ea065 |
| H8 | h8_hce_locals quiet decision run (23:40-23:45, cpu2 / cpu3 1 / 0 -> 1 / 0 %) | - | BIT-EXACT (pack) | 0.9984 (-0.16 %) [0.9919, 1.0039] sd 0.84 % | 0.9962 (-0.38 %) [0.9901, 1.0009] sd 0.75 % | 89ac3f1f | NO-WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN; runs.csv f682fd21 |
| H9 | h9_ptype_arith quiet decision run (23:45-23:50, cpu2 / cpu3 1 / 0 -> 1 / 1 %) | - | BIT-EXACT (pack) | 0.9990 (-0.10 %) [0.9715, 1.0178] sd 3.25 % | 0.9962 (-0.38 %) [0.9702, 1.0154] sd 3.18 % | 96004e91 | NO-WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN; runs.csv e6ae0763 |
| H4 | h4_slider_pdep16 quiet decision run (23:50-23:55, cpu2 / cpu3 1 / 0 -> 86 / 48 %) | - | BIT-EXACT (pack) | 0.9990 (-0.10 %) [0.9914, 1.0206] sd 2.02 % | 1.0000 (+0.00 %) [0.9919, 1.0207] sd 2.00 % | dcc1e022 | NO-WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN; runs.csv a903cfb0 |
| H1 | h1_largepages quiet decision run (23:55-00:00, cpu2 / cpu3 88 / 54 -> 86 / 48 %) | - | BIT-EXACT (pack) | 1.0160 (+1.60 %) [1.0069, 1.0300] sd 1.59 % | 1.0174 (+1.74 %) [1.0067, 1.0311] sd 1.68 % | cecc4d92 | WIN - QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall WIN / cpu WIN; runs.csv 9bdf200f |
H1 note: its run (23:55-00:00) lay entirely inside the trainer's return (PID 11564 started 23:54:38 by itself, Idle 0xF,
~210 % CPU; CPU 3 at 48-62 %) and large pages failed partway (round ratios 1.019-1.057 in rounds 1-5, 0.997-1.013 in
rounds 6-10; the probe right after: 6 / 6 failed with 1450). Its WIN on paper is NOT a valid quiet decision: a quiet
re-time with large pages available is owed to QA. H4's run ended ~30 s after the trainer came back.

**DONE-QUIET (00:01 PC clock):** the timing that needs a quiet PC is finished (quiet A/As qa / qb / qc SANE; decision runs H2,
H3, H6, H5, H8, H9, H4 clean; H7 skipped: large pages failed 6 / 6 at its probe). The NNUE trainer is already running again
(restarted 23:54:38 on its own). QA may restart gates and self-play now. Still running from here, on CPUs 0-3 only as all
day: the closing A/A q2 (CPU 2, under load: information) and the full 12k L3 proof of the screening WIN H5 (CPUs 0-1 Idle).

### Final table of the hunt (decision = the quiet run vs trial_w6, band A/A qc, QA rule: interval fully above 1.000 and median gain > 0.96 %)
| # | idea | define | bit-exact net on / net off | wall vs trial_w6 | cpu vs trial_w6 | exe sha256 | verdict |
|---|---|---|---|---|---|---|---|
| H1 | TT in 2 MB pages | FORGE_SPD_LARGEPAGES=1 | BIT-EXACT incl. full 12k (12,000 / 12,000, 00:30) | -0.19 % [0.9741, 1.0104] (second quiet window, A/A ra band; large pages available before and after the run: verify copy LARGE + probe 6 / 6 on both sides); the 23:55 run (+1.60 %) was under the returned trainer and does not stand | -0.27 % [0.9749, 1.0111] | cecc4d92 | NO-WIN |
| H2 | record_move writes the dirty pieces in place | FORGE_SPD_DIRTY_INPLACE=1 | BIT-EXACT | +0.53 % [1.0006, 1.0151] | +0.19 % [0.9981, 1.0135] | 8c3f2747 | NO-WIN |
| H3 | net update columns by integer arithmetic | FORGE_SPD_NNUE_COLUMNS=1 | BIT-EXACT | +0.81 % [1.0009, 1.0262] | +0.86 % [1.0017, 1.0254] | 9bcdef73 | NO-WIN |
| H4 | 16-bit slider entries + PDEP | FORGE_SPD_SLIDER_PDEP16=1 | BIT-EXACT | -0.10 % [0.9914, 1.0206] (quiet except its last ~30 s: the trainer returned 23:54:38) | +0.00 % [0.9919, 1.0207] | dcc1e022 | NO-WIN |
| H5 | one 32-bit store per generated move | FORGE_SPD_MOVE_STORE32=1 | BIT-EXACT incl. full 12k (12,000 / 12,000, 00:23) | **+1.21 % [1.0024, 1.0194]** | +1.25 % [1.0033, 1.0213] | 5dec3fa7 | **screening WIN** |
| H6 | first pick from the scoring pass | FORGE_SPD_PICK_FIRST=1 | BIT-EXACT | +0.60 % [0.9994, 1.0248] | +0.67 % [0.9969, 1.0259] | 921d1cf7 | NO-WIN |
| H7 | large pages mode 2 (TT + w1 + worker tables) | FORGE_SPD_LARGEPAGES=2 | BIT-EXACT | +0.61 % [1.0006, 1.0227] (second quiet window, A/A ra band; large-page gate passed right before; not re-checked after) | +0.76 % [1.0000, 1.0228] | 344e6113 | NO-WIN (interval above 1.000, median under 0.73 %) |
| H8 | HCE piece-loop accumulators in locals | FORGE_SPD_HCE_LOCALS=1 | BIT-EXACT | -0.16 % [0.9919, 1.0039] | -0.38 % [0.9901, 1.0009] | 89ac3f1f | NO-WIN |
| H9 | piece_type by arithmetic | FORGE_SPD_PTYPE_ARITH=1 | BIT-EXACT | -0.10 % [0.9715, 1.0178] | -0.38 % [0.9702, 1.0154] | 96004e91 | NO-WIN |
No idea changed the search (all nine packs BIT-EXACT vs trial_w6 with the net on and off). H2 and H3 have intervals fully above
1.000 with medians +0.53 % and +0.81 %: by the skill's definition neither is borderline (median < 1 %, no cpu WIN), so no
re-time was run; QA may choose to. One screening WIN (H5) - no
stack (the brief stacks winners only; one winner needs none). H1 / H7 were re-timed in the second quiet
window with large pages proven available (probe + verify copy) - the first H1 run had invalid conditions. Nothing locked or published; QA re-times.
| - | closing A/A q2 (00:00-00:05, trainer back: cpu2 / 3 87 / 49 -> 78 / 56 %) | - | - | 1.0074 [0.9944, 1.0184] sd 1.67 %, width 2.40 % | - | 4181a589 | NOT SANE (median +0.74 % > 0.5 %): confirms the conditions of H1's run were not the quiet ones |

### Second quiet window (user, 00:21 PC clock: "cpu 0-6 and training is off again ... use them")
Trainer stopped ~00:19 (sampler: 0 %, no processes). Large pages available again (probe 6 / 6 OK; the LP verify copy
gets LARGE for the 32 MB UCI table and the 16 MB bench table). Runner v4 times on CPU 2 (CPU 3 idle) while runner v3's
full 12k proofs run on CPUs 0-1 (core 0): A/A gate r (same conditions), then H1 and H7 decision runs, each only after a
probe 6 / 6 OK and a verify run with every allocation LARGE, then a closing A/A. The GPU has no role in CPU engine
timing. DONE-QUIET is written again when this block ends.
| - | A/A ra (00:21-00:26, second quiet window; runner v3's full 12k on CPUs 0-1 throughout) | - | - | 0.9971 [0.9853, 0.9999] sd 1.03 %, width 1.46 % | - | 4181a589 | SANE (QA rule) -> band of the second block (WIN needs low > 1.000 and gain > 0.73 %) |
| H1 | h1_largepages quiet decision run (00:26-00:31, cpu2 / cpu3 1 / 1 -> 1 / 0 %) | - | BIT-EXACT (pack) | 0.9981 (-0.19 %) [0.9741, 1.0104] sd 2.56 % | 0.9973 (-0.27 %) [0.9749, 1.0111] sd 2.55 % | cecc4d92 | NO-WIN - QA rule vs aa_w6_d20_ra (need low > 1.000, gain > 0.73 %): wall NO-WIN / cpu NO-WIN; runs.csv 57453ffb |
| H7 | h7_largepages2 quiet decision run (00:31-00:36, cpu2 / cpu3 4 / 1 -> 0 / 1 %) | - | BIT-EXACT (pack) | 1.0061 (+0.61 %) [1.0006, 1.0227] sd 1.53 % | 1.0076 (+0.76 %) [1.0000, 1.0228] sd 1.57 % | 344e6113 | NO-WIN - QA rule vs aa_w6_d20_ra (need low > 1.000, gain > 0.73 %): wall NO-WIN / cpu NO-WIN; runs.csv 39146413 |
| - | closing A/A r2 (00:36-00:41) | - | - | 1.0020 [0.9913, 1.0196] sd 1.97 %, width 2.83 % | - | 4181a589 | SANE (QA rule): the second block (H1, H7) is bracketed by two sane A/As |

**DONE-QUIET (00:41 PC clock, final):** all timing is finished (second quiet window: A/A ra SANE, H1 and H7 decision runs,
A/A r2 SANE); runners v3 and v4 have stopped; no own engine, build or check is running. QA may restart NNUE training,
gates and self-play now. Result: one screening WIN, H5 FORGE_SPD_MOVE_STORE32 (+1.21 % wall / +1.25 % cpu vs trial_w6,
BIT-EXACT incl. the full 12k); everything else NO-WIN; nothing locked or published. Owed to QA for H5 before any
lock: QA's own re-time vs trial_w6, L3b warm_identity, Threads 2-4 soak.
