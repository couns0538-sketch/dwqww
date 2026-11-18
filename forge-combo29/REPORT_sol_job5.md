# Sol — Job 5 one-step Forge search-setting sensitivity

1. **Step 0 met.** The unchanged Job 4 counting executable passed all eight fresh-process pins. Defaults 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276. [Raw commands and output](sol/job5/step0-count.raw.txt)

   I verified all starts before the engine runs. PC20 overrides came from Job 4's A2 sidecar. Defaults came from the same executable's prior UCI output.

   | Setting | Start | Step | Read from |
   |---|---:|---:|---|
   | HistoryPruneDepth | 3 | 1 | UCI default |
   | HistoryPruneMultiplier | 2220 | 200 | PC20 |
   | HistoryBonusQuadratic | 24 | 3 | PC20 |
   | HistoryBonusLinear | 54 | 6 | PC20 |
   | HistoryBonusMax | 2212 | 180 | PC20 |
   | LmrHistoryDivisor | 5643 | 500 | PC20 |
   | ProbcutMargin | 180 | 15 | UCI default |
   | RfpMargin | 72 | 6 | UCI default |

   Both one-step values and the multiplier controls fit the advertised ranges. [Inputs and exact source lines](sol/job5/start-values.txt)

2. **All three known-answer gates met.** Both warm baseline runs matched Job 3 on 1,800/1,800 rows each, including byte-equal CNT. Re-sending each start value matched all 1,800 soft baseline rows, 14,400 comparisons across eight settings. Identity covered position, reported depth and nodes, bestmove, final nodes, CNT and the last info line with the volatile time and NPS fields removed.

   On 1,800 soft searches, PC20 produced 17,791 history-pruning takes in 6,753,665 actual nodes. `HistoryPruneMultiplier=0` produced 1,295,909 takes in 6,584,542 nodes, up 74.7116× per node. `HistoryPruneMultiplier=20000` produced zero takes in 6,608,555 nodes. Every override handshake reached `readyok`. [Gates](sol/job5/gates.txt) · [Independent control readback](sol/job5/gates-independent.txt)

3. **Prediction graded and all 32 variant arms completed.** The [prediction](sol/job5/prediction.txt) was pushed alone at `3faad8023913e750c1a92ab9f6278ea827fb8ef2` after the gates and before variant runs. The first aggregator tried to parse a prose line starting with a setting name. I restricted the reader to the explicit forecast table and reran it with the same committed forecast and raw rows. [Aggregation retry](sol/job5/aggregation-retry.txt)

Read base-soft.jsonl: 1800 rows, 6753665 actual nodes, 17791 history-pruning events.
Read base-hard.jsonl: 1800 rows, 36000000 actual nodes, 454974 history-pruning events.
Read HistoryPruneDepth-minus-soft.jsonl: 1800 rows, 6747100 actual nodes, 17568 history-pruning events.
Read HistoryPruneDepth-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 448083 history-pruning events.
Read HistoryPruneDepth-plus-soft.jsonl: 1800 rows, 6753662 actual nodes, 17796 history-pruning events.
Read HistoryPruneDepth-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 441563 history-pruning events.
Read HistoryPruneMultiplier-minus-soft.jsonl: 1800 rows, 6636636 actual nodes, 21214 history-pruning events.
Read HistoryPruneMultiplier-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 642457 history-pruning events.
Read HistoryPruneMultiplier-plus-soft.jsonl: 1800 rows, 6677689 actual nodes, 13909 history-pruning events.
Read HistoryPruneMultiplier-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 350301 history-pruning events.
Read HistoryBonusQuadratic-minus-soft.jsonl: 1800 rows, 6418032 actual nodes, 12256 history-pruning events.
Read HistoryBonusQuadratic-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 393867 history-pruning events.
Read HistoryBonusQuadratic-plus-soft.jsonl: 1800 rows, 6433966 actual nodes, 21497 history-pruning events.
Read HistoryBonusQuadratic-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 584529 history-pruning events.
Read HistoryBonusLinear-minus-soft.jsonl: 1800 rows, 6513921 actual nodes, 13696 history-pruning events.
Read HistoryBonusLinear-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 474747 history-pruning events.
Read HistoryBonusLinear-plus-soft.jsonl: 1800 rows, 6510260 actual nodes, 17617 history-pruning events.
Read HistoryBonusLinear-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 459264 history-pruning events.
Read HistoryBonusMax-minus-soft.jsonl: 1800 rows, 6649119 actual nodes, 17716 history-pruning events.
Read HistoryBonusMax-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 473085 history-pruning events.
Read HistoryBonusMax-plus-soft.jsonl: 1800 rows, 6683620 actual nodes, 17952 history-pruning events.
Read HistoryBonusMax-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 504659 history-pruning events.
Read LmrHistoryDivisor-minus-soft.jsonl: 1800 rows, 6494220 actual nodes, 16587 history-pruning events.
Read LmrHistoryDivisor-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 508640 history-pruning events.
Read LmrHistoryDivisor-plus-soft.jsonl: 1800 rows, 6572021 actual nodes, 18968 history-pruning events.
Read LmrHistoryDivisor-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 512176 history-pruning events.
Read ProbcutMargin-minus-soft.jsonl: 1800 rows, 6498862 actual nodes, 16608 history-pruning events.
Read ProbcutMargin-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 476251 history-pruning events.
Read ProbcutMargin-plus-soft.jsonl: 1800 rows, 6645015 actual nodes, 17927 history-pruning events.
Read ProbcutMargin-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 480434 history-pruning events.
Read RfpMargin-minus-soft.jsonl: 1800 rows, 6390676 actual nodes, 16316 history-pruning events.
Read RfpMargin-minus-hard.jsonl: 1800 rows, 36000000 actual nodes, 528648 history-pruning events.
Read RfpMargin-plus-soft.jsonl: 1800 rows, 6540439 actual nodes, 14079 history-pruning events.
Read RfpMargin-plus-hard.jsonl: 1800 rows, 36000000 actual nodes, 455168 history-pruning events.

