# REPORT glmflash5 — JOB 9 — the whole switch against its saving half (on − shal), 20,000 nodes

Branch `cursor/glmflash5-work-cb5c`. PATCHED = job 8's exe (base tree 6b98f217 + kimi5's
LmrDS_tunables.patch.txt on a COPY; no engine source committed). times: pasted from
`tests_glmflash5_job9/stamps.txt` in section 9; nothing typed.

## 1. What was asked, the answer, how sure

Asked: the third side of the triangle — the whole switch (on) head-to-head against its saving
half (shal) at 20,000 nodes, then whether the three matches close.

Answer: **M2 (on − shal): +3.5 Elo, 95 % pair interval [−7.0, +13.9], 1,000 pairs (2,000 games,
COMPLETE in 11:20), 20,000 nodes, built-in net, PATCHED exe; 0 abnormal endings. Closure =
7.2 − (−4.00) − (+3.47) = +7.73, 95 % error ±17.16 (root of the three squared half-widths 8.15 /
10.91 / 10.43) → the triangle CLOSES: the three matches tell one story.**

One sentence for line 3: **at 20,000 nodes on this tree the deeper half's extra value (on−shal
= +3.5 [−7.0, +13.9]) cannot be separated from zero by 1,000 pairs — "worth its nodes" and "not
worth them" both stay open; what IS settled is consistency: the three results close as a
triangle within ±17 Elo.**

How sure: sure of the mechanics (sha equality with job 8's exe proven first; all three step-1
rows exact including the clamp control; probe counts 10/10 − 0 − 10/10 − 0; 2000/2000
validation). The closure number inherits the OLD pool's +7.2 (Fable's number, not recomputed by
me) and is one look per side.

## 2. Step 1 — the exe and three rows, all exact

PATCHED sha256 `fb9152ca0a7cb3ce336decc2637f6e715be9206b979793dbedfa18ce1c4324d7` — EQUAL to
job 8's recorded sha256 (`p9_sha.txt` beside `tests_glmflash5_job8/exe_sha256_8.txt`) → go on
without a rebuild.

`go depth 12`, Threads 1, Hash 16, ucinewgame + isready before every go, first three lines of
kimi5's first200.fens, nodes of the last info line (`p9_on.txt`, `p9_shal.txt`, `p9_clamp.txt`):

| run | nodes | known answer |
|-----|-------|--------------|
| PATCHED, on | 26641, 30896, 68347 | same ✓ |
| PATCHED, shal | 32353, 38250, 68550 | same ✓ |
| PATCHED, on + LmrDeeperBase 100001 | 32353, 38250, 68550 (= shal — the value clamps) | same ✓ |

The control row's line, pasted from the run's captured output: `info string invalid value for
option LmrDeeperBase` — my harness SEES it (the source: the patch gives the option max 100000;
uci.cpp 278–287 of this tree reports the out-of-range integer and still clamps — Fable's
prediction, confirmed on my machine).

## 3. M2: games by ending FIRST (2,000 games)

| ending | count |
|--------|-------|
| White mates | 632 |
| Draw by 3-fold repetition | 590 |
| Black mates | 492 |
| Draw by insufficient mating material | 142 |
| Draw by fifty moves rule | 135 |
| Draw by stalemate | 9 |
| loss on time cand / base | 0 / 0 (fixed nodes; checked) |
| illegal / disconnect / crash | 0 / 0 / 0 |

