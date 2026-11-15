# REPORT_glmflash_job4 (glmflash, 2026-11-15)

1. **packc28's gain is real: pooled over both seeds (job 3's M7 + this job's M1: 3,991 games, 1,996 pairs) it is +18.73 Elo, my 95 % pair interval [11.2, 26.3] — the two seeds agree tightly (M7 +19.13 [8.4, 29.9], M1 +18.51 [7.8, 28.9]). The idea that carries it is the eval-swing history: M2 (`EvalSwingMult 24` + `EvalSwingMax 200` alone) is +19.21 [3.7, 34.0] over its 887 games — the only single-idea interval that excludes 0. `TtCutoffHistory 1` adds nothing on top of the four: M4 (five vs four) +1.39 [-8.9, 11.7] over its full 2,000 games. The Asp pair alone (M3) was cut at only 286 games: +23.12 [-2.3, 48.7] — inconclusive alone, and I do not claim it carries anything.** Reached/cut/not-reached, first paragraph as asked: C complete (300), M4 complete (2,000), M1 cut at 1,991 of 2,000, M2 cut at 887 of 2,000, M3 cut at 286 of 2,000, M5 not reached. Two of my own tools failed along the way and are documented in section 7 with their evidence; the probe-before-match rule caught the second one before any long match was wasted.

## 2. Step 0: known numbers — ALL MATCH (fresh engine process per line; raw outputs in tests_glmflash_job4/step1/)

| setup | expected | printed | file |
|---|---|---|---|
| packc28, no option, bench 11 | 312866 | 312866 | step1/c28_off_b11.txt |
| packc28, no option, bench 13 | 862329 | 862329 | step1/c28_off_b13.txt |
| packc28, no option, go perft 5 | 4865609 | 4865609 | step1/c28_off_perft.txt |
| four gate options through wrapper, bench 13 | 690187 | 690187 | probes/probe logs + driver stamps (wrapcheck) |
| `TtCutoffHistory 1` alone, bench 13 (new, reported) | — | 803034 | step1/c28_ttcutoff_b13.txt |
| `AspFailHighReduce 1` + `AspFailHighMaxReduce 3` alone, bench 13 (new) | — | 649268 | step1/c28_asp_b13.txt |
| `EvalSwingMult 24` + `EvalSwingMax 200` alone, bench 13 (new) | — | 683335 | step1/c28_swing_b13.txt |
| all five together, bench 13 (new) | — | 845159 | step1/c28_allfive_b13.txt |

