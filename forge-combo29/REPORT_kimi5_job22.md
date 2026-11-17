# kimi5 job 22 report — the singular step as three options (NegExtTt, NegExtCut, MultiCutScore) on the PC+A6 build

Asked: port the singular block's three branches as UCI options onto the PC build + my job-19 A6 patch, prove it
against Opus's known rows, scale it with depth, and count which branch fires. Answer: **the port is byte-equal to
Opus's on every known row (10 of 10 row-hash pairs, 200/200 O and 353/353 G per setting, 3,318 searches); all Step-0
numbers exact; all Step-3 known answers hold to the unit.** Sure: as sure as this harness gets — the only failures
were my own (harness, caught and rerun; two of three predictions KILLED, graded below).

(1) **Step 0: MET** (in `step0_v2/`; the first attempt, `step0/`, sent no options — my script looked for
`s14.opt`/`pc20.opt` in the job-22 folder; kept as raw evidence, rerun into a new folder, never deleted).
(2) **Prediction graded:** P1 sf/base d14 G: guessed 0.945, kill range [0.905, 0.985], measured **1.0296** →
**KILLED**. P2 extra multi-cuts of MultiCutScore 1 per 1,000 tests (base, G, d12): guessed 28, kill range [12, 55],
measured **83.3** → **KILLED**. P3 most G positions changed: guessed MultiCutScore 1, measured mc1 348 vs nc2 342,
nt3 332 → **survives**. (3) Step 1 below. (4) Step 2 table below. (5) Step 3 tables below (1,106 searches summed).

## Step 0 (raw files in `tests_kimi5_job22/step0_v2/`, fresh process per line; build stamp with
## `ls -l --time-style=full-iso` in `step0_v2/build_stamp.txt`)

Build = 6b98f217 + `pc_r15.patch` (swarm file 5 lines 56-2374, sha256 `d6bd72c531f785f4...` re-verified) + my job-19
`SingularA6.pc.patch.txt` + this job's `SingularStep.pc.patch.txt`, g++ 13.3.0, Release,
`-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1` (guard arrives; a CMake *variable* would be silently unused — job-20
lesson), AVX-512+BMI2 present, plain exe sha256 `62c9db33dac3110d...`.

| settings | bench 11 | bench 13 | bench 16 | go perft 5 | file |
|---|---|---|---|---|---|
| none | 312866 ✓ | 862329 ✓ | 3024920 ✓ | 4865609 ✓ | `none_bench11/13/16.txt`, `none_perft5.txt` |
| S14 | 242796 ✓ | 656517 ✓ | – | – | `s14_bench11/13.txt` |
| PC20 | 278024 ✓ | 587276 ✓ | – | – | `pc20_bench11/13.txt` |

`uci_list.txt` shows `NegExtTt` spin default 2 min 0 max 3, `NegExtCut` spin default 1 min 0 max 3, `MultiCutScore`
spin default 0 min 0 max 1, plus job 19's `SingularNonCut` and `TripleExtMargin`.

## The port (deliverable)

