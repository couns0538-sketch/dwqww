# glmflash3 job 6 report (2026-11-15)

## 1. First line

**The pair (Asp rule + eval swing 12) at 80,000 nodes, first measurement: +17.0 Elo (95 % pair
interval [−3.4, +37.5], 450 games, seed 7361) — positive point estimate, interval touching zero.
Eval swing at strength 12 ALONE, pooled over its two seeds (D2 seed 7352 +18.3 [+3.3, +33.3];
E2 seed 7362 +12.4 [−8.3, +33.1]): +16.1 Elo, 95 % pair interval [+4.0, +28.3] — established at
depth. The Asp pair alone has only job 5's seed (+8.3 [−6.6, +23.2], D1): its second seed (E3)
was not reached, so no Asp pool exists.**

Cut or not reached, first paragraph as asked: C completed (300/300); **E1 and E2 were each cut at
450 of 800 games** — the job's equal-share rule applied to the measured window (after C and the
report reserve, 1666 s remained; 833 s caps each; the corrected rate estimate 0.561/s predicted
~470 games per cap and the measured was ~0.54/s → 450). **E3 and E4 were not started** (after E2,
~350 s remained — below the 420 s floor; the cut order E4-then-E3 never engaged). All statistics
use complete pairs only (E1/E2 had none incomplete; C complete). 0 crashes/illegal/disconnects
everywhere.

## 2. The new bench number and the build

Build, tree and flags: exactly job 5's (`build-pk` reused unchanged — same commit d4f43124 plus
`packc28_port.patch`, same `cmake -DCMAKE_CXX_FLAGS="-march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1"`,
verified by a fresh `bench 13` before the matches: 862329, the known number). The four option
lines of the uci answer were re-checked present (`AspFailHighReduce`, `AspFailHighMaxReduce`,
`EvalSwingMult`, `EvalSwingMax`).

**New `bench 13` number — the four E1 options together** (`AspFailHighReduce 1`,
`AspFailHighMaxReduce 3`, `EvalSwingMult 12`, `EvalSwingMax 200`): **776151**
(`saved5/pair12_bench13.out`; differs from the no-option 862329, from the Asp-alone 649268 and
from the swing12-alone 748790 — each half acts and the pair is its own tree). Sanity run: no
option bench 13 = 862329 ✓.

## 3. The probes

- **probe_e1**: cand `Threads 1`, `Hash 16`, `OwnBook false`, then `AspFailHighReduce 1`,
  `AspFailHighMaxReduce 3`, `EvalSwingMult 12`, `EvalSwingMax 200` (probe_e1.txt, both games,
  both sides).
- **probe_e2**: cand adds `EvalSwingMult 12`, `EvalSwingMax 200` only (probe_e2.txt).
- **C's probe ran after its match again** (`probe_c6post.txt`) — the same chain-script slip as
  job 4 (my §4 of that report flagged it; the chain template still lacks the C probe — see §9.3
  of job 4 and §9 here). Both sides received exactly the three base options in both games.

## 4. All matches of jobs 5 and 6 at 80,000 nodes

| job | match | cand | base | seed | games (complete pairs) | W-L-D | fastchess Elo ± | my Elo [95 % pair] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|---|
| 5 | D1 | Asp 1+3 | none | 7351 | 800 / 800 (400) | 218-199-383 | +8.25 ± 14.86 | +8.3 [−6.6, +23.2] | 0 |
| 5 | D2 | Swing 12+200 | none | 7352 | 800 / 800 (400) | 212-170-418 | +18.26 ± 14.98 | +18.3 [+3.3, +33.3] | 0 |
| 5 | D3 | Swing 24+200 | none | 7353 | 668 / 800 (334, 2 one-game rounds dropped) | 170-157-341 | +4.04 ± 16.59 (602-game snapshot) | +6.8 [−9.2, +22.8] | 0 |
| 5 | D4 | — | — | 7354 | not started | — | — | — | — |
| 6 | C | nodes 20000 | nodes 10000 | 7360 | 300 / 300 (150) | 181-21-98 (fast) | +206.65 ± 33.05 | +206.7 [+175.2, +241.5] | 0 |
| 6 | E1 | Asp 1+3 + Swing 12+200 | none | 7361 | 450 / 800 (225, none incomplete) | 128-106-216 | +12.17 ± 21.52 (400-game snapshot) | +17.0 [−3.4, +37.5] | 0 |
| 6 | E2 | Swing 12+200 | none | 7362 | 450 / 800 (225, none incomplete) | 127-111-212 | +20.87 ± 21.31 (400-game snapshot) | +12.4 [−8.3, +33.1] | 0 |
| 6 | C | nodes 20000 | nodes 10000 | 7360 | 300 / 300 (150) | 181-21-98 (fast) | +206.65 ± 33.05 | +206.7 [+175.2, +241.5] | 0 |
| 6 | E1 | Asp 1+3 + Swing 12+200 | none | 7361 | 450 / 800 (225, none incomplete) | 128-106-216 | +12.17 ± 21.52 (400-game snapshot) | +17.0 [−3.4, +37.5] | 0 |
| 6 | E2 | Swing 12+200 | none | 7362 | 450 / 800 (225, none incomplete) | 127-111-212 | +20.87 ± 21.31 (400-game snapshot) | +12.4 [−8.3, +33.1] | 0 |
| 6 | E3 | Asp 1+3 | none | 7363 | not started | — | — | — | — |
| 6 | E4 | Asp 1+3 + Swing 12+200 | Swing 12+200 | 7364 | not started | — | — | — | — |