## Prediction grades

A numeric guess survives within a factor of 1.5. A zero guess requires an observed zero. A ratio with no hard-budget changes is undefined.

| Setting | Quantity | Guess | Measured | Outcome |
|---|---|---:|---:|---|
| HistoryPruneDepth | Soft % | 7.00 | 0.3056 | KILLED |
| HistoryPruneDepth | Hard % | 16.00 | 21.1111 | survives |
| HistoryPruneDepth | Soft/hard | 0.4375 | 0.0145 | KILLED |
| HistoryPruneMultiplier | Soft % | 5.00 | 21.8056 | KILLED |
| HistoryPruneMultiplier | Hard % | 15.00 | 30.8889 | KILLED |
| HistoryPruneMultiplier | Soft/hard | 0.3333 | 0.7059 | KILLED |
| HistoryBonusQuadratic | Soft % | 16.00 | 38.8056 | KILLED |
| HistoryBonusQuadratic | Hard % | 22.00 | 33.2778 | KILLED |
| HistoryBonusQuadratic | Soft/hard | 0.7273 | 1.1661 | KILLED |
| HistoryBonusLinear | Soft % | 9.00 | 38.7500 | KILLED |
| HistoryBonusLinear | Hard % | 12.00 | 33.2222 | KILLED |
| HistoryBonusLinear | Soft/hard | 0.7500 | 1.1664 | KILLED |
| HistoryBonusMax | Soft % | 2.00 | 11.3056 | KILLED |
| HistoryBonusMax | Hard % | 7.00 | 32.2500 | KILLED |
| HistoryBonusMax | Soft/hard | 0.2857 | 0.3506 | survives |
| LmrHistoryDivisor | Soft % | 6.50 | 37.1667 | KILLED |
| LmrHistoryDivisor | Hard % | 13.00 | 33.6389 | KILLED |
| LmrHistoryDivisor | Soft/hard | 0.5000 | 1.1049 | KILLED |
| ProbcutMargin | Soft % | 6.50 | 29.6944 | KILLED |
| ProbcutMargin | Hard % | 10.00 | 32.5556 | KILLED |
| ProbcutMargin | Soft/hard | 0.6500 | 0.9121 | survives |
| RfpMargin | Soft % | 12.00 | 38.7500 | KILLED |
| RfpMargin | Hard % | 15.00 | 33.6389 | KILLED |
| RfpMargin | Soft/hard | 0.8000 | 1.1519 | survives |

20 KILLED, 4 survive, 0 ungraded.

History rates divide history-pruning takes by actual main plus qsearch nodes. Pooled rows sum both directions and compare the corresponding two baseline repeats.

## Table 1. One-step changes

