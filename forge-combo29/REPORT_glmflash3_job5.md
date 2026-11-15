# glmflash3 job 5 report (2026-11-15)

## 1. First line

**At 80,000 nodes a move, on this tree, in 800-game matches: the Asp pair alone gains +8.3 Elo
(95 % pair interval [−6.6, +23.2]); eval swing at strength 12 alone gains +18.3 [+3.3, +33.3].
Beside the 20,000-node figures (+13.5 [+5.7, +21.0] pooled for the Asp pair over three seeds;
+20.7 [+7.2, +34.2] for swing@12): NEITHER figure separates from its 20,000-node value — the
800-game intervals are too wide to confirm or refute a shrink of a few Elo, and both point
estimates sit a little below their 20k values. What the depth matches DO show: swing strength 12
(+18.3) stays ahead of strength 24 (+6.8 [−9.2, +22.8], D3) and of the Asp pair (+8.3) at depth,
matching the 20k ordering.**

Cut or not reached, first paragraph as asked: C, D1 and D2 completed their prescriptions
(300/300, 800/800, 800/800; the C-derived rate 0.688 games/s predicted D1 at ~1160 s, measured
1450-1570 s — the rate estimate was ~20 % optimistic, the deadlines were caps and held). D3 was
cut at 670 of 800 games by its deadline; its statistics use complete pairs only (334 pairs, 2
one-game rounds dropped). **D4 (Asp + swing 12 together) was not started**: after D3 there were
~340 s left, below the 420 s floor my chain set for starting a match; D4 is the job's first-cut
match and it was cut all the way to zero.

## 2. Known answers

Tree: commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (the same base commit as job 4, without
the B1 patch — the job says the two do not stack) plus `opus_r13/p1/packc28/packc28_port.patch`
(branch `opus-r13-p1-nearmiss-ports`; `patch -p1`, rc 0, no rejects; 113 lines, touches
src/search.cpp among others). Build flags (once, every build):
`cmake -S pk -B build-pk -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1"`.
Fresh engine process per bench; input: Threads 1, Hash 16, OwnBook false, then the option lines
of the config. Raw outputs `saved5/*.out`.

The `uci` answer lists all four options (checked first, as the job required — the define arrived):
`AspFailHighReduce type spin default 0 min 0 max 1`, `AspFailHighMaxReduce type spin default 3 min 1 max 6`,
`EvalSwingMult type spin default 0 min 0 max 64`, `EvalSwingMax type spin default 200 min 50 max 400`
(`uci_options_list.out`).

| config | command | expected | printed | match |
|---|---|---|---|---|
| no option | bench 11 | 312866 | 312866 | yes |
| no option | bench 13 | 862329 | 862329 | yes |
| no option | go perft 5 | 4865609 | 4865609 | yes |
| Asp 1+3, Swing 24+200 | bench 13 | 690187 | 690187 | yes |
| Asp 1+3 alone | bench 13 | (new) | **649268** | — |
| Swing 12+200 alone | bench 13 | (new) | **748790** | — |

## 3. The probes

- **probe_d1**: cand `Threads 1`, `Hash 16`, `OwnBook false`, `AspFailHighReduce 1`,
  `AspFailHighMaxReduce 3`; base the first three only (probe_d1.txt, both games).
- **probe_d2**: cand adds `EvalSwingMult 12`, `EvalSwingMax 200` (probe_d2.txt).
- **probe_d3**: cand adds `EvalSwingMult 24`, `EvalSwingMax 200` (probe_d3.txt).
- **probe_d4 never ran** (its match was not started).
All probes: both sides received the three base options first, in order, in both games; the cand
options arrived after them, in the order given.

## 4. The matches

| match | nodes | cand options | base options | seed | games (complete pairs used) | W-L-D | fastchess Elo ± | my Elo [95 % pair] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|---|
| C | 20000/10000 | none | none | 7350 | 300 / 300 (150 pairs) | 187-25-88 (fast) | +209.91 ± 32.71 | +209.9 [+178.8, +244.4] | 0 |
| D1 | 80000 | Asp 1+3 | none | 7351 | 800 / 800 (400 pairs) | 218-199-383 | +8.25 ± 14.86 | +8.3 [−6.6, +23.2] | 0 |
| D2 | 80000 | Swing 12+200 | none | 7352 | 800 / 800 (400 pairs) | 212-170-418 | +18.26 ± 14.98 | +18.3 [+3.3, +33.3] | 0 |
| D3 | 80000 | Swing 24+200 | none | 7353 | 670 / 800 (334 complete pairs, 2 one-game rounds dropped) | 170-157-341 | +4.04 ± 16.59 (602-game snapshot) | +6.8 [−9.2, +22.8] | 0 |
| D4 | 80000 | Asp 1+3, Swing 12+200 | none | 7354 | not started (no time left after D3) | — | — | — | — |

Match summary against the 20,000-node figures from the other helpers' pooled results: Asp pair
+13.5 [+5.7, +21.0] (3 seeds) -> here +8.3 [−6.6, +23.2] (1 seed, 800 games); swing@12 +20.7
[+7.2, +34.2] -> here +18.3 [+3.3, +33.3]; swing@24 +6.6 [−1.1, +14.2] (pooled) -> here +6.8
[−9.2, +22.8]. Every depth interval contains its 20k point estimate; no shrink is demonstrated,
and none is excluded for the Asp pair.

## 5. Files of the repository I opened

