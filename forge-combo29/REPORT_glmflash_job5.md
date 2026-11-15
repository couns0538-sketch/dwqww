# REPORT_glmflash_job5 (glmflash, 2026-11-15)

1. **The middle point of the curve — packc28 on TOP of B1 on the old tree — was NOT measured: Step 0 failed. The two port patches conflict in `src/search.cpp` in BOTH orders (b1-then-packc28: 3 of 7 hunks FAILED; packc28-then-b1: 3 of 26 hunks FAILED; reject files committed; the job forbids hand-merging), so the double tree cannot even be built here and Part A (A1, A2) never ran. What Part B established instead: the Asp fail-high pair DOES carry gain by itself — pooled over job 4's 286-game cut and this job's B1m (2,132 games, 1,065 complete pairs): +15.34, my 95 % pair interval [5.5, 25.2]. And EvalSwing's second seed collapsed job 4's first reading: B2m alone +1.06 [-12.2, 14.4] (1,308 games), pooled with job 4's M2: +8.39 [-1.6, 18.4] — after two seeds the EvalSwing-only gain is NOT established, while the four options together stay at +18.83 [11.3, 26.4] (complete-pairs recount). Cut or not reached, first paragraph as asked: A1/A2 not reached (Step 0); B1m cut at 1,846 of 2,000; B2m cut at 1,308 of 2,000; C complete.**

## 2. Step 0: the double tree — FAILED, evidence committed
- Order 1 (b1 first, then packc28): b1 applied cleanly (7 files); packc28 on top: `Hunk #2 FAILED at 63, Hunk #3 FAILED at 98, Hunk #7 FAILED at 1416 — 3 out of 7 hunks FAILED -- saving rejects to file src/search.cpp.rej`. Reject file: `tests_glmflash_job5/step0/search_cpp_rej_packc28_on_top.txt` (the copy taken from the order-1 run).
- Order 2 (packc28 first, then b1): packc28 clean; b1 on top: `3 out of 26 hunks FAILED` (the tail shown included `Hunk #26 FAILED at 1644`), rejects at `src/search.cpp.rej` — committed as `tests_glmflash_job5/step0/search_cpp_rej_b1_on_top.txt`.
- No `.rej` anywhere else; the failing hunks are all in `src/search.cpp` — both patches rewrite overlapping search regions (the TT/history area). Per the job text I did NOT merge by hand; the double tree was never built and its bench numbers were never produced.
- The single-patch pins still hold on the reused packc28 build (verified in job 4: 312866 / 862329 / 4865609 OFF; 690187 four-options through wrapper).

## 3. Probes (before every match) and control
- **C's probe** (no options; the gate is Threads/Hash/OwnBook delivery + alive engines): `probes/probe_C_uci_in.log` + `probes/probe_C.out`; the driver stamps record `probe C pairshape=DEGENERATE (recorded, not a gate at 2 games)` — recorded, not failed: for a no-option probe the two games are identical engines and the degenerate pair is the EXPECTED outcome (that is the determinism property, not a fault).
- **B1m's probe**: `probes/probe_B1m_uci_in.log` — `setoption name AspFailHighReduce value 1` x2, `setoption name AspFailHighMaxReduce value 3` x2 (once per game), plus fastchess's Threads/Hash/OwnBook lines. Driver stamps: `probe B1m delivered: ... x2`, `probe OK B1m`. Its 2-game pair was [0,1,0,0,0] (cand lost as the non-mirror side) — divergent play, recorded.
- **B2m's probe**: `probes/probe_B2m_uci_in.log` — EvalSwing pair x2 each, `probe OK B2m`, probe pair [0,0,0,1,0].
- **Control C (sensitivity), 20,000 vs 10,000 nodes, no options, 300 games, seed 7150**: `C_last40.txt`: Elo 211.54 +/- 33.01, 188-25-87, Ptnml [0,4,34,57,55]; my Elo 211.54 [180.1, 246.4]. The tool sees large differences (third repetition of this control across jobs: 184.7, 189.3, 211.5 — all near +200).
- No "doesn't have option" warning in any of the three matches (stamps: warn counts 0).

## 4. Table: all packc28 matches of jobs 3, 4 and 5 (fixed 20,000 nodes; Hash 16 + Threads 1 both sides; OwnBook false in jobs 4-5)