| Setting | Direction | Soft changed | Soft % | Hard changed | Hard % | Soft/hard | History pruning soft/base | History pruning hard/base | Soft nodes/base | Soft median depth |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HistoryPruneDepth | minus | 11/1800 | 0.6111 | 466/1800 | 25.8889 | 0.0236 | 0.9884 | 0.9849 | 0.9990 | 8.0 |
| HistoryPruneDepth | plus | 0/1800 | 0.0000 | 294/1800 | 16.3333 | 0.0000 | 1.0003 | 0.9705 | 1.0000 | 8.0 |
| HistoryPruneMultiplier | minus | 434/1800 | 24.1111 | 559/1800 | 31.0556 | 0.7764 | 1.2134 | 1.4121 | 0.9827 | 8.0 |
| HistoryPruneMultiplier | plus | 351/1800 | 19.5000 | 553/1800 | 30.7222 | 0.6347 | 0.7907 | 0.7699 | 0.9888 | 8.0 |
| HistoryBonusQuadratic | minus | 720/1800 | 40.0000 | 619/1800 | 34.3889 | 1.1632 | 0.7249 | 0.8657 | 0.9503 | 8.0 |
| HistoryBonusQuadratic | plus | 677/1800 | 37.6111 | 579/1800 | 32.1667 | 1.1693 | 1.2683 | 1.2848 | 0.9527 | 8.0 |
| HistoryBonusLinear | minus | 695/1800 | 38.6111 | 591/1800 | 32.8333 | 1.1760 | 0.7982 | 1.0435 | 0.9645 | 8.0 |
| HistoryBonusLinear | plus | 700/1800 | 38.8889 | 605/1800 | 33.6111 | 1.1570 | 1.0272 | 1.0094 | 0.9640 | 8.0 |
| HistoryBonusMax | minus | 218/1800 | 12.1111 | 577/1800 | 32.0556 | 0.3778 | 1.0114 | 1.0398 | 0.9845 | 8.0 |
| HistoryBonusMax | plus | 189/1800 | 10.5000 | 584/1800 | 32.4444 | 0.3236 | 1.0196 | 1.1092 | 0.9896 | 8.0 |
| LmrHistoryDivisor | minus | 670/1800 | 37.2222 | 627/1800 | 34.8333 | 1.0686 | 0.9696 | 1.1180 | 0.9616 | 8.0 |
| LmrHistoryDivisor | plus | 668/1800 | 37.1111 | 584/1800 | 32.4444 | 1.1438 | 1.0956 | 1.1257 | 0.9731 | 8.0 |
| ProbcutMargin | minus | 549/1800 | 30.5000 | 579/1800 | 32.1667 | 0.9482 | 0.9701 | 1.0468 | 0.9623 | 8.0 |
| ProbcutMargin | plus | 520/1800 | 28.8889 | 593/1800 | 32.9444 | 0.8769 | 1.0241 | 1.0560 | 0.9839 | 8.0 |
| RfpMargin | minus | 694/1800 | 38.5556 | 604/1800 | 33.5556 | 1.1490 | 0.9692 | 1.1619 | 0.9463 | 8.0 |
| RfpMargin | plus | 701/1800 | 38.9444 | 607/1800 | 33.7222 | 1.1549 | 0.8172 | 1.0004 | 0.9684 | 8.0 |

## Table 2. Both directions pooled

| Setting | Direction | Soft changed | Soft % | Hard changed | Hard % | Soft/hard | History pruning soft/base | History pruning hard/base | Soft nodes/base | Soft median depth |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HistoryPruneDepth | pooled | 11/3600 | 0.3056 | 760/3600 | 21.1111 | 0.0145 | 0.9944 | 0.9777 | 0.9995 | 8.0 |
| HistoryPruneMultiplier | pooled | 785/3600 | 21.8056 | 1112/3600 | 30.8889 | 0.7059 | 1.0014 | 1.0910 | 0.9857 | 8.0 |
| HistoryBonusQuadratic | pooled | 1397/3600 | 38.8056 | 1198/3600 | 33.2778 | 1.1661 | 0.9970 | 1.0752 | 0.9515 | 8.0 |
| HistoryBonusLinear | pooled | 1395/3600 | 38.7500 | 1196/3600 | 33.2222 | 1.1664 | 0.9127 | 1.0264 | 0.9642 | 8.0 |
| HistoryBonusMax | pooled | 407/3600 | 11.3056 | 1161/3600 | 32.2500 | 0.3506 | 1.0155 | 1.0745 | 0.9871 | 8.0 |
| LmrHistoryDivisor | pooled | 1338/3600 | 37.1667 | 1211/3600 | 33.6389 | 1.1049 | 1.0330 | 1.1218 | 0.9673 | 8.0 |
| ProbcutMargin | pooled | 1069/3600 | 29.6944 | 1172/3600 | 32.5556 | 0.9121 | 0.9974 | 1.0514 | 0.9731 | 8.0 |
| RfpMargin | pooled | 1395/3600 | 38.7500 | 1211/3600 | 33.6389 | 1.1519 | 0.8923 | 1.0812 | 0.9573 | 8.0 |