`TtCutoffHistory` is accepted by the packc28 engine (bench changes) though it is not declared in the `uci` reply (the reply is job 2's `uci_options_packc28.txt`, 10 base options only) — so M4's cand runs through the five-option wrapper, its base through the four-option wrapper.

## 3. Probes and controls
- **The job's probe gate, run before every match** (2 games, exact match command shape, tee'd cand input): evidence in `tests_glmflash_job4/probes/` — for M1: `probe_M1_uci_in.log` holds each of the four `setoption name ...` lines once per game (2× at check time, recorded as `delivered: ... x2` in the driver stamps) plus fastchess's own `setoption name Threads value 1` / `Hash value 16` / `OwnBook false`; the committed log now shows 3 occurrences per option because the bench-through-wrapper check that follows appends to the same tee'd file (one more inject line) — the count semantics are stated here so the file and the stamps agree. Same shape for M2 (2×2 lines +1), M3 (2×2 +1), M4 (probe log = probes/probe_5_uci_in.log, five options — this probe ran in the first driver and is the one whose OK let M4 play). Probe PGNs and outputs also committed.
- **What the probes caught** (both faults are mine, both are in the committed stamps): (i) my first probe gate required the single 2-game pair to be non-degenerate — with one pair that is ~40 % likely to happen by chance (a drawn pair) and it is VACUOUSLY true-checked for identical engines (control C); four matches were wrongly skipped (driver_job4.sh, stamps 17:28-17:55). (ii) my corrected driver generated the probe wrappers by interpolating the inject FILE PATH into a printf (so the "option" sent was the path string; the engine ran OFF and M1's probe bench read 862329, not 690187) — caught by the probe's own bench check before any match (driver_job4b.sh, stamps 18:03-18:07). The final gate (driver_job4c.sh): every inject line must appear ≥ 2× in the tee'd input log, bench-through-wrapper must equal the given pin, and the pair-shape check [0,0,N,0,0] runs on the MATCH (thousands of pairs), where it is conclusive.
- **Control C (sensitivity), 20,000 vs 10,000 nodes, no options, 300 games, seed 7140, OwnBook false both sides**: C_last40.txt: Elo 189.31 +/- 27.55, 169-20-111, Ptnml [0,1,39,70,40]; my Elo 189.31 [162.8, 218.0]. Near +200 as the job expects; the tool sees large differences with the new form (OwnBook false did not change its sensitivity).
- Determinism check: not repeated this job (D1 exists from job 2; the probe pair-shape recordings cover the same ground for the new wrappers).

## 4. Table: all packc28 matches of jobs 3 and 4 (fixed 20,000 nodes, Hash 16 + Threads 1 + OwnBook false both sides in job 4)

| match | options on cand vs base | seed | games | W-L-D | Ptnml(0-2) | fastchess Elo +/- err | my Elo [pair interval] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|
| M7 (j3) | four via wrapper vs none | 7132 | 2000 | 619-509-872 | [52,216,378,278,76] | 19.13 +/- 10.77 | 19.13 [8.4, 29.9] | 0 |
| C (j4) | nodes 20000 vs 10000, none | 7140 | 300 | 169-20-111 | [0,1,39,70,40] | 189.31 +/- 27.55 | 189.31 [162.8, 218.0] | 0 |
| M1 (j4, INCOMPLETE) | four via wrapper vs none | 7141 | 1991 of 2000 | 618-512-861 | [53,202,397,275,69] | 17.39 +/- 11.17 (block at 1800: M1_last_block.txt) | 18.51 [7.8, 28.9] | 0 |
| M2 (j4, INCOMPLETE) | EvalSwing pair via wrapper vs none | 7142 | 887 of 2000 | 279-230-378 | [15,97,186,117,29] | 20.05 +/- 15.95 (block at 798: M2_last_block.txt) | 19.21 [3.7, 34.0] | 0 |
| M3 (j4, INCOMPLETE) | Asp pair via wrapper vs none | 7143 | 286 of 2000 | 87-68-131 | [4,28,64,39,8] | 27.85 +/- 29.84 (block at 200: M3_last_block.txt) | 23.12 [-2.3, 48.7] | 0 |
| M4 (j4) | five via wrapper vs four via wrapper | 7144 | 2000 | 572-564-864 | [56,231,412,251,50] | 1.39 +/- 10.25 | 1.39 [-8.9, 11.7] | 0 |
| M7 + M1 pooled | four vs none, two seeds | — | 3991 (1996 pairs) | 1237-1021-1733 | [105,418,775,553,145] | — | **18.73 [11.2, 26.3]** | 0 |

W-L-D and pair counts are my PGN recounts (`pgn_to_gamelog.py`; logs committed as `{tag}j4_games.txt`); they match fastchess's blocks where the block covers the same games (C exact; M4 exact; M1's block at 1800 of 1,991; M2's at 798 of 887; M3's at 200 of 286). Cut matches' last printed blocks are committed as `{M1,M2,M3}_last_block.txt` (their tails hold only the interrupt); C's and M4's final tables are inside their `_last40.txt`. My Elo/interval: Fable's pair formula via `elo_from_gamelog.py`, outputs in `my_elo_job4.txt` (including the pooled row). PGNs not committed.

## 5. Step 4 (sanitizers)
Not part of job 4; not done.

## 6. Which files of the repository I opened
- Branch `handoff/fable-opus-combo29-all-20261114`: `forge-combo29/soak_all/FABLE_TO_glmflash_4.md` only.
- No repository file beyond that: packc28's tree was reused from job 2, no new patch fetched (the `TtCutoffHistory` switch lives in the already-extracted packc28_port.patch; its presence was verified by behavior, not by reading the patch again).
- Nothing else; no FABLE_TO_deepseek file read; no other branch touched.

