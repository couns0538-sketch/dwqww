# Sol — Job 9 quiet-history split, clearing controls and KRK

## Step 0 and known answers

1. **Step 0 passed on both executables.** Each matched all eight fresh-process pins. Defaults gave 312866, 862329 and 3024920 nodes at bench depths 11, 13 and 16, and 4865609 at perft 5. S14 gave 242796 and 656517 at bench depths 11 and 13. PC20 gave 278024 and 587276. The candidate advertised `HistoryAgeKeep` default 1024, range 0–1024, and `HistoryAgeTables` default 7, range 0–7. [Step 0 receipt](sol/job9/step0.summary.txt) · [Counting stdout](sol/job9/step0-count.raw.txt) · [Candidate stdout](sol/job9/step0-tables.raw.txt)
2. **Known answer 1 passed.** At mask 7, keep 896 and 512 each matched the corresponding Job 8 warm soft and hard arm on 1,800/1,800 rows, including CNT. The soft arms used 6,396,204 and 6,412,516 actual nodes respectively. Each hard arm used 36,000,000.
3. **Known answer 2 passed.** At keep 729, mask 0 matched Job 6 warm soft on 1,800/1,800 rows including CNT, with 6,753,665 actual nodes.
4. **Known answer 3 passed.** Each of the eight mask/budget pairs matched the matching default on 30/30 opening rows in the opening-only gate and again in the full S rows. [Pre-prediction checks](sol/job9/pre-prediction-gates.txt) · [Full-S opening checks](sol/job9/S-full-openings.txt)
5. **Known answer 4 passed.** W0 matched cold on 1,800/1,800 rows at each budget including CNT, with 5,523,343 actual soft nodes and 36,000,000 actual hard nodes. In the pinned Job 4 source, `src/uci.cpp:388–391` resets the controller board as well as calling `Searcher::clear()`. `src/uci.cpp:433–438`, `src/search.cpp:3267–3274,3287–3290` and `include/forge/search.hpp:474` trace the two buttons to a combined TT and worker reset. `src/eval.cpp:569–571` and `src/search.cpp:1258–1279` account for the double pawn-cache clear. `src/uci.cpp:43–86,706–717` shows the same rebuilt FEN and move history entering each search. [Source audit](sol/job9/W0-source.txt) · [W0 raw rows](sol/job9/W-raw)
6. **Known answer 5 passed.** At keep 729, mask 7 warm soft produced 988 pruning takes in 6,482,018 actual nodes, 0.152422 per 1,000 and 5.79% of default. The default's 17,791 takes in 6,753,665 actual nodes gave 2.634273 per 1,000. The control was below 0.527.

The [prediction](sol/job9/prediction.txt) was the sole file in commit `0be45b1d1d0a04e7d2361fb0631b3cdec322894b`. The step-2 rows all finished before that commit. S measurement started after the push, followed by W and K. The prediction's Block W percentages use Job 4's identical protocols on the same 30-game prefix as historical forecasts. [Run order and timestamps](sol/job9/stamps.txt)

## Prediction grades

A numeric guess survives within a factor of 1.5. A zero guess requires observed zero.

