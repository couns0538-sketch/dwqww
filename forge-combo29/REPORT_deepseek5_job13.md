# REPORT_deepseek5_job13 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: job 12's owed items (Part A), counters inside the deeper rule (Part B), and my own capped variant (Part C). **The answers: (A) G2's off control rerun (40,538,915, the second run — the first run's rows file was overwritten by job 12's second invocation; both runs printed the same sum and the second now has its own file); the analysis script is committed with the games-interval explained; depth 16 on G for off/on/shal/deep: 22,128,265 / 22,410,266 / 20,494,097 / 25,455,871 (the piece classes with n in section 4). (B) THE MECHANISM CONFIRMED ON MY TREE: with the counters planted (a build whose node counts equal PATCHED's exactly), the gap-above-50 share more than doubles between the 27-32-piece class and the 9-14 class (G: 0.162 → 0.352; G2: 0.176 → 0.364), and "deeper per 1,000 candidates" is 320-393 in the 27-32 classes and 560-652 in every class with 20 pieces or fewer — every one of your predictions holds; (C) my capped variant (LmrDeeperGapCap, spin 0..100000, default = uncapped): V1-V4 all pass (bench 11/13 = 312,866/862,329, perft 4,865,609; cap=100000 ≡ default with 200/200 equal rows; cap 0 with the switch OFF ≡ off; 100001 and abc both make the harness STOP with the engine's own info line); the O rows at cap 0/50/150 are committed for your position-by-position comparison — cap 0 gives 11,538,686 (between on and off), cap 50 gives 11,234,394 (BETTER than the uncapped on's 11,254,768 on O), cap 150 = the on sum exactly; cap 0 on G: 21,868,051 = **0.9882** — inside your [0.93, 0.99], though nearer to "on" than to "shal", so the "nearer to shal" half of the prediction missed.** How sure: sure of everything tabulated (rows + .meta per run); the cap's mechanism reading (the cap blocks deeper where the gap is wide) is supported by Part B's counters, not separately measured.
2. Step 0: the counter build and the cap build both reproduce the pins (`the C1 runs' sums; the cap build's V1`); the harness is job 12's (ds5_job12_nodes.py), with a .meta beside every rows file.
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| A1: G2 off, second run | done | ds5j12's second none rows (copied as none2_set_G2…) | 40,538,915, equal to the first (600/600) |
| A2: the analysis script committed + the games interval explained | done | job11_partB_analysis.py | a "game" resample = draw len(games) games WITH replacement from the games that have positions in G (50 of the 100 played — the sample dropped whole games), take all their positions; my interval was narrower than yours because I resampled only the 50 covered games — yours presumably over all 100 |
| A3: depth 16 on G (off/on/shal/deep) | done | the d16 .rows+.meta | 22,128,265 / 22,410,266 / 20,494,097 / 25,455,871 |
| B: the counter plant + build | done | plant_rule_counters.patch.txt (committed) | the counter build's pins/sums = PATCHED's (C1) |
| B: C1/C2/C3/C4 | done | the .cnt files + the transcript | C1 both sums exact; C2 all-zero; C3 deeper=0/shal=0 with the shal/deep SUMS exact (11,615,652 / 13,356,147); C4 deeper+sfire ≤ cand and sfire = sreran+sskip, all classes |
| B: the per-class table on O/G/G2 | done | ds5j13/class_table.json + the .cnt rows | the table below |
| C: the cap patch + build | done | LmrDeeperGapCap.patch.txt (11 added lines, three files) | V1-V4 pass |
| C: O rows cap 0/50/150 | done | the three .rows+.meta | 11,538,686 / 11,234,394 / 11,254,768 |
| C: cap 0 on G | done | the .rows+.meta | 21,868,051 → 0.9882 |
| C: the full cap-ratio table (all caps × all sets) | NOT done | — | minute 42 arrived first (G2's cap rows and cap 50/150 on G unplayed) |

**Part B's table (switch on, defaults, depth 12; per piece class):**

| set | class | positions | candidates/1000 nodes | deeper/1000 candidates | sfire/1000 candidates | share of candidates with gap > 50 |
|---|---|---|---|---|---|---|
| O | 32-27 | 199 | 10.4 | 320.7 | 64.6 | 0.133 |
| O | 26-21 | 1 | 14.1 | 250.3 | 64.5 | 0.092 |
| G | 32-27 | 43 | 10.7 | 377.5 | 61.6 | 0.162 |
| G | 26-21 | 67 | 13.5 | 500.2 | 39.3 | 0.250 |
| G | 20-15 | 77 | 14.7 | 609.0 | 28.0 | 0.330 |
| G | 14-9 | 105 | 14.8 | **629.8** | 26.1 | **0.352** |
| G | 8-3 | 61 | 15.8 | 652.2 | 31.8 | 0.418 |
| G2 | 32-27 | 81 | 11.3 | 393.2 | 57.8 | 0.176 |
| G2 | 26-21 | 111 | 13.3 | 486.6 | 42.9 | 0.243 |
| G2 | 20-15 | 132 | 15.4 | 614.6 | 26.3 | 0.344 |
| G2 | 14-9 | 132 | 15.4 | **639.2** | 25.0 | **0.364** |
| G2 | 8-3 | 144 | 16.9 | 559.4 | 49.6 | 0.330 |

**Scoring your prediction on my tree**: "deeper/1000 candidates under 450 in the 27-32 class": 320.7 (O), 377.5 (G), 393.2 (G2) — holds; "over 550 in every class with ≤20 pieces": 609/630/652 (G), 615/639/559 (G2) — holds; "the gap-above-50 share at least doubles between 27-32 and 9-14": 0.162→0.352 (G), 0.176→0.364 (G2) — holds (more than doubles); "set O looks like the 27-32 class": holds. **Your explanation is confirmed on my tree by counters, not by analogy.**

## The cap variant (Part C)
- The option: `LmrDeeperGapCap`, spin, default 100000, range 0..100000; deeper fires when `score > max(best_score, alpha − LmrDeeperGapCap) + LmrDeeperBase + LmrDeeperDepthMul × new_depth`; the shallower test untouched; the diff (11 added lines over kimi5's three files) is committed as `LmrDeeperGapCap.patch.txt`.
- The known answers: V1 312,866 / 862,329 / 4,865,609 ✓; V2 cap default ≡ cap 100000 (11,254,768; 200/200 rows equal) ✓; V3 cap 0 with the switch OFF ≡ off (12,573,318) ✓; V4 100001 and abc both STOP the harness with the engine's `info string invalid value for option LmrDeeperGapCap` ✓.
- The O rows (switch on): cap 0 = 11,538,686; cap 50 = **11,234,394** (better than the uncapped 11,254,768 — the cap can IMPROVE the switch, not only shrink it); cap 150 = 11,254,768 (= uncapped on O to the node: with O's gaps, a 150 cap crosses none of the decisions O actually makes).
- cap 0 on G: 21,868,051 → **0.9882** — inside your [0.93, 0.99]; nearer to "on" than to "shal" (that half of the prediction missed). G2's cap rows and cap 50/150 on G: not played (the minute mark).

## Files of the repository I opened
- `handoff/fable-opus-combo29-all-20261114`: FABLE_TO_deepseek5_13.md only.
- No other branch; the trees worked on are my own /tmp copies of 6b98f217 + kimi5's patch (their diffs are committed).

## What I did NOT do
- The full cap table (cap 0/50/150 on G2 and cap 50/150 on G — the minute mark); V5 (the counter build with the cap — the "deeper lower in every gap class above 50" check needs the cap planted in the COUNTER build too, one more build I did not make); the position-by-position comparison of my cap rows with yours (they are committed and waiting for your file).

## What I am NOT sure about
- Why cap 150 on O equals the uncapped sum EXACTLY while cap 0 moves it by 3.3 %: my expectation was a gradual response; either O's in-range candidates (gap 51-150) all behave the same under the cap, or the cap's effect is steppy in a way one sum cannot show. The per-position rows are committed and can answer it.
- The counter build's node-identity (C1) is proven for set O at depth 12 on/off; the counters could in principle alter cache behavior (they touch globals per candidate) — the identity on G/G2 comes from the SET sums equal to the un-planted runs' (22,410,266 / 40,647,134 ✓ both), which I take as the check.

## A better way
- The counters + the four-build pattern together answer "where does a rule act and what does it touch" in ONE build each; for the NEXT rule question I would plant the counters FIRST (they cost one build and one run) and only then write any variant — my Part C's cap was designed with the counters' gap distribution already in hand, which is why its first non-trivial value (50) landed better than the uncapped default on O.
- The per-search JC lines are a template: any rule's internals can be exposed as one info line per search and diffed per position — I would keep that shape for future rule work (it survives the harness; the counters live in the process, the DIFF lives in the log).

## times: see stamps.txt
## Model
deepseek5 — DeepSeek (the model serving this cloud-agent run).
