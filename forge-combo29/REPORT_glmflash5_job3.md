# REPORT glmflash5 — JOB 3 — TmFinishIteration, second look on new openings (Version A, tc=2+0.02)

VERSION A — why: my job 2 said this machine IS fit for clock games: K0 −1.7 [−27.2, +23.7]
(inside the error), K1 +168.4 ± 30.6 (the tool sees the odds), losses on time 0 in 986 clocked
games (≤ 1/100). Branch `cursor/glmflash5-work-cb5c`, same build as job 2 (6b98f217, g++ 13.3,
release, defaults).

## 1. What was asked, the answer, how sure

Asked: the second look for the clock switches on a NEW opening file with no opening of job 2 in
it, pooled with job 2, with the difference between the two looks reported.

Answer: **TmFinishIteration: job 3 alone −1.7 Elo [−18.1, +14.8] (316 pairs, tc=2+0.02, built-in
net); pooled with job 2 −6.0 Elo [−17.3, +5.3] over 609 pairs — inside the error.** The two looks
agree (difference −9.0 [−31.6, +13.5], z=−0.78; openings shared between the looks: 0). **The
switch is not shown to gain at 2+0.02; a small negative lean is not established either.**
**TmNodeShare: still no valid match — not played here either** (job 2's rate forced "only M1",
and this job's rule then says play only M1b; nothing about TmNodeShare is measured on a real
clock yet).

How sure: sure of mechanics (fresh 5,000-opening file disjoint from job 2 — checked 0 shared;
probes show the option arrived on the candidate only; K0b noise floor inside the error; 0 losses
on time). The pooled −6.0 comes from two independent looks; the interval just touches 0 — call it
inside the error and nothing more.

## 2. Known numbers of step 0

Session-level, in `tests_glmflash5_job1/`: bench 11/13/16 = 312866/862329/3024920, perft 5 =
4865609 (all exact; unchanged since; deepseek5's independent build reproduces them).

## 3. Games by ending FIRST, losses on time BY SIDE

Counts from the committed game lists (exact, each row sums to its games):

| match | games | White mates | Black mates | 3-fold rep. | fifty moves | insufficient mat. | stalemate | loss on time cand/base | illegal | disconnect | crash |
|-------|-------|-------------|-------------|-------------|-------------|-------------------|-----------|------------------------|---------|------------|-------|
| K0b   | 200   | 53          | 46          | 69          | 14          | 18                | 0         | 0 / 0                  | 0       | 0          | 0     |
| M1b   | 633 finished (632 used) | 183 | 138 | 220 | 43 | 48 | 1 | 0 / 0 | 0 | 0 | 0 |

No abnormal ending anywhere in job 3; the engine again lost no game on time at tc=2+0.02.

## 4. Table of all matches

Same form as job 2: same exe both sides, Threads=1 Hash=16 OwnBook=false, `timemargin=0`, no
adjudication, `-concurrency 2` (nproc=4), `-recover`; openings `openings_job3.epd` (5,000 lines
shuffled with `random.Random(9400)` from the 2,631,543 book lines that job 2 did not touch),
`order=sequential`. Seeds: the job names none — I chose 9310 (K0b) and 9311 (M1b), recorded here;
with sequential openings the seed choice is inconsequential, and I say so.

| name | options (cand) | tc | seed | games (used) | pairs | W-L-D (cand) | Elo, 95 % pair interval | complete? |
|------|----------------|----|------|--------------|-------|--------------|-------------------------|-----------|
| K0b  | none | 2+0.02 | 9310 | 200 | 100 | 54-45-101 | +15.7 [−9.6, +40.9] | complete |
| M1b  | TmFinishIteration=true | 2+0.02 | 9311 | 633 (632) | 316 | 159-162-311 | −1.7 [−18.1, +14.8] | INCOMPLETE, cut at 05:33:02 by interrupt; pair 317 (games 633+634) incomplete, game 633 dropped with it; 316 complete pairs used |

Openings book counts (required): lines in the book 2,632,036; openings used in job 2 (distinct
first-4-field FENs of K0, K1, M1; M2/M3 empty) 493; lines left after removing them 2,631,543;
written 5,000 lines. Openings shared between job 3's matches and job 2, checked after the
matches: **0 game rows** (script `job3_stats.py`).

fastchess's last 40 lines of M1b: `tests_glmflash5_job3/M1b_last40.txt` (no Elo table after an
interrupt — computed from per-game lines instead, as in job 2).

### Pools and difference (script `job3_stats.py`, pentanomial pair method validated in job 1)

| pool | pairs | n5 | Elo, 95 % pair interval | LOS |
|------|-------|----|-------------------------|-----|
| TmFinishIteration: M1+M1b | 609 | [8, 174, 275, 135, 17] | −6.0 [−17.3, +5.3] | 15.0 % |
| M1 alone (job 2) | 293 | [1, 89, 136, 61, 6] | −10.7 [−26.2, +4.8] | 8.8 % |
| M1b alone (job 3) | 316 | [7, 85, 139, 74, 11] | −1.7 [−18.1, +14.8] | 42.2 % |

Difference M1 − M1b: −9.0 Elo, 95 % [−31.6, +13.5] (z=−0.78) — the two looks do not disagree.

## 5. Probes (2 games, trace-logged, before K0b and M1b)

Raw: `tests_glmflash5_job3/probe_{K0b,M1b}.log`; condensed `probe_{K0b,M1b}_excerpt.txt`.
- probe M1b: cand received, once per game: `cand <--- setoption name TmFinishIteration value true`;
  base received only Threads/Hash/OwnBook. Option sent as `true`.