| Block | Arm | Budget or mode | Quantity | Guess | Observed | Outcome |
|---|---|---|---|---:|---:|---|
| S | 1 | soft | Pruning / default | 0.82 | 0.5705 | survives |
| S | 1 | soft | Changed vs default % | 29 | 36.8889 | survives |
| S | 1 | soft | Changed vs cold % | 47 | 47.7778 | survives |
| S | 1 | hard | Pruning / default | 0.87 | 0.6562 | survives |
| S | 1 | hard | Changed vs default % | 25 | 30.6111 | survives |
| S | 1 | hard | Changed vs cold % | 40 | 41.3889 | survives |
| S | 2 | soft | Pruning / default | 0.30 | 0.7392 | KILLED |
| S | 2 | soft | Changed vs default % | 39 | 39.5000 | survives |
| S | 2 | soft | Changed vs cold % | 48 | 48.8889 | survives |
| S | 2 | hard | Pruning / default | 0.46 | 0.8620 | KILLED |
| S | 2 | hard | Changed vs default % | 33 | 33.0556 | survives |
| S | 2 | hard | Changed vs cold % | 41 | 42.3889 | survives |
| S | 5 | soft | Pruning / default | 0.58 | 0.1057 | KILLED |
| S | 5 | soft | Changed vs default % | 36 | 40.6667 | survives |
| S | 5 | soft | Changed vs cold % | 48 | 47.0556 | survives |
| S | 5 | hard | Pruning / default | 0.66 | 0.1614 | KILLED |
| S | 5 | hard | Changed vs default % | 31 | 32.6111 | survives |
| S | 5 | hard | Changed vs cold % | 41 | 39.1667 | survives |
| W | W1 | soft | Changed vs warm % | 41.00 | 41.0000 | survives |
| W | W1 | soft | Changed vs cold % | 46.78 | 46.7778 | survives |
| W | W1 | hard | Changed vs warm % | 34.44 | 34.4444 | survives |
| W | W1 | hard | Changed vs cold % | 40.17 | 40.1667 | survives |
| W | W2 | soft | Changed vs warm % | 43.83 | 43.8333 | survives |
| W | W2 | soft | Changed vs cold % | 43.94 | 43.9444 | survives |
| W | W2 | hard | Changed vs warm % | 36.94 | 36.9444 | survives |
| W | W2 | hard | Changed vs cold % | 39.83 | 39.8333 | survives |
| K | default | game | Misses | 10 | 1 | KILLED |
| K | default | stain | Misses | 18 | 7 | KILLED |
| K | zero | game | Misses | 3 | 2 | survives |

6 KILLED, 23 survive, 0 ungraded.

## Table S. History-age masks at keep 729

Rates use actual main plus qsearch nodes. Ply bins tally all best moves that differ from the default in order 0, 1–9, 10–29 and 30–59.

| Mask | Budget | Pruning / 1k | Pruning / default | Changed vs default | Changed vs cold | Soft actual nodes | Soft nodes/default | Soft median root depth | Changes by ply group | Largest non-opening group |
|---:|---|---:|---:|---|---|---:|---:|---:|---|---|
| 1 | soft | 1.5028 | 0.5705 | 664/1800 (36.8889%) | 860/1800 (47.7778%) | 6438849 | 0.9534 | 8.0 | 0 / 98 / 230 / 336 | 30–59 |
| 1 | hard | 8.2927 | 0.6562 | 551/1800 (30.6111%) | 745/1800 (41.3889%) | – | – | – | 0 / 87 / 191 / 273 | 30–59 |
| 2 | soft | 1.9472 | 0.7392 | 711/1800 (39.5000%) | 880/1800 (48.8889%) | 6422017 | 0.9509 | 8.0 | 0 / 95 / 256 / 360 | 30–59 |
| 2 | hard | 10.8946 | 0.8620 | 595/1800 (33.0556%) | 763/1800 (42.3889%) | – | – | – | 0 / 105 / 199 / 291 | 30–59 |
| 5 | soft | 0.2785 | 0.1057 | 732/1800 (40.6667%) | 847/1800 (47.0556%) | 6354543 | 0.9409 | 8.0 | 0 / 110 / 254 / 368 | 30–59 |
| 5 | hard | 2.0401 | 0.1614 | 587/1800 (32.6111%) | 705/1800 (39.1667%) | – | – | – | 0 / 89 / 199 / 299 | 30–59 |
| 7 | soft | 0.1524 | 0.0579 | 720/1800 (40.0000%) | 893/1800 (49.6111%) | 6482018 | 0.9598 | 8.0 | 0 / 101 / 240 / 379 | 30–59 |
| 7 | hard | 1.0964 | 0.0868 | 573/1800 (31.8333%) | 725/1800 (40.2778%) | – | – | – | 0 / 95 / 188 / 290 | 30–59 |

## Table W. Hash or worker clearing