`tests_kimi5_job22/SingularStep.pc.patch.txt` sha256 `a40685dd11cc920a02f0aa4d84521ff496963268139aed425502129eb859493a`;
applies `patch -p1 -F0`, zero fuzz, on 6b98f217 + pc_r15 + SingularA6 (verified on a fresh copy, `diff -q` of the
applied file against the built one: equal). Three hunks: declarations, option-table rows, the branch block.
The three branches in the PC build (6b98f217 + pc_r15 + A6, before this job's edits), `src/search.cpp`:
branch (1) multi-cut test at **line 2218** (`return singular_beta;` at 2219); branch (2) `tt_score >= beta` →
`extension = -2` at **lines 2220-2221**; branch (3) `cut_node` → `extension = -1` at **lines 2222-2223**.
At the defaults the ternaries evaluate to today's test and today's values (MultiCutScore 0 → `singular_beta >= beta`,
return `singular_beta`; NegExtTt 2 → -2; NegExtCut 1 → -1) — proven by Step 0's unchanged benches and the identity
below. Show it again: `sed -n 2210,2224p src/search.cpp` on that tree.

## Step 1 — PC20, `go depth 12` (rows in `rows/*_d12.json`, .meta beside each, checker `check_s1_j22.py`,
## output `check_s1.txt`)

Every row set equals Opus's known rows position by position, node count AND best move, via file 22's row hashes:

| setting | O (200) | G (353) |
|---|---|---|
| base | n fd609b7b1a8dd179 m 14583c86b5f56cb6 ✓ | n 60b6916f01395e99 m 0846f027e7e9b77e ✓ |
| NegExtTt 3 | n 163ec0bd9bc90140 m 555369f411e75bd5 ✓ | n b5da8f033e46f6ce m 53678ff52ed6f21c ✓ |
| NegExtCut 2 | n 4bc99ee17d45ade1 m e8237ae038b24511 ✓ | n 7ab800b9941d73c9 m 77dfb085c5c1a49b ✓ |
| MultiCutScore 1 | n 3e443de62239d7ef m 18173b4af5a3a2e0 ✓ | n 2ee86e30605f3b86 m 92540e0591a1ed48 ✓ |
| sf | n 29ce1577d5dc8322 m 6dcb3071f9d4ff4f ✓ | n e2ea641e63a75d2a m e8cb4719ff4c234d ✓ |

All ten sums and first-threes also equal the file's numbers (DONE lines in `rows/*_d12.stdout`). Identity (the three
options SENT at their defaults): equal to base on 200/200 O and 353/353 G, nodes and best moves. Options proven to
ARRIVE: `rows/mc1_O_d12_input.log` has `setoption name MultiCutScore value 1`, `rows/sf_G_d12_input.log` has all
three sf lines, `rows/ident_O_d12_input.log` all three at defaults.

Positions where the ON setting changes the node count vs base (best moves changed in parentheses): nt3 O 200 (40),
G 332 (54); nc2 O 199 (44), G 342 (70); mc1 O 200 (49), G 348 (81); sf O 200 (46), G 348 (89).

## Step 2 — depth scaling, PC20 (`step2_j22.py`, bootstrap 95 % over positions, 2000 resamples, seed 12;
## output `step2_table.txt`)

```
set depth  setting      nodes   ratio            boot95 bm!=base
O     12     base    8315168  1.0000 [ 1.0000, 1.0000]        0
O     12      nt3    8126584  0.9773 [ 0.9343, 1.0145]       40
O     12      nc2    8085814  0.9724 [ 0.9269, 1.0116]       44
O     12      mc1    8052011  0.9684 [ 0.9189, 1.0103]       49
O     12       sf    7899876  0.9501 [ 0.9012, 0.9933]       46
O     14     base   19377109  1.0000 [ 1.0000, 1.0000]        0
O     14      nt3   18484368  0.9539 [ 0.9061, 0.9990]       43
O     14      nc2   18866478  0.9736 [ 0.9302, 1.0128]       31
O     14      mc1   18761560  0.9682 [ 0.9174, 1.0145]       40
O     14       sf   18231642  0.9409 [ 0.8896, 0.9867]       44
G     12     base   17611204  1.0000 [ 1.0000, 1.0000]        0
G     12      nt3   17539646  0.9959 [ 0.9591, 1.0257]       54
G     12      nc2   17298748  0.9823 [ 0.9431, 1.0180]       70
G     12      mc1   16993960  0.9650 [ 0.9249, 1.0024]       81
G     12       sf   16894018  0.9593 [ 0.9147, 1.0012]       89
G     14     base   41052503  1.0000 [ 1.0000, 1.0000]        0
G     14      nt3   40119915  0.9773 [ 0.9191, 1.0239]       62
G     14      nc2   40205806  0.9794 [ 0.9295, 1.0237]       82
G     14      mc1   40025998  0.9750 [ 0.9150, 1.0238]       86
G     14       sf   42265855  1.0296 [ 0.9753, 1.0824]       84
```