- `opus_r13/p1/packc28/packc28_port.patch` (branch `opus-r13-p1-nearmiss-ports`) — read via `git show`, applied (no rejects), and its search.cpp hunks read around every hook it adds.
- The d4f43124 tree (same worktree copy as job 4): the packc28 option handlers and their search hooks in `src/search.cpp`/`src/uci.cpp` (the Asp pair's aspiration-fail-high reduction site and the eval-swing multiplier's use), `CMakeLists.txt` (the `FORGE_EXPOSE_TUNABLES` option gate).
- Job 4's report of the same tree served for the shared build recipe; no new engine file beyond those.
No engine source modified in the repository.

## 6. Stamps of every step

All UTC from `/tmp/g3job5/stamps.txt` (committed). Job start (reading file 5) ~20:07:53; budget
end (90 min) 21:37:53; the 80-min stop-and-write mark 21:27:53.

| step | start | end | note |
|---|---|---|---|
| packc28 patch fetched + applied | 20:07:5x | 20:08:0x | rc 0, no rejects |
| build pk | 20:08:03 | 20:08:09 | with the tunables define |
| uci options listed + known-answer battery | 20:08:1x | 20:08:2x | 6 benches, file mtimes in saved5/ |
| chain launch | 20:08:22 | — | |
| control C | 20:08:22 | 20:10:11 | 300/300, elapsed 109 s → **rate_C = 2.752 games/s**; rate_D = rate_C/4 = **0.688/s** (the job's 4x factor) |
| probe d1 + D1 | 20:10:11 | 20:34:23 | deadline cap 2061 s; completed 800/800 in 1448 s (**measured 0.552/s**) |
| probe d2 + D2 | 20:34:28 | 21:00:33 | cap 2061 s; completed 800/800 in 1565 s (**measured 0.511/s**) |
| probe d3 + D3 | 21:00:39 | 21:20:59 | deadline 1220 s (STOP-derived); **cut at 670/800** |
| D4 | — | — | **not started**: LEFT4 ≈ 340 s < the chain's 420 s start floor |
| report + commit + push | 21:21 | ~21:30 |

Deadline derivation as prescribed: every later limit came from C's measured rate (2.752/s) with
the job's 4x factor → 0.688/s predicted → D1/D2 caps sized so both could complete their 800 games
with margin; the measured rate came out 0.51-0.55/s (the per-node cost grows with depth beyond
the 4x factor — §9), which the caps absorbed because they were caps.

## 7. What I did not do

- **D4 (Asp pair + swing 12 together) did not run** — the job's first-cut match; after D3 the
  remaining time was below my chain's 420 s start floor, and a ~340 s match would have reached
  only ~180 games (worse than useless for a 95 % interval). The combined-halves question at depth
  stays open.
- No second seed for any D match (the job prescribed one seed each; the depth intervals are
  single-seed and wide).
- No equal-time check, no other swing strengths (the job fixed the grid: 12 and 24).

## 8. What I am not sure about

- The rate model: the job's "about four times" factor predicted 0.688 games/s at 80,000 nodes;
  the measured rate was 0.51-0.55/s — per-node cost grows with search depth (deeper trees touch
  more TT and history memory). My caps absorbed this; a tighter schedule would not have. Next
  time: use a 5x factor or measure one D game before sizing.
- The "no shrink demonstrated" reading rests on 800-game intervals against three-seed 20k pools
  from OTHER helpers (different machines possibly — deepseek3's "plain tree" box vs mine). A
  same-machine 20k baseline for exactly these options does not exist in my own data; the cross-
  machine comparison is the best I have and I flag it.
- D3's two dropped one-game rounds: the deadline interrupt leaves the in-flight games uncounted;
  I dropped the incomplete PAIRS as the job prescribes. If fastchess had written half-finished
  games with results into the PGN (it does not appear to), my filter would have kept wrong pairs;
  the parser counts a game only when its PGN block carries a result, and the two dropped rounds
  are the games that never finished.
- The swing@12 vs swing@24 ordering at depth (+18.3 vs +6.8) comes from two single seeds; the
  intervals overlap ([+3.3, +33.3] vs [−9.2, +22.8]). The ordering matches the 20k picture but a
  single seed each cannot rank them firmly.

## 9. A better way

1. **Measure one 80,000-node game before sizing the depth matches.** The job's 4x factor was a
   good first guess but 25 % optimistic (measured 0.51-0.55/s vs predicted 0.688). A single timed
   D-game (~2-3 s of waiting after C) would have sized every cap exactly. Cost: seconds; saves
   the surprise.
2. **The complete-pairs rule needs to be in the parser from the start, not added when a match is
   cut.** My job 2-4 parser counted every parsed game; job 5's D3 was the first cut match whose
   last rounds were incomplete, and the filter had to be retrofitted (the D1-D3 numbers above use
   it; D1/D2/C were complete so nothing changes for them). A parser that ALWAYS drops incomplete
   pairs and reports how many it dropped would have been right for every job so far.
3. **Report the depth-cost fact next to the rate rule**: the "games per second at N nodes" is
   not proportional to 1/N across node levels on this tree (0.511-0.552/s at 80k vs 1.32-1.72/s
   at 20k — a 2.4-2.6x rate drop for a 4x node rise). Whoever sizes future deep matches should
   use the measured per-node cost curve, not a linear factor.

## 10. Model

GLM 5.3 Flash (glm-5.3-flash).