W-L-D (cand) 572-552-876; pairs 1,000; n5 = [57, 230, 407, 248, 58] (= fastchess's own Ptnml);
**Elo +3.47, 95 % pair interval [−6.96, +13.91]** (fastchess: +3.47 ± 10.43, LOS 74.32 % — same);
**COMPLETE** (2,000/2,000; fastchess total 00:11:20). Validation line: 2000/2000 rows equal
fastchess's own lines, 0 mismatches. Last 40 lines: `M2_last40.txt`.

Command (`cmd_M2.txt`): cand = PATCHED `option.LmrDeeperShallower=true`; base = PATCHED
`option.LmrDeeperShallower=true option.LmrDeeperBase=100000`; `-each proto=uci nodes=20000`;
`-openings file=openings_job9.epd format=epd order=sequential -srand 9370 -rounds 1000 -games 2
-repeat -concurrency 4 -recover -ratinginterval 100 -pgnout file=M2.pgn min=true`.
Openings: book minus the openings used in jobs 2,3,5,6,7,8 (2,714 distinct removed; 2,629,322
left; Random(9900); 5,000 lines) — first line
`rnbqkb1r/pp3ppp/3ppn2/8/4P3/1PN2N2/1BPP1PPP/R2QKB1R w KQkq - 2 7`, order sequential.
prediction.txt committed BEFORE the first game: mine +11, wrong outside [−3, +25] — built on the
triangle arithmetic (7.2 − M1's −4.0) and on the node rows (on 26641 < shal 32353: the shallower
re-search that flips a bound forces a second full re-search, so "shal" is the BIGGER tree — the
surprise I recorded in the prediction). Observed +3.47: inside my range; the prediction's
reasoning survives, its point value was high by ~7.6 (inside the error).

## 4. Step 2 — the probe (three counts)

Ten games, PATCHED both sides, cand = on, base = shal, nodes=20000, engine I/O logged
(`probe_M2j9.log`): **cand received LmrDeeperShallower 10/10 and LmrDeeperBase 0 times; base
received BOTH 10/10 and 10/10; lines with `unknown option` or `invalid value`: 0.** (Probe used
openings_job7.epd lines 1–10, delivery only.)

## 5. Step 4 — the triangle

closure = (on−none) − (shal−none) − (on−shal) = 7.2 − (−4.00) − (+3.47) = **+7.73**
half-widths: pool 8.15 (Fable's [−1.0, +15.3]), M1 10.91 (job 8), M2 10.43 (this job);
95 % error = √(8.15² + 10.91² + 10.43²) = **±17.16** → |7.73| < 17.16 → **closes**.
No swapped-side hunt needed (all three matches were counted the same way, each validated row by
row). Noted for honesty: the closure carries Fable's +7.2 pool (I did not recompute it) and
"under an ASSUMED 168 Elo per doubling" arithmetic from job 7 stays out of these first lines, as
Fable instructed.

## 6. From my partners

- deepseek5's job-14 headline is RETRACTED by Fable ("the gap, not the excess" — false; both
  classes grow as pieces come off). I built nothing on it; the gap-cap match on the PC is Fable's
  line of work, not mine.
- Fable's SoundMatePruning three-part decomposition (in-check free, PV 8–9 %, mate-score ×3.6 on
  bare won endings) — noted for job 10 planning; deepseek5 is writing the three as options on my
  tree; a match of the free part is a candidate.
- The correction I keep: a number that was not measured is written "not measured" (my job 7
  cost line now lives under an ASSUMED-168 flag in its report — flagged there).

## 7. What I did NOT do

- No second seed of M2 (one look; the job's plan is 1,000 pairs, complete).
- No re-derivation of the +7.2 pool from the older matches' raw games (not on my branch).
- The other three tunables (LmrDeeperDepthMul, LmrShallowerBase, LmrShallowerDepthMul) stay at
  defaults, unprobed beyond presence.

## 8. What I am NOT sure about

- Whether the deeper half is worth its nodes: +3.5 [−7.0, +13.9] — cannot say at this size; the
  triangle's closure says the THREE LOOKS agree, not that any of them is precise.
- The closure's ±17.16 treats the three looks as independent (different openings, seeds); the
  two PATCHED-side matches share the same exe and machine — some correlation is possible, which
  would make the true error smaller, not larger.
- The stalemate count (9) and each ending string come from fastchess unverified by replay.

## 9. UTC stamps (pasted verbatim from stamps.txt)

```
2026-11-16T08:14:34Z job 9 file read; step 1 begins
2026-11-16T08:14:37Z step 1 done (sha equal; rows + clamp control exact)
2026-11-16T08:14:43Z probe done rc=0
2026-11-16T08:14:52Z prediction + openings_job9 done
2026-11-16T08:14:52Z cmd_M2.txt written; launching M2
2026-11-16T08:26:13Z M2 finished rc=0 after 681s
2026-11-16T08:26:20Z M2 stats done (complete)
```

## 10. Real output of `git status --short` and `ls` of the job folder (verbatim, 08:26:26Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job9/
=== ls of my job9 folder:
cmd_M2.txt
config_M2.json
gamelist_M2j9.txt
m2j9_stats.txt
M2j9_stdout.txt
M2_last40.txt
make_openings_job9.py
openings_job9.epd
p9_clamp.txt
p9_on.txt
p9_shal.txt
p9_sha.txt
prediction.txt
probe_M2j9.log
probe_M2j9_stdout.txt
stamps.txt
```

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