| Arm | Budget | Changed vs warm | Changed vs cold | History pruning / 1k actual nodes | Soft actual nodes |
|---|---|---|---|---:|---:|
| W1 | soft | 738/1800 (41.0000%) | 842/1800 (46.7778%) | 1.9434 | 5786167 |
| W1 | hard | 620/1800 (34.4444%) | 723/1800 (40.1667%) | 10.8292 | – |
| W2 | soft | 789/1800 (43.8333%) | 791/1800 (43.9444%) | 0.0929 | 6189056 |
| W2 | hard | 665/1800 (36.9444%) | 717/1800 (39.8333%) | 0.5315 | – |

## Table K. KRK mate reporting at depth 14

Misses have no mate score in the last depth-14 line. The raw fixture has ten positions each at M7, M6, M5 and M4. A mate other than +7 and a mismatch against the fixture distance are counted separately. Miss indexes use pass:zero-based fixture index. Last-info nodes come from the last emitted search info line. Actual nodes sum the CNT main and quiescence searches.

| Config | Mode | Misses | Mates other than +7 | Mates differing from fixture DTM | Last-info nodes | Actual CNT nodes | Missed positions |
|---|---|---|---:|---:|---:|---:|---|
| count | FRESH | 1/40 | 31 | 3 | 5890743 | 5890743 | 1:02 |
| count | STAIN | 7/400 | 321 | 26 | 60083294 | 60083294 | 2:02, 3:02, 5:02, 6:02, 8:02, 9:02, 10:02 |
| count | GAME | 1/400 | 314 | 19 | 49611944 | 49611944 | 1:02 |
| default | FRESH | 1/40 | 31 | 3 | 5890743 | 5890743 | 1:02 |
| default | STAIN | 7/400 | 321 | 26 | 60083294 | 60083294 | 2:02, 3:02, 5:02, 6:02, 8:02, 9:02, 10:02 |
| default | GAME | 1/400 | 314 | 19 | 49611944 | 49611944 | 1:02 |
| decay | FRESH | 1/40 | 31 | 3 | 5890743 | 5890743 | 1:02 |
| decay | STAIN | 9/400 | 319 | 25 | 62748943 | 62748943 | 2:02, 4:02, 5:02, 6:02, 7:02, 8:02, 9:02, 10:22, 10:02 |
| decay | GAME | 2/400 | 314 | 19 | 49892312 | 49892312 | 1:02, 6:02 |
| zero | FRESH | 1/40 | 31 | 3 | 5890743 | 5890743 | 1:02 |
| zero | STAIN | 11/400 | 316 | 30 | 59105406 | 59105406 | 1:02, 2:02, 3:02, 4:02, 5:02, 5:05, 6:02, 7:02, 8:02, 9:02, 10:02 |
| zero | GAME | 2/400 | 322 | 29 | 52336875 | 52336875 | 1:02, 7:02 |


## Facts

- At keep 729, ageing main and rework together brought history pruning down to 10.57% of the warm default rate at soft and 16.14% at hard. Adding continuation lowered it to 5.79% and 8.68%. Continuation alone left 73.92% and 86.20%. The main-plus-rework arm still differed from cold on 847 soft and 705 hard bestmoves out of 1,800. The replay evidence supports using mask 5 as the next ageing candidate.
- W0 was sufficient to reconstruct the cold result. With only one of the two clear commands, both W1 and W2 still differed from cold on 43.94–46.78% of the soft replays and 39.83–40.17% of the hard replays. W1 kept 1.9434 soft pruning takes per 1,000 actual nodes versus W2's 0.0929. W1 clears the TT and evaluator pawn cache. W2 clears worker histories, corrections, caches and stack, and leaves the TT. The four W1/W2 arms independently reproduced all 1,800 paired rows of the historical Job 4 prefixes. [Independent replay readback](sol/job9/W-independent.txt)
- The K FRESH gate matched all three candidate configurations against count on 40/40 each by node count, bestmove and depth-14 score. At default, the candidate also matched count on 400/400 STAIN and 400/400 GAME. All four configurations gave 1/40 FRESH misses. In the default's 400 searches per carried mode, misses rose from one in GAME to seven in STAIN, all at index 02. The two ageing arms each gave two GAME misses. Their STAIN misses were nine at keep 729 mask 5 and eleven at keep 0 mask 7. [KRK identity checks](sol/job9/K-gate.txt)
- The exact pinned Carbon2 file labels indices 00–09 as M7, 10–19 as M6, 20–29 as M5 and 30–39 as M4. See fixture lines 5–44. The handoff's all-M7 description differs from those labels. Table K preserves the requested +7 comparison and separately counts scores that differ from the stated label. The reported mate distances are the engine's output at depth 14. [Pinned fixture](sol/job9/krk_40_positions.txt) · [Blob and SHA-256](sol/job9/krk-fixture.txt)