| match | options on cand vs base | seed | games | W-L-D | Ptnml(0-2) | fastchess Elo +/- err | my Elo [pair interval, complete pairs] |
|---|---|---|---|---|---|---|---|
| M7 (j3) | four via wrapper vs none | 7132 | 2000 | 619-509-872 | [52,216,378,278,76] | 19.13 +/- 10.77 | 19.13 [8.4, 29.9] |
| C (j4) | nodes 20000 vs 10000 | 7140 | 300 | 169-20-111 | [0,1,39,70,40] | 189.31 +/- 27.55 | 189.31 [162.8, 218.0] |
| M1 (j4, INCOMPLETE) | four vs none | 7141 | 1991 of 2000 | 618-512-861 | [53,202,397,275,69] | 17.39 +/- 11.17 (block at 1800) | 18.52 [7.9, 29.1] |
| M2 (j4, INCOMPLETE) | EvalSwing pair vs none | 7142 | 887 of 2000 | 279-230-378 | [15,97,186,117,29] | 20.05 +/- 15.95 (block at 798) | 19.23 [4.1, 34.4] |
| M3 (j4, INCOMPLETE) | Asp pair vs none | 7143 | 286 of 2000 | 87-68-131 | [4,28,64,39,8] | 27.85 +/- 29.84 (block at 200) | 23.12 [-2.3, 48.7] |
| M4 (j4) | five vs four (both wrapped) | 7144 | 2000 | 572-564-864 | [56,231,412,251,50] | 1.39 +/- 10.25 | 1.39 [-8.9, 11.7] |
| C (j5) | nodes 20000 vs 10000 | 7150 | 300 | 188-25-87 | [0,4,34,57,55] | 211.54 +/- 33.01 | 211.54 [180.1, 246.4] |
| B1m (j5, INCOMPLETE) | Asp pair vs none | 7153 | 1846 of 2000 | 570-493-783 | [46,185,398,238,57] | 13.90 +/- 10.78 (block at 1800: B1m_last_block.txt) | 14.14 [3.5, 24.8] |
| B2m (j5, INCOMPLETE) | EvalSwing pair vs none | 7154 | 1308 of 2000 | 377-373-558 | [40,164,241,170,39] | 4.92 +/- 13.92 (block at 1200: B2m_last_block.txt) | 1.06 [-12.2, 14.4] |
| POOLED four (M7j3 + M1j4) | four vs none, 2 seeds | — | 3991 (1995 pairs) | 1237-1021-1733 | [105,417,775,553,145] | — | 18.83 [11.3, 26.4] |
| POOLED Asp pair (M3j4 + B1m) | Asp vs none, 2 seeds | — | 2132 (1065 pairs) | 657-561-914 | [50,213,460,277,65] | — | **15.34 [5.5, 25.2]** |
| POOLED EvalSwing (M2j4 + B2m) | EvalSwing vs none, 2 seeds | — | 2195 (1097 pairs) | 656-603-936 | [55,260,427,287,68] | — | 8.39 [-1.6, 18.4] |

W-L-D and pair counts: my PGN recounts (`pgn_to_gamelog.py`; logs committed as `{tag}j5_games.txt`), matching fastchess's blocks where the block covers the same games (C exact; B1m's block at 1800 of 1,846; B2m's at 1200 of 1,308). **Correction applied this job and stated plainly**: my earlier per-match Elo used EVERY round as a pair, including an incomplete end-round (a 1-game round entered the mean as a half-pair); from this job on the pair statistics use COMPLETE pairs only (rounds with exactly 2 games), with the dropped count shown. The four re-derived job-4 numbers above move by at most 0.1-0.2 Elo (M2j4: 19.21 -> 19.23; M1j4: 18.51 -> 18.52; the pools: 18.73 -> 18.83, Asp 15.31 -> 15.34, EvalSwing 8.23 -> 8.39); the committed `my_elo_job5.txt` shows both passes with a marker line between them. Job 2-4's committed files stay as they were (they are the record of what was reported then); the job-2/job-3 intervals Fable re-derived independently already agreed with the corrected method's outputs to 0.1.
- Crashes / illegal / disconnect: 0 in all three job-5 outputs (grep: no hits).

## 5. Step 4 (sanitizers)
Not part of job 5; not done.

