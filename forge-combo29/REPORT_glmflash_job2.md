# REPORT_glmflash_job2 (glmflash, 2026-11-15)

1. **HistRework 2 carries the bundle's gain: +21.82 Elo over 1,499 games, my pair interval [9.2, 34.0] (fastchess at its 1,400-game block: +21.62 +/- 12.78) — clearly the largest single part; TtPruneV2 = 0.00 [-12.2, 12.2], CuckooRep = +3.47 [-8.4, 15.3] (both consistent with 0). bnd68 and packc28: NOT ESTABLISHED — their matches are invalid, because the two ports never declare their new options in the `uci` reply, fastchess refuses to send undeclared options ("Warning; cand doesn't have option ..."), and both matches degenerated to identical-engine play (Ptnml [0,0,N,0,0], Elo 0.00 +/- 0.00). The engines DO honor the options when the lines are sent directly — all six bnd68 and all four packc28 bench pins matched the job's expected values — so the ports work; only their UCI option listing is missing, and until that is fixed they cannot be measured in fastchess at all.**

## 2. Step 1: known numbers — ALL MATCH (fresh engine process per line; raw outputs in tests_glmflash_job2/step1/)

| build | setup | expected | printed | file |
|---|---|---|---|---|
| B1 (job 1 build, reused) | no option, bench 11 | 312866 | 312866 | (re-verified live; same pins as job 1) |
| B1 | no option, bench 13 | 862329 | 862329 | (re-verified live) |
| B1 | no option, go perft 5 | 4865609 | 4865609 | (re-verified live) |
| bnd68 | no option, bench 11 | 312866 | 312866 | step1/bnd68_off_b11.txt |
| bnd68 | no option, bench 13 | 862329 | 862329 | step1/bnd68_off_b13.txt |
| bnd68 | no option, go perft 5 | 4865609 | 4865609 | step1/bnd68_off_perft.txt |
| bnd68 | its six options, bench 11 | 365135 | 365135 | step1/bnd68_on.txt |
| bnd68 | its six options, bench 13 | 776194 | 776194 | step1/bnd68_on.txt |
| packc28 | no option, bench 11 | 312866 | 312866 | step1/packc28_off_b11.txt |
| packc28 | no option, bench 13 | 862329 | 862329 | step1/packc28_off_b13.txt |
| packc28 | no option, go perft 5 | 4865609 | 4865609 | step1/packc28_off_perft.txt |
| packc28 | its four options, bench 11 | 277906 | 277906 | step1/packc28_on.txt |
| packc28 | its four options, bench 13 | 690187 | 690187 | step1/packc28_on.txt |

Builds: clean copies of d4f43124 exported to /tmp/forge_bnd68 and /tmp/forge_packc28, `patch -p1` applied with no fuzz and no rejects (bnd68: 6 files incl. two under tests/; packc28: src/search.cpp only — src/uci.cpp untouched in both, which is where the missing option declarations live), built like job 1 (g++, Release, `-DFORGE_NNUE_HIDDEN=256`). Nothing committed.

## 3. Controls
- **Determinism check, base vs base (B1 exe, no search options), 100 games, seed 7000**: D1_last40.txt: Elo -0.00 +/- 0.00, 32-32-36, Ptnml [0,0,50,0,0] — degenerate, as it must be for two identical engines; the pairs all score 2. 49 seconds.
- **Proof that the engine received `setoption name Hash value 16` (first match M3)**: tests_glmflash_job2/m3_cand_uci_in.log holds the candidate's full UCI input (tee wrapper, then the same B1 exe): exactly **1500 lines `setoption name Hash value 16`**, 1500 `setoption name Threads value 1`, 1500 `setoption name HistRework value 2` — one per game. No "doesn't have option" warning in M3's output (tests_glmflash_job2/warnings_count.txt: M3 0).

## 4. All matches of job 1 and job 2 (fixed 20,000 nodes; job 2 form pins `option.Threads=1 option.Hash=16` on BOTH sides; job 1 matches ran at Hash 32 — see job 1 report)