## Table 3. First changed bestmove by game

First changes are recommendations on a fixed replay. The following search uses the recorded move. The 30–59 bin retains later first changes separately from unchanged games.

| Setting | Direction | Regime | Ply 0 | Plies 1–9 | Plies 10–29 | Plies 30–59 | No change |
|---|---|---|---:|---:|---:|---:|---:|
| HistoryPruneDepth | minus | soft | 0 | 0 | 1 | 1 | 28 |
| HistoryPruneDepth | minus | hard | 0 | 3 | 25 | 2 | 0 |
| HistoryPruneDepth | plus | soft | 0 | 0 | 0 | 0 | 30 |
| HistoryPruneDepth | plus | hard | 0 | 1 | 18 | 8 | 3 |
| HistoryPruneMultiplier | minus | soft | 0 | 7 | 15 | 7 | 1 |
| HistoryPruneMultiplier | minus | hard | 1 | 28 | 1 | 0 | 0 |
| HistoryPruneMultiplier | plus | soft | 0 | 2 | 16 | 9 | 3 |
| HistoryPruneMultiplier | plus | hard | 0 | 28 | 2 | 0 | 0 |

## Facts

- None of the pooled soft/hard changed-move ratios exceeded 1.5. Two were below 0.67: `HistoryPruneDepth` at 0.0145 and `HistoryBonusMax` at 0.3506. The two history-bonus coefficients, `LmrHistoryDivisor` and `RfpMargin` were above 1.0. The exact counts and rates are in Table 2.
- `HistoryPruneDepth` changed 11 of 3,600 soft-budget recommendations and 760 of 3,600 hard-budget recommendations. Increasing the setting to 4 changed zero soft bestmoves and 294 hard bestmoves. Its soft node count and history-pruning count still moved.
- `HistoryBonusQuadratic` changed the most soft recommendations in this sample, 1,397 of 3,600, two more than either `HistoryBonusLinear` or `RfpMargin`. `LmrHistoryDivisor` and `RfpMargin` shared the hard maximum at 1,211 of 3,600. All soft variant arms retained a median reported root depth of 8.
- With the lower multiplier, 29 of 30 hard games had a changed recommendation by ply 9 versus seven soft games. With the higher multiplier those counts were 28 and two. Table 3 preserves first changes after ply 29 separately from games with unchanged recommendations.
- Independently checked the earlier Job 3 A control noted by Opus. On the old counting build with PC20, the last reported PV head equals bestmove for all 206 soft searches with an 8,000-node ceiling hit and all 5,794 other A searches. [Job 3 PV readback](sol/job5/job3-cap-readback.txt)

## Build, settings and evidence

