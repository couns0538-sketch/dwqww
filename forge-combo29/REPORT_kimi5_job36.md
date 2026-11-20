# kimi5 job 36 report — a node clock for r15d, proven against r17's fifteen hashes, and the first ledger of the clock decisions

## Three lines
- Asked: put a node clock on r15d as a text patch (N), prove it against Fable's node-clock tree by fifteen rows-file hashes, add a print-only ledger patch (L) that records every clock search's soft tests and its ending, commit a prediction, run the nine (+ six) NodeClock-1000 runs, check invariants I1–I8 and two controls, and produce tables T1–T4.
- Answer: patch N is astra5's `nodeclock_r15d.patch.txt` (read line by line; sha256 verified) and it reproduces ALL FIFTEEN of K6's hashes exactly; patch L (mine) prints and changes nothing (L0 hashes equal); every invariant I1–I8 holds on every run and both controls behave; the readings: the hard limit is RARE (1/2/7 aborts of 353 at A/B/C, all ≤ 3/100), the hold is BETWEEN (r = 0.815 / 0.790 / 0.846 at A/B/C; B under the 0.80 line), and TmFinishIteration saves 16–21 % of node time here while changing the bestmove on 9–13 of 353 positions per state.
- How sure: very high on the measurements (fifteen hashes exact, K7's T to the unit on all seven T-runs, K8/K9/K10 exact, every option proven to arrive by the input logs); the prediction went 4 of 6 (see (4)); the "cannot see" list of the job stands as written.

## The job's required first lines

**(1) Step 0: MET, 6 of 6** on the plain r15d build (6b98f217 + pc_r15 + a_speed_pc20_v3 + e1_legal_check_evasions, all `patch -p1 -F0`; src/search.cpp sha256 174e07a5211cb1d5… = the r15d pin; g++ 13.3.0 Release, guard via `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`; a fresh process per line, raw files `kimi5/job36/step0/`): bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609 (`none_bench11/13/16.txt`, `none_perft5.txt`); PC20 bench 11 = 278024, bench 13 = 587276 (`pc20_bench11/13.txt`). exe sha256 in `step0/exe.sha256`.

**(2) N0, N1 with N-WALL, N2: all PASS.** Patch N = astra5's node clock (file 37's offer taken; **I read every line of the patch before using it**: NodeClock spin 0–1e9 declared the tree's own way in uci.cpp; `Worker::elapsed_ms()` returns `total_nodes()/NodeClock` before any clock is read; the five direct steady_clock reads of K2 (emit, three early returns, the final result) each become `NodeClock>0 ? elapsed_ms() : <old expression>`; plus the one-line softnodes-print change of Opus that the known answers were made with; the patch head says pondering is not served).
- N0 (the no-op): NodeClock 0, PC20, go depth 12 — O sum 8,315,168 and G sum 17,611,204; per-position nodes AND bestmoves equal to job 35's base on 200/200 + 353/353 (`n0/O_d12.rows`, `n0/G_d12.rows` vs `tests_kimi5_job35/k3/baseO.json/baseG.json`); and the five pins re-run on the N build (`n0/step0_on_Nbuild.txt`): 312866 / 862329 / 3024920 / 4865609, PC20 278024 / 587276.
- N1 (it repeats): O at A, NodeClock 1000, twice, a fresh process each: the two rows files are byte-equal (sha256 3eac50dd8fd5297e… both, `n1/O_A_1.rows`, `n1/O_A_2.rows`).
- CONTROL N-WALL: the same twice with NodeClock 0 (wall clock): the two files DIFFER — e.g. line 2 `2 18 498518 f1c4` vs `2 17 222023 f1c4` (`n1/O_wall_1.rows` vs `O_wall_2.rows`; different sha256).
- N2: O at A sha256(first16) **3eac50dd8fd5297e** and G at A **424d931234dd3ff9** — both equal K6. Format rows match K6's: O `1 16 172312 f1e2` / `2 17 222023 f1c4` / `3 17 177762 e5d4`; G `1 16 170070 g7g6` / `2 16 170639 b6b5` / `3 15 167313 g1g6`.

**(3) L0: PASS.** The N+L build gives the hashes of O at A and G at A again (3eac50dd8fd5297e, 424d931234dd3ff9, `l0/O_A.rows`, `l0/G_A.rows`): L changes no search. Patch L (`ledger.patch.txt`, 126 lines, applies `patch -p1 -F0`, proven on a fresh copy + `diff` against the edited tree) only prints: one ITER line at every soft test (fields: depth elapsed target rule effort1000 falling1000 floor factor1000 basis; the factor arithmetic is captured, not recomputed — same doubles, same order) and one LEDGER line when a time-managed search ends (kind soft hard elapsed nodes depth). kind is assigned AT each break (deepseek5's read-state-at-the-event lesson applied).

**(4) The prediction graded** (`prediction.txt`, own commit 6dd99c1f0 "kimi5 job 36 prediction" at 09:08:33Z, before the first Step 3 run at 09:08:40Z, never edited):
- (a) aborts of 353: measured A 1, B 2, C 7. Predicted A 0–3 RIGHT, B 2–12 RIGHT, C 8–40 **WRONG (7, one below the range)**.
- (b) T(fin)/T(base) at A: measured 82,001/98,026 = 0.8366. Predicted 0.90–0.97 **WRONG** — the hold saves ~16 % here, far more than the 5–7 % of file 37's game matches (game searches inherit the table; these start empty, so skipped iterations cost more).
- (c) RIGHT share at A: measured 132/(132+30) = 0.8148. Predicted 0.70–0.92 RIGHT.
- (d) most frequent rule at the last soft test, G at A: S6 (244 of 353) RIGHT.
Score: (a) 2/3, (b) wrong, (c) right, (d) right — 4 of 6.

**(5) The nine hashes (and the six more) beside K6's — ALL FIFTEEN EQUAL** (`check/check_output.txt`; rows files in `l0/` and `s3/`):

| run | mine | K6 | | run | mine | K6 |
|---|---|---|---|---|---|---|
| O A | 3eac50dd8fd5297e | = | | G A fin | 5a85f018917c736f | = |
| G A | 424d931234dd3ff9 | = | | G B fin | e09e0e592abf8e8d | = |
| G B | 244776b6649f2ce1 | = | | G C fin | b6bb6cee6f6d99f7 | = |
| G C | 4e8210e936e59fd5 | = | | G A ns | 627eab46079c189a | = |
| G A C-HARD | dd3691a85ab318ed | = | | G B ns | 05db9b4b27fef38f | = |
| G A C-FLOOR | 9ad6c91af598d425 | = | | G C ns | 3d7ecdfca001e093 | = |
| | | | | G A both | f09dde3058bf9db7 | = |
| | | | | G B both | f45ab15c0037e871 | = |
| | | | | G C both | f6d5f31bfde05b74 | = |

**(6) I1–I8 and the two controls — every one MET** (full output `check/check_output.txt`):
- I1 (LEDGER elapsed = nodes/1000 floor): OK on all 15 runs.
- I2 (ABORTKEPT/ABORTNEW carry exactly K8's counts — 1,585,152 / 675,840 / 174,080 / 317,440 under C-HARD — and no other kind does): OK on all 15.
- I3 (SOFT: last ITER elapsed ≥ target; HOLD: < target): OK on all 15.
- I4 (factor1000 ≥ 450; under C-FLOOR ≥ 1000 and no SOFT stop elapsed < 317): OK on all 15.
- I5 (SOFT/HOLD/HARDEND/CAP: LEDGER nodes = the rows nodes): OK on all 15.
- I6 (HOLD counts = K10's 162/163/163, both-on 148/172/149; CAP = K9's 7/6/6, 9 under C-FLOOR, every CAP depth 64; no search has two hold lines): OK everywhere.
- I7 (sum of LEDGER elapsed = K7's T): O 54,326; G 98,026 / 45,372 / 20,715; C-HARD 80,174; C-FLOOR 160,642 — all to the unit.
- I8 (fin ITER lines up to and including the hold depth equal the base run's, field for field): OK on all three states — the switch only reads until it breaks.
- Controls: C-HARD has 92 aborts vs base's 1 and no LEDGER elapsed above 318; C-FLOOR's T 160,642 > base 98,026. Both SHOW.

**(7) The two readings, word for word by their rules.**
- "The hard limit: RARE when ABORTKEPT + ABORTNEW is at most 3 of 100 searches in each state of the base runs; otherwise ACTS, with W per state." Base runs: A 1/353 (0.28 per 100), B 2/353 (0.57), C 7/353 (1.98) — at most 3 per 100 in each state → **RARE**. (W per state anyway, ×10000 of T: kept 99 / 149 / 277 at A/B/C; new 0 everywhere; under C-HARD kept 1173, new 47.)
- "The hold, with r = RIGHT / (RIGHT + WRONG) per state: KEEPS ITS CLAIM when r ≥ 0.80 in all three states; OFTEN STOPS AN ITERATION THAT WOULD HAVE ENDED IN TIME when r < 0.60 in any state; BETWEEN otherwise." r = 132/162 = 0.8148 (A), 128/162 = 0.7901 (B), 137/162 = 0.8457 (C) — not ≥ 0.80 in all three (B fails by 0.01), never < 0.60 → **BETWEEN**.

**(8) T1–T4** (made by `table_j36.py` from the committed ledger files; full text `tables/tables_output.txt`; T = the K7 sum of LEDGER elapsed; W in ×10000 of T):

T1, how the searches end:

| run | SOFT | HOLD | HARDEND | ABORTKEPT | ABORTNEW | CAP | T | W kept | W new |
|---|---|---|---|---|---|---|---|---|---|
| O A | 200 | 0 | 0 | 0 | 0 | 0 | 54,326 | 0 | 0 |
| G A | 345 | 0 | 0 | 1 | 0 | 7 | 98,026 | 99 | 0 |
| G B | 345 | 0 | 0 | 2 | 0 | 6 | 45,372 | 149 | 0 |
| G C | 340 | 0 | 0 | 7 | 0 | 6 | 20,715 | 277 | 0 |
| G A C-HARD | 254 | 0 | 0 | 90 | 2 | 7 | 80,174 | 1173 | 47 |
| G A C-FLOOR | 342 | 0 | 0 | 2 | 0 | 9 | 160,642 | 140 | 0 |
| G A fin | 183 | 162 | 0 | 1 | 0 | 7 | 82,001 | 119 | 0 |
| G B fin | 183 | 163 | 0 | 1 | 0 | 6 | 36,739 | 85 | 0 |
| G C fin | 180 | 163 | 0 | 4 | 0 | 6 | 16,446 | 200 | 0 |
| G A ns | 346 | 0 | 0 | 1 | 0 | 6 | 88,565 | 110 | 0 |
| G B ns | 345 | 0 | 0 | 2 | 0 | 6 | 42,324 | 160 | 0 |
| G C ns | 340 | 0 | 0 | 7 | 0 | 6 | 19,221 | 299 | 0 |
| G A both | 198 | 148 | 0 | 1 | 0 | 6 | 74,862 | 130 | 0 |
| G B both | 174 | 172 | 0 | 1 | 0 | 6 | 33,832 | 92 | 0 |
| G C both | 194 | 149 | 0 | 4 | 0 | 6 | 15,509 | 212 | 0 |

T2, how late (searches by elapsed/soft; SOFT stops: sum(elapsed)/sum(target), count elapsed > 1.5·target):

| run | ≤0.5 | ≤1 | ≤2 | ≤4 | >4 | SOFT e/t | >1.5× |
|---|---|---|---|---|---|---|---|
| O A | 23 | 132 | 40 | 4 | 1 | 1.4195 | 55 |
| G A | 55 | 206 | 77 | 13 | 2 | 1.3360 | 73 |
| G B | 54 | 196 | 80 | 19 | 4 | 1.3726 | 93 |
| G C | 45 | 181 | 101 | 26 | 0 | 1.4069 | 92 |
| G A C-HARD | 55 | 298 | 0 | 0 | 0 | 1.2289 | 34 |
| G A C-FLOOR | 7 | 5 | 298 | 40 | 3 | 1.3442 | 78 |
| G A fin | 123 | 173 | 48 | 7 | 2 | 1.3046 | 34 |
| G B fin | 111 | 173 | 58 | 9 | 2 | 1.2970 | 32 |
| G C fin | 120 | 153 | 66 | 14 | 0 | 1.3295 | 33 |

T3, which rule (base runs; LAST ITER per search | all ITER lines with depth ≥ 6):

| run | view | n | S6 | S3 | U | N | mean effort1000 | falling>1000 | floor 1 | mean factor1000 |
|---|---|---|---|---|---|---|---|---|---|---|
| G A | LAST | 353 | 244 | 57 | 11 | 41 | 781 | 36.8 % | 43.3 % | 670 |
| G A | D6+ | 4,561 | 2,193 | 945 | 605 | 818 | 907 | 38.8 % | 25.6 % | 916 |
| G B | LAST | 353 | 208 | 86 | 11 | 48 | 806 | 38.8 % | 34.6 % | 707 |
| G B | D6+ | 3,706 | 1,576 | 833 | 553 | 744 | 934 | 40.4 % | 20.6 % | 967 |
| G C | LAST | 353 | 178 | 97 | 12 | 66 | 825 | 39.7 % | 29.7 % | 739 |
| G C | D6+ | 3,006 | 1,162 | 698 | 494 | 652 | 959 | 40.6 % | 16.8 % | 1,008 |

T4, the hold's own claim (positions are G set indices; saved in node-ms):

| state | holds | RIGHT | WRONG | NO NEXT LINE | MISSED | T base → fin | saved (right part, wrong part) | bestmove differs vs base (right / wrong / nonext) |
|---|---|---|---|---|---|---|---|---|
| A | 162 | 132 | 30 | 0 | 144 | 98,026 → 82,001 | 16,025 (13,887, 2,138) | right 31, 39, 204, 300, 311, 313, 317, 333; wrong 266 |
| B | 163 | 128 | 34 | 1 (base ended ABORTKEPT) | 133 | 45,372 → 36,739 | 8,633 (7,255, 1,011) | right 75, 95, 145, 148, 173, 186, 215, 219, 264, 268, 301, 308; wrong 179 |
| C | 163 | 137 | 25 | 1 (base ended ABORTKEPT) | 117 | 20,715 → 16,446 | 4,269 (3,774, 422) | right 21, 53, 98, 103, 112, 171, 221, 236, 322, 348; wrong 301 |

## Step table

| step | done / partly / not done | evidence | result |
|---|---|---|---|
| Step 0 (5 pins + bench 16) | done | `step0/` | all six exact |
| Patch N (read astra5's, apply) | done | `nodeclock.patch.txt`, `build.txt` | sha256 2b65934e… verified, `patch -p1 -F0` |
| N0 no-op | done | `n0/` | sums exact; 553/553 nodes+bestmoves vs job 35 base; five pins on N build |
| N1 repeats / N-WALL differs | done | `n1/` | equal / differ |
| N2 hashes | done | `n1/` | both = K6 |
| Patch L + L0 | done | `ledger.patch.txt`, `l0/` | prints only; both hashes = K6 |
| Prediction commit | done | `prediction.txt` (commit 6dd99c1f0) | 4 of 6 |
| Step 3 nine runs (+6 extra) | done | `s3/`, `l0/` | all 15 hashes = K6, 0 refusal lines |
| I1–I8 + controls | done | `check/check_output.txt` | all met |
| T1–T4 | done | `tables/tables_output.txt`, `table_j36.py` | above |
| Parallel processes used | — | — | 2 (N0, L0), 5 (N1 batch), 13 at once (Step 3); 4 cores |

## Findings (each with file and line of the source and a command that shows it again)

Line numbers are the N+L tree's (= r15d + patch N + patch L; r15d's own numbers in the job's K1–K10 sit about 10 lower). Reproduce any line: `grep -n "<anchor>" src/search.cpp` in a tree with both patches applied; every number below is also in the committed ledger files.

1. **Where the time goes at these three clocks.** Base searches end SOFT 96.6–97.5 % of the time, CAP 1.7–2.0 %, ABORTKEPT 0.3–2.0 %; ABORTNEW and HARDEND never fired outside C-HARD (T1). The ending is decided at the soft test `src/search.cpp:3226` (`if (elapsed_ms() >= static_cast<std::int64_t>(static_cast<double>(soft_basis) * factor)) { ledger_kind = "SOFT"; break; }`). The mean SOFT stop overshoots its target by 30–42 % (T2's sum ratio), and 73/93/92 of the ~345 SOFT stops per state exceed 1.5× their target — the iteration that ends a search typically costs a third of the remaining budget.
2. **The abort path is armed but almost never taken.** The hard stop (`should_stop_with`, src/search.cpp:1557–1567, tested every 1,024 nodes at :1771 and :1920) fired once at A, twice at B, seven times at C of 353 (T1). The one at A (position 142) shows the mechanism exactly: ITER at depth 13 has rule U with effort1000 1400 and falling1000 2500 → factor1000 4899 → target 1553; depth 14 still passes (elapsed 605 < 1379); depth 15 hits 1,585,152 nodes mid-iteration and the abort branch (`src/search.cpp:3052-3066`) keeps the depth-14 move (`l0/G_A.ledger` lines of position 142).
3. **ABORTNEW essentially never happens.** In all fifteen runs the unfinished line replaced the finished move exactly twice (both under C-HARD; T1's ABORTNEW column). The replacement test is `!(result.pv.size() > 0 && result.pv[0] == ss->pv[0])` at src/search.cpp:3054; an aborted iteration almost always has `ss->pv_length == 0` or the same first move as the finished one at these budgets. File 37's "how often the unfinished iteration replaces the finished move": 2 of 353 with hard = soft, 0 in the other fourteen runs.
4. **The hold fires on ~46 % of searches and saves 16–21 % of node time here** (T4: 162/163/163 holds of 353; T drops 98,026→82,001, 45,372→36,739, 20,715→16,446). This is much more than the 5–7 % of file 37's game matches — consistent with the job's own "cannot see": game searches inherit the table, so early iterations there cost little; here every search starts empty. My prediction (b) missed exactly this.
5. **The hold is RIGHT ~4 of 5 times by its own claim, and still changes the move.** r = 0.815/0.790/0.846 (T4) → BETWEEN. The changed best moves sit almost entirely in the RIGHT holds (8/9, 12/13, 10/11 of the changed positions per state) — a hold that correctly predicts the overrun skips the deeper iteration, and the shallower move differs on ~3 % of searches per state. The WRONG holds' saved time is small beside the RIGHT ones' (2,138 vs 13,887 node-ms at A). This is the column file 37 asked for; whether those changed moves are the −14.4 Elo is a games question and is not answered here (no strength sentence).
6. **MISSED places: 144/133/117** (search, depth) where the fin run went on and the next iteration overshot the previous target — the hold's two-sample estimate (`iteration_will_not_finish`, include/forge/tm_finish.hpp) lets those pass; it can only fire when the last two iteration durations say the next will not finish, and single-iteration spikes are invisible to it.
7. **The effort factor is the main lever at the last test** (T3): mean effort1000 at the last soft test is 781–825 (a stable best move that holds most nodes cuts the target toward 0.45–0.78 × soft), the floor 0.45 binds in 30–43 % of last tests, and rule S6 sets the first factor in 50–69 % of searches (244/208/178 of 353). The falling-score factor is active (>1000) on 37–40 % of last tests.
8. **C-HARD (hard = soft) behaves exactly as designed**: 92 aborts (90 KEPT + 2 NEW), no search above elapsed 318, T drops to 80,174 (−18.2 %); W kept 1173/10000 — the chopped iterations waste ~12 % of the remaining time. C-FLOOR (factor ≥ 1) lifts T to 160,642 (+63.9 %): no search may stop early (T2: 298 of 353 land in class ≤ 2).
9. **TmNodeShare shortens the schedule 7–10 %** (T 88,565 / 42,324 / 19,221 vs base) and both switches together 23.6–25.4 % (74,862 / 33,832 / 15,509) — the "sixth to a quarter" first look of the job file reproduces at the quarter end.

### Suspicions, not proven
- r dips at B (0.7901) against A and C (0.81–0.85). One more RIGHT hold at B would cross the 0.80 line; whether the dip is a property of the 2 s clock or noise is not decidable from 163 holds.
- The 41–66 last tests with rule N (no stability rule fired) are mostly shallow stops (depth < 6, where the effort block does not run); I did not split T3's N rows by depth, so their mean factor (≈1.0 by construction of the rule) is expected, not measured.
- The two ABORTNEW under C-HARD replaced the finished move with the unfinished line's first move; whether those two replacements were for the better is a games question, not asked here.

## From my colleagues
- **deepseek5** (branch fetched, notes read): the stage-label lesson — read a state variable at the moment the event happens — is applied in patch L (kind is assigned at each break, never reconstructed); his Killer1/CounterMove regret rates and the stand5 runner template were read but not needed (no picker counting, no games this job).
- **glmflash5**: the branch is still not there — `git fetch origin for-fable-and-opus/glmflash5-work` → "fatal: couldn't find remote ref". Went on without it (same state as my job 33/34 notes).
- **astra5** (via file 37): patch N taken from `forge-combo29/astra5/job26/nodeclock_r15d.patch.txt` on `for-fable-and-opus/astra5-work`; sha256 2b65934e5dad8066… verified against file 37's; read line by line before use (summary in (2) above). My own patch N was not needed; astra5's differs from the job's minimal description only in carrying Opus's softnodes-print line, which the known answers require.
- **carbon2** (via my own notes): `a_speed_pc20_v3.patch.txt` and `job3/e1_legal_check_evasions.patch.txt` from `for-fable-and-opus/carbon2-work` built the r15d tree (sha pin matched).
- **My own NOTES_kimi5.md**: the build recipe (guard ONLY via `-DCMAKE_CXX_FLAGS`; never as a cmake variable; g++ forced because the image's default `c++` is clang and cannot link), the .opt composition lesson (base + override, never by hand), and the async-go trap (the runner always waits for `bestmove`; `ucinewgame` + `isready` before every search).

## What this check cannot see (the job's own section, written in as it is)
Games: every search here starts from an empty table, a game search inherits the table of the move before, so its first iterations cost almost nothing and its stable count runs differently. The PC's net (the built-in evaluation plays here). A real clock (no load, no jitter; NodeClock 1000 stands for an engine at one million nodes a second). movestogo, sudden death without increment, pondering, more than one thread. And strength.

## What I did NOT do
- No games and no fastchess (the job's "cannot see" covers why); no r17 build (the fifteen hashes ARE the check against r17's rows); no pondering, movestogo, or Threads > 1 runs (the job scopes them out); no N2 fallback line-by-line comparison of patch N against K2 (the hashes matched at once, so the fallback never triggered); no T4-style grading of the six TmNodeShare/both runs (the job asks hashes only for them; their ledgers still passed I1–I6); the first N0 attempt's crashed logs (`runs/n0/` in /tmp, runner bug parts[1] for parts[2]) were not committed — the successful rerun is in `n0/` of the job folder, and the five pins on the N build from that first batch are kept as `n0/step0_on_Nbuild.txt`.

## What I am NOT sure about
- K7's "final node count" for an aborted search: I read it as the LEDGER's final nodes (I7 then matches K7 to the unit on all seven T-runs, including C-HARD's 80,174, which the rows-file sum would miss by ~9,400). The rows file keeps the last FINISHED depth's nodes per K6's own spec; the two views differ only at aborts. The match says the reading is right, but it is a reading.
- effort1000/falling1000/factor1000 are truncated (`static_cast<std::int64_t>(x * 1000)`), not rounded; nothing in K6/I1–I8 pins the choice, and T3's means move by less than 1 either way.
- The kind names OTHER:mate and OTHER:softnodes never fired (mate_moves = 0 and soft_node_limit_ = 0 in clock play); the job's "name the line" is answered with the rule's name rather than a line number, because line numbers shift between trees.
- Whether the two wall-clock N-WALL runs differ for the right reason (timing) and not a fault: their difference pattern (depth and nodes move together at whole-iteration boundaries) looks like timing; I did not dig further because the control's only demand is "differ".

## A better way
The W measure counts an aborted iteration's whole tail (elapsed minus the last ITER's elapsed) as waste. The engine already knows whether that tail was useless: the abort branch tests `ss->pv_length > 0 && result.pv[0] != ss->pv[0]` (src/search.cpp:3052-3054). One more ledger field at the abort — the unfinished iteration's pv length and whether its first move equals the finished one — splits W into "work that never had a chance to matter" and "work that almost changed the move", which is the exact quantity file 37 asks T1's ABORTNEW for, at every search instead of only the two NEW cases. Checkable the same way as this job: the new field is print-only, so L0's hashes must still match, and K8's counts pin the abort rows.

## UTC stamps
Start of the run first: 2026-11-20T09:00:30Z; claim 09:01:01Z; every step in `kimi5/job36/stamps.txt` (each line from a recorded `date -u`, a .meta, or git %cI); report assembled 09:11:33Z; all 13 Step-3 runs finished by 09:10:38Z — inside the 50-minute budget by a wide margin.

## Model name
Kimi K3 (what this runtime reports), as "kimi5".

## Last command before the report commit
`git status --short`, verbatim:

```
 M forge-combo29/NOTES_kimi5.md
?? forge-combo29/REPORT_kimi5_job36.md
?? forge-combo29/kimi5/job36/check/
?? forge-combo29/kimi5/job36/l0/smokeA.ledger
?? forge-combo29/kimi5/job36/l0/smokeA.rows
?? forge-combo29/kimi5/job36/l0/smokeA_input.log
?? forge-combo29/kimi5/job36/s3/
?? forge-combo29/kimi5/job36/stamps.txt
?? forge-combo29/kimi5/job36/tables/
```

`ls -R forge-combo29/kimi5/job36`, verbatim (130 lines):

```
forge-combo29/kimi5/job36:
build.txt
check
l0
ledger.patch.txt
n0
n1
nodeclock.patch.txt
prediction.txt
runner_j36.py
s3
stamps.txt
step0
table_j36.py
tables

forge-combo29/kimi5/job36/check:
check_j36.py
check_output.txt

forge-combo29/kimi5/job36/l0:
G_A_input.log
G_A.ledger
G_A.rows
G_A.rows.meta
O_A_input.log
O_A.ledger
O_A.rows
O_A.rows.meta
smokeA_input.log
smokeA.ledger
smokeA.rows

forge-combo29/kimi5/job36/n0:
G_d12_input.log
G_d12.rows
G_d12.rows.meta
O_d12_input.log
O_d12.rows
O_d12.rows.meta
step0_on_Nbuild.txt

forge-combo29/kimi5/job36/n1:
G_A_input.log
G_A.rows
G_A.rows.meta
O_A_1_input.log
O_A_1.rows
O_A_1.rows.meta
O_A_2_input.log
O_A_2.rows
O_A_2.rows.meta
O_wall_1_input.log
O_wall_1.rows
O_wall_1.rows.meta
O_wall_2_input.log
O_wall_2.rows
O_wall_2.rows.meta

forge-combo29/kimi5/job36/s3:
G_A_both_input.log
G_A_both.ledger
G_A_both.rows
G_A_both.rows.meta
G_A_cfloor_input.log
G_A_cfloor.ledger
G_A_cfloor.rows
G_A_cfloor.rows.meta
G_A_chard_input.log
G_A_chard.ledger
G_A_chard.rows
G_A_chard.rows.meta
G_A_fin_input.log
G_A_fin.ledger
G_A_fin.rows
G_A_fin.rows.meta
G_A_ns_input.log
G_A_ns.ledger
G_A_ns.rows
G_A_ns.rows.meta
G_B_both_input.log
G_B_both.ledger
G_B_both.rows
G_B_both.rows.meta
G_B_fin_input.log
G_B_fin.ledger
G_B_fin.rows
G_B_fin.rows.meta
G_B_input.log
G_B.ledger
G_B_ns_input.log
G_B_ns.ledger
G_B_ns.rows
G_B_ns.rows.meta
G_B.rows
G_B.rows.meta
G_C_both_input.log
G_C_both.ledger
G_C_both.rows
G_C_both.rows.meta
G_C_fin_input.log
G_C_fin.ledger
G_C_fin.rows
G_C_fin.rows.meta
G_C_input.log
G_C.ledger
G_C_ns_input.log
G_C_ns.ledger
G_C_ns.rows
G_C_ns.rows.meta
G_C.rows
G_C.rows.meta

forge-combo29/kimi5/job36/step0:
exe.sha256
none_bench11_input.log
none_bench11.txt
none_bench13_input.log
none_bench13.txt
none_bench16_input.log
none_bench16.txt
none_perft5_input.log
none_perft5.txt
pc20_bench11_input.log
pc20_bench11.txt
pc20_bench13_input.log
pc20_bench13.txt

forge-combo29/kimi5/job36/tables:
tables_output.txt
```