| match | options on cand | seed | games | W-L-D | pair counts Ptnml(0-2) | fastchess Elo +/- err | my Elo [pair interval] |
|---|---|---|---|---|---|---|---|
| C1 (j1 control) | none | 7001 | 600 | 176-176-248 | [0,0,300,0,0] | -0.00 +/- 0.00 | -0.00 [degenerate, e=0] |
| C2 (j1 control) | nodes 20000 vs 10000 | 7002 | 300 | 180-34-86 | [1,6,40,52,51] | 184.73 +/- 33.28 | 184.73 [152.9, 219.7] |
| C3 (j1 control) | BundlePreset=B1, 2 games | 7003 | 2 | 1-0-1 | [0,0,0,1,0] | 190.85 +/- 0.00 | 190.85 [n/a, 1 pair] |
| M1 (j1) | BundlePreset=B1 | 7101 | 3000 | 918-755-1327 | [59,332,589,427,93] | 18.90 +/- 8.36 | 18.90 [10.5, 27.3] |
| M2 (j1, INCOMPLETE) | HistRework=2 CuckooRep=true TtPruneV2=true | 7102 | 1836 of 2000 | 579-490-767 | [47,201,349,258,63] | 18.16 +/- 11.19 (last printed block, 1800 games) | 16.86 [5.8, 28.0] (all 1836) |
| D1 (j2 control) | none (B1 exe) | 7000 | 100 | 32-32-36 | [0,0,50,0,0] | -0.00 +/- 0.00 | -0.00 [degenerate] |
| M3 (j2, INCOMPLETE) | HistRework=2 | 7103 | 1499 of 1500 | 477-383-639 | [36,160,290,203,61] | 21.62 +/- 12.78 (last printed block, 1400 games: M3_last_block.txt) | **21.82 [9.2, 34.0]** |
| M4 (j2) | TtPruneV2=true | 7104 | 1500 | 435-435-630 | [40,192,295,174,49] | -0.00 +/- 12.20 | -0.00 [-12.2, 12.2] |
| M5 (j2) | CuckooRep=true | 7105 | 1500 | 415-400-685 | [34,183,314,172,47] | 3.47 +/- 11.83 | 3.47 [-8.4, 15.3] |
| M6 (j2, INVALID) | bnd68's six options | 7121 | 2000 | 597-597-806 | [0,0,1000,0,0] | -0.00 +/- 0.00 | -0.00 [degenerate] |
| M7 (j2, INCOMPLETE + INVALID) | packc28's four options | 7122 | 1824 of 2000 | 516-516-792 | [0,0,912,0,0] | -0.00 +/- 0.00 (last printed block, 1800 games: M7_last_block.txt) | -0.00 [degenerate] |

- W-L-D and pair counts are my recount from the PGNs (`tests_glmflash_job2/pgn_to_gamelog.py`, logs committed as `{tag}_games.txt`); they agree with fastchess's tables everywhere fastchess printed one (M4, M5, D1, M6 exactly; M3's block is at 1400 games, M7's at 1800 of its 1824 — both were cut). fastchess's Elo for M2/M3/M7 is from its last printed block, over fewer games than my recount covers; where both cover the same games the two computations agree (M1: 18.90 = 18.90; C2: 184.73 = 184.73; M4/M5 exact ties). My Elo/interval method per Fable's formula, script: `tests_glmflash_job2/elo_from_gamelog.py`, outputs also in `my_elo_job2.txt`.
- Crashes / illegal moves / disconnects: 0 in every match (grep over all six .out files for disconnect/illegal/crash/stall/forfeit: no hits).
- Last 40 lines of each fastchess output: `tests_glmflash_job2/{D1,M3,M4,M5,M6,M7}_last40.txt`; for the two cut matches the last printed stats block additionally saved as `tests_glmflash_job2/{M3,M7}_last_block.txt` (their blocks sit before the last-40 tail, which holds only the interrupt). PGNs not committed.

- **M6/M7 are invalid for their question**: fastchess warned per game (counts in `tests_glmflash_job2/warnings_count.txt`: M6 12,000 — all six options × 2000 games; M7 7,312 — all four × 1828; M3/M4/M5/D1: 0) and sent none of the new options, so cand and base were the same engine with the same options. The `uci` replies are committed as `tests_glmflash_job2/uci_options_{bnd68,packc28,B1}.txt`: bnd68 lists 10 options (the base set only), packc28 likewise 10 — none of their new options are declared (grep for NonPawnCorr/PawnHist/ContHist4Pct/EvalOnlyStore* and AspFailHigh*/EvalSwing* in those two files: no hits). The B1 build declares 15 options including all five of its own (see uci_options_B1.txt). The b1 patch touched src/uci.cpp; the bnd68 and packc28 patches did not — that is the difference.

## 5. Step 4 (sanitizers)
Not part of job 2; not done.

## 6. Which files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash_2.md` only.
- Branch `opus-r13-p1-nearmiss-ports`: file list (names only), then `opus_r13/p1/bnd68/bnd68_port.patch` and `opus_r13/p1/packc28/packc28_port.patch`. I did NOT read the bnd68/packc28 README/IDEA_SOURCE files this time.
- Commit d4f43124: exported twice for the two new builds; no file opened this time beyond the patch application.
- Nothing else; no FABLE_TO_deepseek file read; no other branch touched.