- Case A. GPT-6 (Codex), Linux x86_64. Unchanged Job 4 counting binary SHA-256 `63356d12c5505ab657e71ddd020e3ca27c8e8c6b4b1632bae343c57deef33333`, PC r15 from base `6b98f2170a3210e71beed04bbd2553972c253ed7` with the recorded PC, counter and buttons patches, GCC 14.2.0, CMake 4.2.3 Release, libstdc++ `6.0.33`, glibc 2.41 and x86-64-v4. [Job 4 build details](REPORT_sol_job4.md)
- Built-in AL1 s198 weights source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`, no external net, PC20 with one explicit option override per variant, Threads 1, Hash 16 MiB, OwnBook false, one PV. Button options were unused. [PC20 recipe](REPORT_sol_job2.md)
- The first 30 Job 3 games supplied exactly 1,800 positions. Full replay list SHA-256 `6d3343843f1bd6e9597f1e54ea64779fab78a1df64abb2431c749151e5a060a1`. Each game started with `ucinewgame` and a waited-on `isready`. The search received the original FEN plus preceding recorded moves. Soft used `go softnodes 2000`. Hard used `go nodes 20000`. The raw files preserve the last info line and CNT. Sidecars preserve every command, accepted overrides and timestamps. [Games](sol/job3/games.txt) · [Raw rows and metadata](sol/job5/raw) · [Clock stamps](sol/job5/stamps.txt)

From `forge-combo29/sol/job5`, reproduce the gates and three tables from the committed logs:

```sh
python3 summarize.py gates ../job3/games.txt raw ../job3/raw
python3 summarize.py tables ../job3/games.txt raw --prediction prediction.txt
```

## Suspicions

A shallower regime leaves fewer opportunities for an extra ply of history pruning or for the quadratic history bonus to reach its maximum. Those mechanisms are plausible explanations for the two low soft/hard ratios. The fixed replay did not isolate the mechanisms from changes in earlier searches and retained state.

## What I did not do

No owner-PC work, active standalone v3 net, tuner run, timing comparison, match or Elo measurement. Variants did not choose the moves subsequently replayed.

## What I am not sure about

The move-change fractions do not determine which moves are stronger. The ordering of sensitivities could differ with the PC's live net, step sizes or a game that follows a variant's own moves.

## Pre-commit readback

```text
M  forge-combo29/NOTES_sol.md
AM forge-combo29/REPORT_sol_job5.md
A  forge-combo29/sol/job5/aggregation-retry.txt
A  forge-combo29/sol/job5/gates-independent.txt
A  forge-combo29/sol/job5/gates.txt
A  forge-combo29/sol/job5/job3-cap-readback.txt
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-start-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusLinear-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusMax-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusMax-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusMax-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusMax-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusMax-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusMax-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusMax-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusMax-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusMax-start-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusMax-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-start-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryBonusQuadratic-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-start-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneDepth-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-max-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-max-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-start-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-zero-soft.jsonl
A  forge-combo29/sol/job5/raw/HistoryPruneMultiplier-zero-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-start-soft.jsonl
A  forge-combo29/sol/job5/raw/LmrHistoryDivisor-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/ProbcutMargin-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/ProbcutMargin-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/ProbcutMargin-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/ProbcutMargin-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/ProbcutMargin-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/ProbcutMargin-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/ProbcutMargin-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/ProbcutMargin-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/ProbcutMargin-start-soft.jsonl
A  forge-combo29/sol/job5/raw/ProbcutMargin-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/RfpMargin-minus-hard.jsonl
A  forge-combo29/sol/job5/raw/RfpMargin-minus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/RfpMargin-minus-soft.jsonl
A  forge-combo29/sol/job5/raw/RfpMargin-minus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/RfpMargin-plus-hard.jsonl
A  forge-combo29/sol/job5/raw/RfpMargin-plus-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/RfpMargin-plus-soft.jsonl
A  forge-combo29/sol/job5/raw/RfpMargin-plus-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/RfpMargin-start-soft.jsonl
A  forge-combo29/sol/job5/raw/RfpMargin-start-soft.jsonl.meta
A  forge-combo29/sol/job5/raw/base-hard.jsonl
A  forge-combo29/sol/job5/raw/base-hard.jsonl.meta
A  forge-combo29/sol/job5/raw/base-soft.jsonl
A  forge-combo29/sol/job5/raw/base-soft.jsonl.meta
A  forge-combo29/sol/job5/run_variants.py
A  forge-combo29/sol/job5/stamps.txt
A  forge-combo29/sol/job5/start-values.txt
A  forge-combo29/sol/job5/step0-count.raw.txt
A  forge-combo29/sol/job5/step0.summary.txt
A  forge-combo29/sol/job5/summarize.py
?? forge-combo29/sol/job2/__pycache__/
forge-combo29/sol/job5:
aggregation-retry.txt
gates-independent.txt
gates.txt
job3-cap-readback.txt
prediction.txt
raw
run_variants.py
stamps.txt
start-values.txt
step0-count.raw.txt
step0.summary.txt
summarize.py

