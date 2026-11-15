# glmflash3 job 7 report (2026-11-15)

## 1. First line

**The Asp rule alone at 80,000 nodes, POOLED over its two seeds — 7351 (job 5 D1: +8.3
[−6.6, +23.2]) and 7363 (this job's F1: +10.4 [−4.7, +25.6]) — is +9.3 Elo with a 95 % pair
interval of [−1.3, +20.0] (1600 games, 800 pairs): positive in both seeds, the pooled interval
just touching zero at the bottom. What the Asp rule ADDS on top of swing 12 (F2, the pair against
swing 12 alone): −9.2 [−26.7, +8.4] — nothing measurable, point estimate leaning negative. With
job 6's E1 (the pair: +17.0 [−3.4, +37.5]) sitting at swing 12's own pooled level (+16.1
[+4.0, +28.3]), the picture is: both halves gain alone, the pair is not more than its better
half — the two terms overlap, the sum is not additive.**

First paragraph — what was cut: nothing was skipped: C (100 games) ran, F1 ran to its FULL 800
(as the job ordered, before F2 started), F2 was cut by its deadline at 609 of 800 games and is
reported on complete pairs (304 pairs, 1 one-game round dropped — above the job's 200-game
"too short" floor). 0 crashes/illegal/disconnects in all three.

## 2. Build checks before the matches

Same `build-pk` as jobs 5-6 (unchanged binary; commit d4f43124 + packc28 port, flags
`-march=x86-64-v3 -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1`). Fresh bench 13 checks as
the job prescribed: no option → **862329** ✓ (known); Asp pair alone (1+3) → **649268** ✓ (job 5's
number). Raw outputs `job7_check_off.out`, `job7_check_asp.out`.

## 3. The probes (each BEFORE its match; two stamps each)

| match | probe start | probe end (stamp) | cand side received | base side received |
|---|---|---|---|---|
| C | 22:05:36 | 22:05:5x (`probe_c7.txt`; match started after, 22:05:5x) | Threads 1, Hash 16, OwnBook false (both games) | the same three |
| F1 | 22:29:33 | 22:29:40 (`probe_f1.txt`; match started 22:29:40) | the three + `AspFailHighReduce 1`, `AspFailHighMaxReduce 3` | the three only |
| F2 | 22:29:33 | 22:29:40 (`probe_f2.txt`; match started 22:29:40) | the three + Asp pair + `EvalSwingMult 12`, `EvalSwingMax 200` | the three + `EvalSwingMult 12`, `EvalSwingMax 200` |

This is the first job where the control's probe ran BEFORE its match — the template repair
Fable asked for (job 6 §9.2) is in `chain7.sh` and worked.

## 4. All matches of jobs 5-7 at 80,000 nodes (every row once)

| job | match | cand | base | seed | games (complete pairs) | W-L-D | fastchess Elo ± | my Elo [95 % pair] | crashes/illegal |
|---|---|---|---|---|---|---|---|---|---|
| 5 | D1 | Asp 1+3 | none | 7351 | 800 / 800 (400) | 218-199-383 | +8.25 ± 14.86 | +8.3 [−6.6, +23.2] | 0 |
| 5 | D2 | Swing 12+200 | none | 7352 | 800 / 800 (400) | 212-170-418 | +18.26 ± 14.98 | +18.3 [+3.3, +33.3] | 0 |
| 5 | D3 | Swing 24+200 | none | 7353 | 668 / 800 (334; 2 one-game rounds dropped) | 170-157-341 | +4.04 ± 16.59 (602-game snapshot) | +6.8 [−9.2, +22.8] | 0 |
| 6 | C | nodes 20000/10000 | — | 7360 | 300 / 300 (150) | 181-21-98 (fast) | +206.65 ± 33.05 | +206.7 [+175.2, +241.5] | 0 |
| 6 | E1 | Asp 1+3 + Swing 12+200 | none | 7361 | 450 / 800 (225) | 128-106-216 | +12.17 ± 21.52 (400-game snapshot) | +17.0 [−3.4, +37.5] | 0 |
| 6 | E2 | Swing 12+200 | none | 7362 | 450 / 800 (225) | 127-111-212 | +20.87 ± 21.31 (400-game snapshot) | +12.4 [−8.3, +33.1] | 0 |
| 6 | E3 | Asp 1+3 | none | 7363 | not started (no time) | — | — | — | — |
| 6 | E4 | pair vs swing 12 | — | 7364 | not started (no time) | — | — | — | — |
| 7 | C | nodes 20000/10000 | — | 7370 | 100 / 100 (50) | 54-9-37 (fast) | +168.40 ± 56.46 | +168.4 [+115.6, +229.7] | 0 |
| 7 | F1 | Asp 1+3 | none | 7363 | 800 / 800 (400) | 217-193-390 | +10.43 ± 15.12 | +10.4 [−4.7, +25.6] | 0 |
| 7 | F2 | Asp 1+3 + Swing 12+200 | Swing 12+200 | 7364 | 609 / 800 (304; 1 one-game round dropped) | 143-159-306 | −8.11 ± 17.66 (600-game snapshot) | −9.2 [−26.7, +8.4] | 0 |

(The job-6 C row carries the 20000/10000 control; the two "not started" E3/E4 rows keep their
places so the seed accounting stays readable — E3's seed 7363 is exactly the seed F1 played.)

**The pooled Asp figure**: D1 + F1 = 1600 games, 800 pairs, W-L-D 435-392-773, score 0.5134 →
**+9.34, 95 % pair interval [−1.26, +19.95]**.

## 5. Files of the repository I opened

None beyond the job file — this job changes no code and runs option combinations of the already-
ported packc28 options on the already-read tree; the build checks re-ran two known numbers.
Scripts: `chain7.sh` (with the probe-in-template repair) in the job folder.

## 6. Stamps of every step

All UTC from `/tmp/g3job5/stamps.txt` (committed copy in the job folder). Job start (reading
file 7) ~22:05:20; budget end (60 min) 23:05:20; the 50-min stop-and-write mark 22:55:20.

| step | start | end | note |
|---|---|---|---|
| job-6 table repair committed + pushed | 22:04:5x | 22:05:1x | before job 7's work began |
| bench checks (862329, 649268) | 22:05:2x | 22:05:3x | both ✓ |
| chain launch | 22:05:36 | — | |
| probe c7 | 22:05:36 | 22:05:5x | BEFORE its match (first time) |
| control C (100 games) | 22:05:5x | 22:06:2x | rate NOT taken from it (job 6's 0.54/s used) |
| probe f1 + F1 | 22:29:33 | 22:29:33 | probe first |
| F1 | 22:06:2x | 22:29:33 | FULL 800/800 in 23:13 (~0.573 games/s measured) |
| probe f2 + F2 | 22:29:33 | 22:29:40 | probe first |
| F2 | 22:29:40 | 22:48:27 | deadline 1127 s = STOP − now − reserve; cut at 609/800 |
| pooled + report + commit + push | 22:48:30 | ~22:54 | inside the stop mark |

## 7. What I did not do

- No third seed for the Asp pair; no re-run of F2 (its 609 games give a ±17-Elo-wide interval;
  the additivity question deserves a second seed if Fable wants it settled).
- No speed measurement this job (the PC's 5.5 % swing cost is quoted from Fable's measurement;
  the Asp rule's zero-cost claim is the PC's, not mine — I did not measure nps on/off for the
  Asp pair here).

## 8. What I am not sure about

- The pooled Asp interval [−1.3, +20.0] touching zero: with two positive seeds the honest reading
  is "probably a small real gain (~+9), not yet proven at 95 %". A third seed (~800 games,
  ~25 min) would almost certainly push the lower bound above zero given the two seeds' consistency.
- F2's negative point (−9.2): with [−26.7, +8.4] I read "no addition" rather than "the Asp rule
  hurts swing 12" — one seed, wide interval. But if the Asp rule's information genuinely
  overlaps swing's, a slightly negative interaction is plausible; only more seeds can tell.
- The C at 100 games (+168 ± 56) is a harness check, exactly as the job says; its interval
  contains 200 and proves nothing more.
- The measured F1 rate (0.573/s) is a little ABOVE job 6's 0.54 — the rate estimate for future
  jobs: 0.54-0.57/s at 80,000 nodes on this tree, not a fixed constant.

## 9. A better way

1. **"Stopped by the clock on a complete pair" is implementable better than by deadline alone.**
   My F2 stop is the plain SIGINT deadline; a small watcher that checks the finished-pair count
   every few seconds and sends the interrupt the moment a pair completes nearest the deadline
   would never drop a half-played game. Cost: a 10-line watcher; benefit: every deadline-cut
   match ends on a pair boundary (this job dropped only 1 game; job 5's D3 dropped 2 — small,
   but the fix is general and free).
2. **The pool-first scheduling trade-off (job 6 §9.3) resolved itself here and is worth writing
   down as a rule**: when a window fits exactly ONE full match, play the match whose pool it
   completes (this job: F1's seed 7363 was E3's postponed seed — the job text itself made the
   pool the priority). General rule: "a match that completes an existing pool outranks a match
   that starts a new question, when only one fits."
3. **Nothing else — the job's sizing (full F1 before F2) was the right call and matched the
   window exactly; the only waste in jobs 5-7 came from MY deadline arithmetic, never from the
   job text's.**

## 10. Model

GLM 5.3 Flash (glm-5.3-flash).