Every single option shrinks both trees at both depths — except **sf on G at depth 14 GROWS the tree 3.0 %**
(1.0296, interval [0.9753, 1.0824] just clears 1) while it shrinks O 5.9 % at the same depth. The three parts are
sub-additive at d12 on G (0.9959 · 0.9823 · 0.9650 = 0.944 < 0.9593 measured sf) and flip sign jointly at d14.

## Step 3 — which branch fires (counter patch `SingularStepCount.pc.patch.txt` sha256
## `12087df6a968b678561b3b679dc31cf7505570ef1e442841971f9ca0b4dd22e2`, applies `patch -p1 -F0` on
## 6b98f217 + pc_r15 + SingularA6 + SingularStep — verified; counter exe `e31519cf...` ≠ plain exe `62c9db33...`;
## counters compile-flagged `FORGE_SNS_CHECK`, observe-only; summer `sum_sns.py`, output `step3_table.txt`)

Known answers, all met: (a) the counting build counts the same nodes as the plain build at both settings —
cntbase 8,315,168 / 17,611,204 and cntsf 7,899,876 / 16,894,018 equal Step 1's sums to the node; (b) the TAKEN
classes add up to the tests run in all four runs (summer prints OK); (c) every test in "today's but NOT
MultiCutScore 1's" has a mate score as the excluded score — counted: 23 (O base), 422 (G base), 12 (O sf),
344 (G sf). Cross-check against file 22 itself: my base-G counts reproduce its numbers exactly (31,604 multi-cuts,
10,247 branch (2), 15,219 branch (3) in 176,423 verifications). Internal closure: under sf, taken multi-cuts equal
wtoday − wmate + wnew to the unit (G: 31,607 − 344 + 16,609 = 47,872; O: 11,095 − 12 + 6,250 = 17,333).

Per-search SNS lines in `rows/cnt*_full.txt`; totals over ALL searches (200 + 353 + 200 + 353 = **1,106 summed**):

| run | tests | sing | mc | b2 | b3 | none | wtoday | wnew | wmate |
|---|---|---|---|---|---|---|---|---|---|
| base O d12 | 48,220 | 19,360 | 11,268 | 6,978 | 5,010 | 5,604 | 11,268 | 6,025 | 23 |
| base G d12 | 176,423 | 111,221 | 31,604 | 10,247 | 15,219 | 8,132 | 31,604 | 14,693 | 422 |
| sf O d12 | 47,166 | 18,830 | 17,333 | 2,361 | 3,223 | 5,419 | 11,095 | 6,250 | 12 |
| sf G d12 | 175,511 | 109,291 | 47,872 | 2,698 | 8,137 | 7,513 | 31,607 | 16,609 | 344 |

The counters' answer: Stockfish's form adds **83.3 extra multi-cuts per 1,000 tests on game positions** (14,693;
openings 124.9, 6,025) — against 179.1 today's multi-cuts per 1,000 on G (so +47 % more cutoffs where it fires) —
and loses 2.4 per 1,000 to mate scores (422). The negative branches fire, under base on G, at 58.1 (branch (2),
tt-fail-high) and 86.3 (branch (3), cut node) per 1,000 tests; on openings 144.7 and 103.9. Under sf the taken
branch-(2)/(3) rates drop to 15.4/46.4 on G (the extra multi-cuts eat the branch-(2) pool first, as P2's reasoning
said — but there were three times more of them than guessed).

## Step table