forge-combo29/sol/job5/raw:
HistoryBonusLinear-minus-hard.jsonl
HistoryBonusLinear-minus-hard.jsonl.meta
HistoryBonusLinear-minus-soft.jsonl
HistoryBonusLinear-minus-soft.jsonl.meta
HistoryBonusLinear-plus-hard.jsonl
HistoryBonusLinear-plus-hard.jsonl.meta
HistoryBonusLinear-plus-soft.jsonl
HistoryBonusLinear-plus-soft.jsonl.meta
HistoryBonusLinear-start-soft.jsonl
HistoryBonusLinear-start-soft.jsonl.meta
HistoryBonusMax-minus-hard.jsonl
HistoryBonusMax-minus-hard.jsonl.meta
HistoryBonusMax-minus-soft.jsonl
HistoryBonusMax-minus-soft.jsonl.meta
HistoryBonusMax-plus-hard.jsonl
HistoryBonusMax-plus-hard.jsonl.meta
HistoryBonusMax-plus-soft.jsonl
HistoryBonusMax-plus-soft.jsonl.meta
HistoryBonusMax-start-soft.jsonl
HistoryBonusMax-start-soft.jsonl.meta
HistoryBonusQuadratic-minus-hard.jsonl
HistoryBonusQuadratic-minus-hard.jsonl.meta
HistoryBonusQuadratic-minus-soft.jsonl
HistoryBonusQuadratic-minus-soft.jsonl.meta
HistoryBonusQuadratic-plus-hard.jsonl
HistoryBonusQuadratic-plus-hard.jsonl.meta
HistoryBonusQuadratic-plus-soft.jsonl
HistoryBonusQuadratic-plus-soft.jsonl.meta
HistoryBonusQuadratic-start-soft.jsonl
HistoryBonusQuadratic-start-soft.jsonl.meta
HistoryPruneDepth-minus-hard.jsonl
HistoryPruneDepth-minus-hard.jsonl.meta
HistoryPruneDepth-minus-soft.jsonl
HistoryPruneDepth-minus-soft.jsonl.meta
HistoryPruneDepth-plus-hard.jsonl
HistoryPruneDepth-plus-hard.jsonl.meta
HistoryPruneDepth-plus-soft.jsonl
HistoryPruneDepth-plus-soft.jsonl.meta
HistoryPruneDepth-start-soft.jsonl
HistoryPruneDepth-start-soft.jsonl.meta
HistoryPruneMultiplier-max-soft.jsonl
HistoryPruneMultiplier-max-soft.jsonl.meta
HistoryPruneMultiplier-minus-hard.jsonl
HistoryPruneMultiplier-minus-hard.jsonl.meta
HistoryPruneMultiplier-minus-soft.jsonl
HistoryPruneMultiplier-minus-soft.jsonl.meta
HistoryPruneMultiplier-plus-hard.jsonl
HistoryPruneMultiplier-plus-hard.jsonl.meta
HistoryPruneMultiplier-plus-soft.jsonl
HistoryPruneMultiplier-plus-soft.jsonl.meta
HistoryPruneMultiplier-start-soft.jsonl
HistoryPruneMultiplier-start-soft.jsonl.meta
HistoryPruneMultiplier-zero-soft.jsonl
HistoryPruneMultiplier-zero-soft.jsonl.meta
LmrHistoryDivisor-minus-hard.jsonl
LmrHistoryDivisor-minus-hard.jsonl.meta
LmrHistoryDivisor-minus-soft.jsonl
LmrHistoryDivisor-minus-soft.jsonl.meta
LmrHistoryDivisor-plus-hard.jsonl
LmrHistoryDivisor-plus-hard.jsonl.meta
LmrHistoryDivisor-plus-soft.jsonl
LmrHistoryDivisor-plus-soft.jsonl.meta
LmrHistoryDivisor-start-soft.jsonl
LmrHistoryDivisor-start-soft.jsonl.meta
ProbcutMargin-minus-hard.jsonl
ProbcutMargin-minus-hard.jsonl.meta
ProbcutMargin-minus-soft.jsonl
ProbcutMargin-minus-soft.jsonl.meta
ProbcutMargin-plus-hard.jsonl
ProbcutMargin-plus-hard.jsonl.meta
ProbcutMargin-plus-soft.jsonl
ProbcutMargin-plus-soft.jsonl.meta
ProbcutMargin-start-soft.jsonl
ProbcutMargin-start-soft.jsonl.meta
RfpMargin-minus-hard.jsonl
RfpMargin-minus-hard.jsonl.meta
RfpMargin-minus-soft.jsonl
RfpMargin-minus-soft.jsonl.meta
RfpMargin-plus-hard.jsonl
RfpMargin-plus-hard.jsonl.meta
RfpMargin-plus-soft.jsonl
RfpMargin-plus-soft.jsonl.meta
RfpMargin-start-soft.jsonl
RfpMargin-start-soft.jsonl.meta
base-hard.jsonl
base-hard.jsonl.meta
base-soft.jsonl
base-soft.jsonl.meta
```