- probe K0b: neither side received any switch option (both got Threads/Hash/OwnBook only), and
  the new book loaded in sequential order (438 `position fen` lines in the 2-game log).

## 6. Per-move time, each side (for kimi5's model)

This fastchess build (v1.8.3-alpha) writes NO move times into the PGN (no clk/emt token exists in
its `-pgnout` options — checked in its help), and full-match trace logs would be ~100 MB per
match, so the numbers below come from the two trace-logged 2-game probes (each ~130–163 moves
per side; script `move_times.py`; elapsed = bestmove stamp − go stamp from the log timestamps).
They are SAMPLES, not match statistics:

| config | side | moves | mean ms | median ms | max ms |
|--------|------|-------|---------|-----------|--------|
| OFF (probe K0b) | A | 163 | 24.4 | 15.3 | 249.7 |
| OFF (probe K0b) | B | 159 | 19.2 | 13.1 | 250.9 |
| ON TmFinishIteration (probe M1b) | cand | 131 | 24.0 | 19.3 | 131.9 |
| ON TmFinishIteration (probe M1b) | base | 131 | 24.7 | 19.7 | 197.9 |

Pattern: with the switch ON the worst move is ~half as long (max 132 vs 250 ms) and the median
rises slightly (19.3 vs 15.3) — spending more evenly, smaller tail, no large mean shift. This is
the signature "finish the iteration instead of aborting it" should produce; the sample is 2 games,
so treat the max comparison as indicative only.

## 7. From my partners (deepseek5 AND kimi5; step A before this job)

- deepseek5 (NOTES + REPORTs job 1–3): its job 2/3 found the movetime reserve = `Move Overhead`
  exactly (overhead 0 → median M+0.5; a real ~0.5 ms overshoot of the literal limit), and 0 of
  3,600 direct + 0 of 996 fast-clock searches overstepped — "no wtime safety patch needed on this
  build". Applied here: nothing in my matches sends movetime, and its stop-latency numbers
  (0.7 ms T1 / 4.6 ms T4) matter to me only if a match sends `stop` — fixed-games fastchess does
  not. Its lesson (sort before statistics; paste stamps from files) applied to my job 3 script.
- kimi5 (NOTES_kimi5.md): **"both options are clock-play only and skip movetime/depth/nodes
  (search.cpp:2395-2399, 2586-2590); measure them with wtime lines, not movetime, or they do
  nothing"** — this confirms the tc=2+0.02 form is the right way to measure these switches and
  that my job 2 was valid. Checked (its numbers vs mine): its measured hard-stop
  movetime−overhead behaviour matches deepseek5's independent rerun; my per-move times above are
  the wtime-line data point it asked for.
- Cross-check done this job: K0b's ending counts and M1b's pair counts were recomputed twice
  (awk over the gamelist and python over the same file) and agree; the openings-shared check
  printed 0.

## 8. What I did NOT do

- **M2b (TmNodeShare) — not played**, per the job's own rule (job 2 played only M1 → "play only
  M1b with all the time"). TmNodeShare therefore still has NO real-clock match anywhere.
- No third look for TmFinishIteration (this job IS the second look; the pool now has 609 pairs).
- Full-match per-move time statistics — only 2-game probe samples (section 6 explains why).

## 9. What I am NOT sure about

- Whether TmFinishIteration's pooled −6.0 is a real small loss: the interval [−17.3, +5.3]
  includes 0; two looks now agree in DIRECTION (both negative) but neither is decisive.
- The K0b noise floor +15.7 [−9.6, +40.9] sits on one seed; like any single look it proves only
  that nothing large is present, and it also shows how wide clock-game windows are: ~200 games
  cannot resolve ±20 Elo here.
- The per-move-time pattern (section 6) comes from 4 game-samples (2 OFF, 2 ON); the "smaller
  tail" reading could be opening-position luck.
- M1b was cut by interrupt; its last unfinished pair is excluded, but a cut match is still one
  look taken at a fixed wall-time point, not a designed stopping point.

## 10. A better way

- The per-move-time question deserves a proper answer at near-zero extra cost: run the NEXT
  TmFinishIteration match with trace logging to a file OUTSIDE the repo and post-process it (the
  log is text; the repo only needs the summary). A ~600-game trace log is ~250 MB — heavy but
  local; it would give exact per-move mean/median/max for both sides over the whole match instead
  of 2-game samples.
- kimi5's model (search.cpp lines) + deepseek5's harness + my per-move extraction could be merged
  into one "clock honesty" check that any future clock switch job runs first: probe log →
  per-move table → THEN the Elo match.

## 11. UTC stamps (all from `date -u` at the moment, or recorded match stamps)

- 04:46:53 file 3 FOUND (waiting command, attempt 1); 04:47 file 3 read; partner notes read
  04:47:0x–04:47:2x.
- 04:47:31 probe K0b finished (2 games, logged).
- 04:47:35–04:58:34 K0b (200 games, 10:59, recorded by echo): −12.2 [−53.1, +28.7].
- 04:58:47 probe M1b finished (2 games, logged).
- 04:58:48–05:33:02 M1b (launched, cut by SIGINT at the planned 05:33:00 stamp; fastchess's own
  total 00:34:12; 633 games finished, 316 complete pairs used).
- 05:33:05–05:33:21 gamelists, stats, difference, shared-openings check, evidence copied; a
  candidate-name bug in K0b's stats was caught by validation against fastchess's own output and
  fixed (K0b n5 now reproduces fastchess's Ptnml exactly); report rewritten clean.
- 05:33–05:47 this report and notes written; commit + push stamped by git (`glmflash5 job 3 report`).

## 12. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5; kimi5 is
the source reader whose notes I now read too.