## 7. Start and end of each step (from tests_glmflash_job4/stamps.txt, UTC) — including the two tool faults
- 17:26 job 4 file read; 17:26-17:27 step 0 (the seven bench runs above).
- 17:26:37 driver 4 start with my first probe gate; probes C/M1/M2/M3 MISFIRED on the 1-pair degeneracy check (stamps PROBEFAIL 17:28-17:35); M4's probe passed and M4 ran 17:37:05-17:53:35 (2,000 games, complete table, warn 0); M5's probe misfired the same way at 17:55; driver done 17:55:40.
- 17:56-17:58: diagnosis of the gate (a 1-pair shape check cannot separate "identical play" from "a drawn pair"; ~40 % flaky; inapplicable to identical engines), written into the stamps; driver 4b launched 17:57:01 with the shape check moved to the match.
- 18:01-18:07: C played clean (300 games, shape OK); the M1/M2/M3 probes now caught a REAL wrapper-generation bug (inject path interpolated instead of file content; M1's probe bench read the OFF 862329) — probes refused them; driver 4b done 18:07:39.
- 18:08: driver 4c: wrapper generation fixed to `{ cat <inject-file>; cat; } | tee | exe`; probes M1/M2/M3 all PASS (delivery x2 each; M1 bench13 = 690187); matches: M1 18:10:27-18:26:28 (CUT at 960 s, 1,991 games); M2 18:28:33-18:35:33 (CUT at 420 s, 887 games); M3 18:37:39-18:40:00 (CUT at 141 s, 286 games — the stop line arrived during it); driver done 18:40:00.
- 18:40-18:50: recounts, my Elo, pooling, report, verification, commit. The 75-minute line (18:41) fell inside M3's run; per the stop rule the report uses the games the matches had.

## 8. What I did not do
- M5 (`EvalSwingMult 48` + `EvalSwingMax 200`, 1,500 games): not reached — no time left after the two gate faults and the four matches.
- M2 and M3 at their full 2,000 games: the clock (and my two gate faults, which cost ~25 minutes) cut them to 887 and 286. The EvalSwing conclusion rests on 887 games; the Asp-pair question is OPEN (286 games is not enough to say anything).
- No pull request; no engine source committed; no PGN committed; no other branches touched.

## 9. What I am not sure about
- **Whether the Asp pair contributes.** Its 286-game interval [-2.3, 48.7] covers everything from nothing to more than the whole patch. The four-option result (+18.7 pooled) and the EvalSwing-only result (+19.2 [3.7, 34.0]) together suggest EvalSwing carries most or all of it, but a full 2,000-game M3 is the only way to close it.
- M2's +19.2 comes from 887 games — consistent with the four-option pooled +18.7, but a single-idea estimate at this length has an error of ~±15, so "EvalSwing carries it" is the reading I stand behind, not a measured equality with the four-option value.
- M1's last round: 1,991 games = 995 complete pairs + 1 game (the cut) — my recount counts that single game as a half-pair in the mean (the committed script notes it); the effect on the interval is negligible but it is there.
- The engine's handling of option ORDER (Threads first in every probe log; the inject block always precedes fastchess's own options): all probes showed the expected bench, so delivery is proven; semantics under other orders are untested.

## 10. A better way
- **The probe gate belongs where the evidence is.** What a 2-game probe CAN prove: option delivery (input log), bench-through-wrapper pin, engine alive. What it CANNOT prove at one pair: non-degeneracy (a drawn pair happens ~40 % of the time; identical engines make it certain). The conclusive shape check belongs on the match. My first gate inverted this and cost four matches; the corrected gate then caught a real injection bug on its first use — the rule is right, the division of labor between probe and match was wrong.
- **Generate wrappers from file content, never by string interpolation.** `printf '<path>'` sent the path as an option. The `cat <file>; cat` form is immune to quoting and to option-count changes; I would make it the standard for every wrapper from now on.
- **The opening-file indexing costs ~2 minutes per fastchess invocation** (visible in every probe stamp: ~2:07 for 2 games). For probe-heavy jobs that dwarfs the games. If fastchess ever gains an index cache (or if a smaller book slice is acceptable for probes only — the MATCH book stays as is), probes drop to seconds. Not something I can change from here; flagging the cost because three probes per job is ~6 minutes of pure indexing.
- For the pooled number I again used pair-list pooling (Fable's formula). If you pool differently, name the method and I will compute both.

## Questions for Fable
- M3 (Asp pair alone) was cut at 286 games — is the question "does the Asp pair add anything on top of EvalSwing" worth a full 2,000-game match next job, or does the four-vs-none pooled +18.7 plus EvalSwing-only +19.2 settle the port decision already?
- TtCutoffHistory measured +1.4 [-8.9, 11.7] on top of the four. Keep it out of the port, or is its bench behavior (803034 vs 862329 OFF — it SEARCHES more, not less) worth a look at what it does before deciding?
- My step-0 observation: the Asp pair alone REDUCES bench nodes the most (649268 < 683335 EvalSwing < 862329 OFF < 803034 TtCutoff < 845159 all five). If you want, next job can check whether Asp's node reduction is pure speed (same moves, fewer nodes) or a search-behavior change — one bench series per depth answers it.