## Suspicions

- The drop from main-only to main-plus-rework implicates scaling the rework term in this PC20 build. The design omitted rework alone, so it leaves open how much of the drop would also happen with mask 4 and whether it depends on main being aged alongside it.
- The part of GAME that STAIN removes helped this fixture at default under the ten order seeds. The two protocols change the TT and pawn cache together. A randomized holdout of KRK positions and a clear command restricted to the TT would test whether the same direction holds separately.

## What I did not do

I measured the original counting executable and one isolated scratch copy. The branch records the scratch change as a unified text diff against the Job 8 age patch. I ran no playing match, tuning, training, PC experiment or independent KRK retrograde solve. [Text patch](sol/job9/history_age_tables.patch.txt)

## What I am not sure about

The pruning and bestmove changes give no estimate of Elo, wall-clock cost or the result with the PC's current net and tune. K has one concentrated hard position and ten orders of the same 40 positions. Its miss counts do not estimate the chance of missing mate in other endgame classes.

## Reproduction

Both executables are PC r15 on Forge `6b98f2170a3210e71beed04bbd2553972c253ed7` with the Job 2 counters and Job 4 buttons. The counting executable SHA-256 is `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`. The candidate adds the Job 8 age patch and the Job 9 bit mask. Candidate SHA-256 `1a1cd00fdea3fefa446f48034fc34699edbc54703712484ea2e9c8627bbcf8cd`. The scratch root skips all ageing at keep 1024 and applies bits 1, 2 and 4 to main, continuation and rework at `src/search.cpp:2695–2700`. The candidate build used GCC 14.2.0, CMake 4.2.3 Release, libstdc++ 6.0.33, glibc 2.41, x86-64-v4 and `FORGE_MATE_ALPHA_GUARD=1`. [Build receipt](sol/job9/build.txt)

All replay arms used PC20, Threads 1, Hash 16 MiB, one PV, OwnBook false and built-in AL1 s198 with weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. Each row's sibling `.meta` records the exact settings, budget, UTC start and end, binary and input hashes. S and W used the first 30 Job 3 games with `go softnodes 2000` or `go nodes 20000`. K used `go depth 14` and Python `random.Random(k).shuffle` for each of ten fresh processes in each retained-state mode. [Job 3 games](sol/job3/games.txt) · [S rows](sol/job9/S-raw) · [W rows](sol/job9/W-raw) · [K rows](sol/job9/K-raw)

From `forge-combo29/sol/job9`, the following commands check the identities and regenerate all table cells and the per-arm read counts.

```sh
python3 verify_known.py known ../job3/games.txt --job6-raw ../job6/raw --job8-raw ../job8/raw --job8-age ../job8/age-raw
python3 verify_known.py full ../job3/games.txt
python3 summarize.py k-gate krk_40_positions.txt K-raw
python3 summarize.py tables ../job3/games.txt krk_40_positions.txt S-raw W-raw K-raw \
  --job6-raw ../job6/raw --job8-raw ../job8/raw --prediction prediction.txt
```

[Per-arm row counts and node totals](sol/job9/read-counts.txt) · [UTC stamps](sol/job9/stamps.txt) · [Precommit tree readback](sol/job9/precommit-readback.txt)