| step | state | evidence | result |
|---|---|---|---|
| patch + builds | done | `SingularStep.pc.patch.txt`, `step0_v2/build_stamp.txt` | -F0 verified; exe `62c9db33...` |
| Step 0 | done | `step0_v2/` (first attempt `step0/` kept) | 8/8 exact, uci names/ranges correct |
| prediction | done | `prediction.txt` (own commit 21:04:20Z, before first run 21:04:55Z) | P1, P2 KILLED; P3 survives |
| Step 1 | done | `rows/*_d12.*`, `check_s1.txt` | 10/10 hash pairs equal; identity 553/553 |
| Step 2 | done | `rows/*_d14.*`, `step2_table.txt` | table above; sf G d14 grows |
| Step 3 | done | `SingularStepCount.pc.patch.txt`, `rows/cnt*`, `step3_table.txt` | all known answers met |

## Findings

1. `src/search.cpp:2218-2223` (PC+A6 tree): the three branches, line numbers above. Reproduce: apply the chain,
   `sed -n 2210,2224p`.
2. sf's d14 G growth (1.0296) coexists with every part shrinking at both depths — an interaction, not a sum.
3. Under MultiCutScore 1 the taken multi-cut count equals wtoday − wmate + wnew exactly on both sets: the fail-soft
   excluded score is what makes the extra cutoffs exist at all (under fail-hard, `singular_score` could never exceed
   `singular_beta` and wnew would be structurally 0).

Suspicions, not proven: the d14 G growth likely comes from MultiCutScore 1 returning `singular_score` (a fail-soft
score that can sit far above `singular_beta`) into parent nodes that then re-search — consistent with the growth
appearing only when all three are on and only at the deeper depth — but I ran no experiment that isolates the
returned-value effect from the extra-cutoff effect. Also suspicious: wmate > 0 means the excluded search returns
mate scores often enough (422 on G) to matter for a "never return mate from a verification" variant; not chased.

## From my colleagues

deepseek5 (`for-fable-and-opus/deepseek5-work`, read 21:02): newest notes — the stage-label one-late lesson (count a
state variable at the moment the event happens), the stand5 self-play runner template, Killer/CounterMove regret
rates. Applied: its "count at the event" lesson is exactly how the SNS counters record the taken branch (inside the
branch itself, not reconstructed after). glmflash5: **the branch `for-fable-and-opus/glmflash5-work` does not exist**
(fetch failed); said so here as ordered, nothing to apply. My own job-21 notes (opt files as base+override; guard via
CMAKE_CXX_FLAGS; never inline backgrounding) were applied — the identity setting caught nothing this time because
the .opt composition was right.

## What I did NOT do

No match games (not asked). No mate-variant experiment (the wmate counts are reported, not explained away). Job 23
(LmrFine) not touched — it is the NEXT job; its file was read as ordered and holds no corrections to job 22. The
first step0 attempt's raw files were kept (`step0/`), not deleted.

## What I am NOT sure about

The mechanism of sf's d14 G growth (above). Whether wnew's rate is stable with depth (only d12 counted — the job
asks d12 only). The 100-minute rule: no other claim existed; nothing to judge.

## A better way

The WOULD classes were hardcoded in the engine (three `if`s). Better: print the per-test triple
`(singular_beta, beta, singular_score, taken_branch)` — one short line per test, ~500 per search here — and compute
every would-class offline. Cost: one more counter line per test (I/O only, still observe-only); gain: any future
MultiCutScore variant (e.g. "not a WIN mate score only", "score capped at beta") is re-classified from the SAME raw
files without a new build, and the taken/would closure checks become arithmetic over one stream instead of parallel
counter blocks that can drift. Check that it is better: recompute this report's wtoday/wnew/wmate from the triples
and require equality with the counter build's lines on the same 1,106 searches.

## Times and model

times: see `tests_kimi5_job22/stamps.txt` (run start 21:01:54Z, claim 21:02:23Z, report commit below). Model:
Kimi K3 (running as "kimi5"). `git status --short` and `ls -R` of the job folder: the last command before the
report commit, in `tests_kimi5_job22/final_ls.txt`.