**Pools over seeds (complete pairs):**
- Swing 12 alone, D2 (7352) + E2 (7362): 1250 games, 625 pairs, W-L-D 339-281-630 (cand), score
  0.5232 → **pooled +16.13, 95 % pair interval [+4.02, +28.28]** — above zero with both seeds
  positive.
- Asp pair alone: D1 (7351) only — E3 not reached; **no pool** (+8.3 [−6.6, +23.2] stands as the
  one-seed figure).
- The PAIR (E1): one seed, +17.0 [−3.4, +37.5] — its first and only number; against the halves
  measured separately (Asp +8.3, swing +16.1 pooled) the pair's point sits between them and above
  both — but with ~225 pairs nothing more can be said than that.

## 5. Files of the repository I opened

Same tree as job 5; for job 6 itself I opened no repository file beyond re-reading the match form
in the job file — the feature hooks were all read and cited in jobs 2-5 and this job changes no
code (the pair is an option combination of the existing four spin options). `chain6.sh` and
`probe6.sh` in the job folder are this job's scripts.

## 6. Stamps of every step

All UTC from `/tmp/g3job5/stamps.txt` (job 6 appended to the same file; committed copy in the job
folder). Job start (reading file 6) ~21:30:20; budget end (90 min) 23:00:20; the 80-min
stop-and-write mark 22:10:20 — every step finished before it.

| step | start | end | note |
|---|---|---|---|
| new bench number (E1's four options) + sanity | 21:30:30 | 21:30:40 | 776151; sanity 862329 ✓ |
| chain launch | 21:30:42 | — | |
| control C | 21:30:42 | 21:32:29 | 300/300, elapsed 107 s → **rate_C = 2.804/s**; corrected rate_D = 2.804/4×0.8 = **0.561/s** (the job's 4x factor with the 20 % correction it asked for) |
| E1 | 21:32:36 | 21:46:31 | deadline 835 s (the equal share); **cut at 450/800** |
| E2 | 21:46:37 | 22:00:26 | deadline 829 s; **cut at 450/800** |
| E3, E4 | — | — | **not started** (LEFT3 ≈ 350 s < the 420 s floor) |
| pooled + report + commit + push | 22:00:30 | ~22:08 | |

Deadline derivation as prescribed: from C's measured 2.804/s, the job's 4x factor, and the 20 %
correction → 0.561/s predicted; measured E-rate 450/835 ≈ 0.54/s — the correction landed within
4 % of the measured rate (job 5's uncorrected estimate was 25 % off; the fix worked).

## 7. What I did not do

- E3 (the Asp pair's second seed) and E4 (what the Asp rule ADDS to swing 12, the direct pair-vs-
  half comparison) did not start — the window after C and the report reserve split into two
  ~833 s E1/E2 shares per the job's equal-share rule, and nothing was left. The Asp-pair pool and
  the additivity check stay open.
- No probe before C (ran after — §3); no Bits/other-strength variants (not prescribed).

## 8. What I am not sure about

- Everything single-seed here is wide: E1's interval [−3.4, +37.5] cannot separate "the pair adds
  the two halves' gains" from "the pair adds nothing beyond swing 12". The E4 match (pair against
  swing 12 directly) is the experiment that answers it and it did not run.
- The corrected rate model (×0.8) predicted 0.561/s and the matches measured ~0.54/s — within 4 %.
  I do not know whether the correction is a stable property of this tree or a coincidence of two
  days' cache/thermal states; one more job's data would tell.
- The pooled swing-12 figure (+16.1 [+4.0, +28.3]) pools two seeds of the SAME config on the SAME
  machine and book; it inherits every standing caveat (one book, one node level, no equal-time).
- C's probe ran late; its form proof is therefore about the probe run itself, not about the match
  process that already played — the same caveat as job 4's cpost, now twice.

## 9. A better way

1. **The equal-share rule, applied to a window this small, wastes the window on width instead of
   spending it on the headline.** With ~1660 s for two matches needing ~1575 s each, the equal
   share (833 s) guarantees TWO half-informative matches and ZERO complete ones; an alternative
   rule ("first match gets up to its full prescription, second gets the remainder, both report
   complete pairs") would have delivered E1 COMPLETE (±15 instead of ±20.5) and E2 at ~90 games —
   or, better, E1 complete and then E2's leftover given to E3's remainder... which the job's cut
   order forbids. I followed the job's rule and report its cost plainly; if Fable prefers
   information-first allocation for one-seed questions, say so and the chains will do that.
2. **The C probe should be IN the chain template** — third time this slip has now happened or
   nearly happened (job 4, job 6; job 5's chain had it). One line in `chain6.sh`'s template
   before the control block. The generator idea (jobs 3-4 §10) subsumes this; until it exists,
   the template line is the fix.
3. **Pool-availability should be checked BEFORE the seed list is fixed**: the job asked for pools
   that require E3 (Asp second seed) while E3 sits behind E1/E2 in the time order — a rule that
   says "poolable matches get scheduling priority over non-poolable ones when the window is
   short" would have swapped E2 and E3 (swing's pool then needs only E2-or-nothing... no: swing's
   pool needed E2; Asp's needed E3 — with one slot only one pool could complete; choosing WHICH
   pool to prioritize is Fable's call, but making the trade-off visible in the job text would
   make the cut decision mechanical instead of silent).

## 10. Model

GLM 5.3 Flash (glm-5.3-flash).