## 6. Which files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash_5.md` only.
- The two patch files (b1, packc28) were REUSED from jobs 1-2 (/tmp copies); both `patch -p1` runs on fresh exports of d4f43124 produced the rejects. No new repository file opened this job; no FABLE_TO_deepseek file read; no other branch touched.

## 7. Start and end of each step (from tests_glmflash_job5/stamps.txt, UTC)
- 18:44 job 5 file read; 18:44-18:45 step 0: order-1 apply (3/7 hunks FAILED), rejects saved; order-2 apply (3/26 hunks FAILED), rejects saved; both orders' evidence committed.
- 18:45:28 driver 5 start; C probe 18:45:28-18:47:33, C match 18:47:33-18:49:18 (complete, 300 games); B1m probe 18:49:18-18:51:22 (PASS), match 18:51:22-19:07:37 (CUT at its 975 s limit, 1,846 games); B2m probe 19:07:37-19:09:42 (PASS), match 19:09:42-19:25:57 (CUT at the STOP deadline, 1,308 games); driver done 19:25:57.
- 19:26-19:38: recounts, the complete-pairs correction, pools, report, verification, commit. Within the job's 85-minute budget (the 75-minute stop line falls during report writing, after the matches ended).

## 8. What I did not do
- A1 and A2 (packc28 ON TOP of B1, the job's main question on this tree): not reached — the double tree cannot be assembled without a hand-merge, which the job forbids. The middle point of the curve therefore does not exist from me; the PC's own measurement of the switches on top of today's bundle is the only source for it.
- The combined bench "B1 AND the four packc28 options together" (the Step-0 new-report item): not run — it belongs to the double tree that does not exist.
- B1m is 154 games and B2m 692 games short of their 2,000 (both cut by their limits/deadline).
- No pull request; no engine source committed; no PGN committed; no other branches touched.

## 9. What I am not sure about
- **The two-seed disagreement inside packc28 is now the main open question**: EvalSwing alone read +19.2 [4.1, 34.4] on seed 7142 and +1.1 [-12.2, 14.4] on seed 7154; the Asp pair read +23.1 [-2.3, 48.7] on seed 7143 and +14.1 [3.5, 24.8] on seed 7153. Pooled: Asp +15.3 [5.5, 25.2] (established), EvalSwing +8.4 [-1.6, 18.4] (not established). Either single-idea attribution is unstable between seeds; the four-option sum is the stable quantity.
- Whether the Asp pair's gain is additive with EvalSwing's (pooled parts 15.3 + 8.4 = 23.7 vs the four-option pooled 18.8 — parts do not have to add; interactions are possible and untested on this tree).
- The exact overlap of the two port patches (which lines of search.cpp both rewrite): the reject files show the hunk positions, not a merged reading; the merge difficulty is Fable's to judge from the rejects.

## 10. A better way
- **Check patch OVERLAP before ordering patches**: `grep '^+++ ' b1_port.patch packc28_port.patch` shows both touch `src/search.cpp` before anything is exported — five seconds that would have predicted this job's Step-0 failure. If two patches touch the same file, a double-tree job needs either a combined patch from the patch author or an explicit "expect conflict" plan.
- **The middle point may not need the old tree at all.** The PC already plays packc28's switches on top of today's bundle (your file 4 says so); the old-tree double measurement would only corroborate. If the PC number at 20,000-node equivalents exists there, this job's Part A is redundant — I would rather spend my next budget completing the parts matrix (Asp pair at a third seed) than re-fighting the merge.
- **Complete-pairs-only statistics from now on** (the correction in section 4): a 1-game end-round entered my earlier means as a half-pair. The fix is one filter line; the differences are tiny but the method is now exact and stated.
- Probe cost remains ~2 minutes each (opening-file indexing dominates); three probes this job ≈ 6 minutes. Same flag as job 4 — a probe book slice would return most of it.

## Questions for Fable
- The Asp pair is now the strongest pooled single idea (+15.3 [5.5, 25.2]) yet job 4's single seed read it weakest. Do you want a third Asp seed to lock it, or does the pooled interval suffice for the port decision on the new tree?
- EvalSwing: two seeds, pooled not established. Do you still port it (it is inside the four-option +18.8 which IS established), or does it need a third seed to earn its place?
- For the middle point: is the PC's 20,000-node measurement of packc28-on-top-of-bundle the intended replacement for my Part A, or do you want the old-tree double patch re-ported cleanly (a combined patch from you) and measured here?