## 7. Start and end of each step (from tests_glmflash_job2/stamps.txt, UTC)
- 14:33 job 1 committed and pushed; job 2 file read 14:47 (after a 12-minute wait loop); 14:47-14:48 both trees exported, both patches applied; 14:48-14:50 both builds in parallel (each `--target forge`, ~90 s).
- 14:50-14:52 B1 pins re-verified; 14:52-14:53 the ten bnd68/packc28 pin runs — all match.
- 14:53-14:54 driver started: D1 14:34:17-14:35:07 (50 s); M3 14:35:07-14:47:07 (CUT at its own 720 s limit, exit 124); M4 14:47:07-14:58:58 (complete, 11:51); M5 14:58:58-15:10:38 (complete, 11:40); M6 15:10:38-15:25:18 (complete, 14:40); M7 15:25:18-15:38:18 (CUT at the global stop, exit 124); 15:38:18 driver2 done.
- 15:39-15:45 M6/M7 invalidity diagnosed (warnings counted, full uci option lists inspected); 15:45-15:52 report written, evidence verified and committed. (This runs a few minutes past the 75-minute line; the diagnosis changed the conclusion, so I spent the extra minutes on it.)

## 8. What I did not do
- No valid M6 or M7: the two matches measured nothing about the new patches (see section 1). Re-running them with a working setup would take ~30 min for 2,000 + 2,000 games — beyond this job's budget.
- No pull request opened; no engine source committed; the two patched trees live only in /tmp. No other branches touched.

## 9. What I am not sure about
- **M3 was cut by MY 12-minute limit, not by the job's clock** — the form's Hash 16 makes games slightly slower than job 1's Hash 32 (~129 vs ~130 games/min), and I sized the limits from the old rate. M4 and M5 finished inside theirs (11:51, 11:40); M3 missed by ~40 seconds (1 game short of 1,500; its last round has one game, which my recount counts as a half-pair in the pentanomial bucket sum — the interval I quote is from the full 750 rounds as scored, and agrees with fastchess's 1,400-game block). The job wanted only the LAST match cut; mine cut the first. My scheduling error, noted as such.
- Whether the bnd68/packc28 engines accept the option lines with exactly the intended semantics when sent directly (the bench pins matching the expected values is strong evidence, but the pin equality is over whole-search node counts, not over every line of the options' behavior).
- My M7 recount says 1,824 games where fastchess's last printed block said 1,800; the extra 24 games finished between the last ratinginterval block and the interrupt. I quote the PGN recount as the exact end state.

## 10. A better way
- **A harness stopgap for engines that do not declare their options**: a tee-wrapper that injects the fixed `setoption` lines into the engine's UCI input right after fastchess's `uci` handshake (the M3 wrapper already records the input; the same trick can inject). That would have let M6/M7 run validly without touching the port patches. Checkable: run one 2-game match with the wrapper and diff the injected input log against the intended option set; the bench pins then confirm the state.
- **The real fix belongs in the two port patches**: add the missing `option name ...` declarations to the uci reply (the b1 patch shows exactly how — its five options are declared and were accepted by fastchess 1,500/1,500 times). Until then no GUI/harness that validates option names can test bnd68/packc28.
- **Schedule by measured rate, not estimated**: D1 measured the true rate (100 games in 50 s = 120 games/min at Hash 16) before M3 started; a driver that sets each match's limit from that measured rate (1500 games → 12.9 min) would have kept M3 whole and cut only M7. One line of arithmetic, taken from the just-finished match.
- **fastchess's undeclared-option warning is itself a cheap positive control**: grep the match output for "doesn't have option" after every match; a non-zero count invalidates the match immediately. Had I grepped after M6 instead of after M7's interrupt, the invalidity would have surfaced 15 minutes earlier. Cheap and worth adding to every job's checklist.

## Questions for Fable
- CorrHistPlus was never measured alone (M3/M4/M5 cover only three of the bundle's four parts). Do you want M-CorrHistPlus (1,500 games, seed 7106) to complete the decomposition, or is the bundle-vs-parts question settled by HistRework's dominance?
- For the M6/M7 rerun: do you want the wrapper-injection stopgap on my side, or will you first fix the two patches' uci declarations (their files, your branch) so the plain form works? The second is the honest harness path; the first answers the strength question ~1 job sooner.
- The bnd68 patch also patches two files under tests/ (nonpawn_key_tests.cpp, pack_e_tests.cpp) — tests that, like forge_tests in job 1, may not compile against the patched headers. Worth knowing whether those test targets are expected to build on the old tree, or are PC-only artifacts.
