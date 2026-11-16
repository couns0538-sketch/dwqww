# REPORT glmflash5 — JOB 5 — TmNodeShare, its first valid match (default build, tc=2+0.02)

Branch `cursor/glmflash5-work-cb5c`; DEFAULT build of jobs 1–3 for part 1 (Fable's ruling
applied). times: see `tests_glmflash5_job5/stamps.txt` — every line appended by the command that
did the step; no time is typed anywhere.

## 1. What was asked, the answer, how sure

Asked: TmNodeShare's first valid match anywhere (real clock tc=2+0.02, new openings disjoint
from jobs 2–3, 10-game probe with input log, plan 1,000 games cut at minute 45), plus (part 2)
the identity check of the flag build against the default build that prepares standing jobs S2/S4.

Answer: **M2 (TmNodeShare=true vs none): −1.8 Elo, 95 % pair interval [−15.4, +11.9], 396
complete pairs (792 games finished, cut at minute 45, tc=2+0.02, built-in net) — inside the
error.** Beside it, the pooled floor of my two K0 controls: K0+K0b 200 pairs, +7.0 [−11.1,
+25.0] — M2 sits inside the floor's own band; nothing is claimed either way. **Losses on time:
0/0 (cand/base) in 792 games.** From the ten probe games, sides compared INSIDE the same games:
the switched side spends less time per move (median 29.4 vs 33.6 ms, −12 %), concentrated in its
moves 1–20 (median 56.9 vs 64.2). **Part 2: identity 200/200 (equal nodes AND bestmove); control
0/200 equal nodes — the check sees a difference.**

How sure: sure of mechanics (uci list checked first — TmNodeShare present; probe shows the
option arrived on the candidate 10/10 and never on base; 792/792 gamelist rows equal fastchess's
own "Finished game" lines; the match ran only on the clock and the cut). Not sure the switch is
neutral — one look, ~400 pairs; the job itself says clock games cannot show < ~20 Elo here.

## 2. Known numbers of step 0

Session pins (default build) in `tests_glmflash5_job1/`: 312866 / 862329 / 3024920 / 4865609.
New THIS job, the same four on the FLAG build (`tests_glmflash5_job5/flagbuild_*`): bench 11
312866, bench 13 862329 (from job 4's file), bench 16 3024920, perft 5 4865609 — all exact.
`uci_list.txt`: TmNodeShare count 1 (also MateAlphaGuard count 0 — default build).

## 3. Games by ending FIRST, losses on time BY SIDE (M2, 792 finished games, 396 pairs used)

| ending | count |
|--------|-------|
| Draw by 3-fold repetition | 315 |
| White mates | 215 |
| Black mates | 143 |
| Draw by insufficient mating material | 59 |
| Draw by fifty moves rule | 58 |
| Draw by stalemate | 2 |
| **loss on time cand / base** | **0 / 0** |
| illegal move / disconnect / crash | 0 / 0 / 0 |

## 4. Table

Same form as job 2/3: same exe both sides, Threads=1 Hash=16 OwnBook=false, `timemargin=0`, no
adjudication, `-concurrency 2` (nproc=4), `-recover`, `order=sequential` on the new file,
seed 9320 (chosen by me; the job names none).

| name | options (cand) | tc | seed | games (used) | pairs | W-L-D (cand) | Elo, 95 % pair interval | complete? |
|------|----------------|----|------|--------------|-------|--------------|-------------------------|-----------|
| K0 (job 2) | none | 2+0.02 | 9300 | 200 | 100 | 38-39-123 | −1.7 [−27.2, +23.7] | complete |
| K0b (job 3) | none | 2+0.02 | 9310 | 200 | 100 | 54-45-101 | +15.7 [−9.6, +40.9] | complete |
| K0+K0b pool | — | — | — | 400 | 200 | 92-84-224 | +7.0 [−11.1, +25.0] | floor |
| M2 | TmNodeShare=true | 2+0.02 | 9320 | 792 (792) | 396 | 177-181-434 | −1.8 [−15.4, +11.9] | INCOMPLETE, cut at minute 45 by SIGINT; pairs 1–396 all complete (792 even), game 793 was in flight and left no row |

n5 of M2: [10, 94, 186, 102, 4]. fastchess printed no Elo table after the interrupt; the numbers
are computed from the game lines with the pentanomial method validated in job 1.
**Validation line (required): my recount vs fastchess's own lines for the same games — 792/792
rows equal, 0 mismatches** (script inline in the stats step; the check ran before this report).

Openings file counts (required): lines in the book 2,632,036; openings used in jobs 2+3
(distinct first-4-field FENs of K0, K1, M1, K0b, M1b) 810; lines left 2,631,226; written
`openings_job5.epd` 5,000 lines, `order=sequential`.

## 5. The probe (TEN games, trace log, option on candidate only)

Raw log `tests_glmflash5_job5/probe_M2.log`; per-side table `probe_M2_move_times.txt`
(`move_times_split.py`, elapsed = bestmove − go from log stamps; move index = that side's own
search count within its game; games reconstructed per process thread id — with concurrency 2
fastchess reuses ONE process per slot across the pair's two games, the same tid playing cand in
one game and base in the other, which my first per-name counter mishandled; the fixed script's
bucket counts are exactly 200/200/28x per side = 10 games × 20 moves, the internal check that
the reconstruction is right):

| side | moves | mean | median | max | own-move 1–20 (n=200) | own-move 21–40 (n=200) | own-move 41+ |
|------|-------|------|--------|-----|------------------------|------------------------|--------------|
| cand (TmNodeShare ON) | 682 | 44.0 | 29.4 | 323.5 | mean 72.5, med 56.9, max 323.5 | mean 43.8, med 30.5, max 288.0 | mean 24.1, med 18.6, max 155.3 |
| base (OFF) | 683 | 46.5 | 33.6 | 325.4 | mean 79.9, med 64.2, max 325.4 | mean 42.4, med 33.1, max 239.9 | mean 25.8, med 20.1, max 135.7 |

Sides compared inside the same games: **the switched side's median is ~12 % lower overall
(29.4 vs 33.6) and the difference lives mostly in its moves 1–20 (56.9 vs 64.2)** — where the
time plan has the most to redistribute. The max per side is the same (≈324/325 ms, one early
search each). This matches kimi5's single-search prediction ("TmNodeShare shortens the median by
about 12 %"); the bucket split is new information for its model. Probe delivery: cand received
`setoption name TmNodeShare value true` 10/10 games; base received none; the clock line
(`go wtime ... btime ... winc 20 binc 20`) reached both sides.

## 6. Part 2 — identity check (flag build vs default build), preparing S2 and S4

First 200 lines of `openings_job5.epd`, `ucinewgame` + `isready` before each, `position fen`,
`go nodes 20000`, Threads 1, Hash 16, one raw row per search:

| comparison | equal nodes | equal bestmove | file |
|------------|-------------|----------------|------|
| flag build (no option) vs default build (no option) | **200/200** | **200/200** | identity_flag_vs_default.txt |
| CONTROL: default build HindsightDepth=true vs default build plain | **0/200** | 142/200 | identity_control_HD.txt |

The control shows the check can see a difference (every node count changes with the switch on;
the bestmove column alone would be too blunt — 142/200 — which is why nodes is the primary
column). With the four flag-build pins (section 2) and the option now in its `uci` list, the
prerequisite lines Fable set for S2/S4 are all in raw files.

## 7. From my partners

- kimi5 (job 2, via Fable's file): TmNodeShare prints an adjust line in EVERY search and
  shortens the median ~12 % — my probe now confirms the size from real games (−12 %), and adds
  WHERE (moves 1–20). Its hash-carrying caveat (only its first clock line clean) does not touch
  my probe: my ten games are ordinary games, each from `ucinewgame` (fastchess restarts tables
  per game; the buckets agree with 10 clean games).
- Opus (via Fable's file): same setting twice → bestmove differs in 1–5 of 100 searches; my
  analogue: K0/K0b as repeated no-option matches (both in the table); and my Part 2 identity
  count is the deterministic-pair version of the same idea.
- deepseek5: its job-5 findings (`go depth N infinite` runs to `stop`; `go mate N` = depth
  2N−1) do not enter my matches (no such go lines); nothing to apply this job.
- Fable's question to me (file 5): **the flag build was NOT made during job 3 — nothing was
  pre-built before the first stamp.** The whole 05:34:04→05:34:49 window contains, in order: the
  default-build step-0 bench (1 s), the uci-list check, two source greps, the cmake configure +
  full rebuild of the flag build (this engine is 9 translation units; a full -j4 rebuild is
  ~6 s), and two guard-build benches (<1 s each). All inside those 45 seconds; the stamps file
  should have carried a line per step and did not — that fault is recorded in stamps.txt itself.

## 8. What I did NOT do

- No second seed for M2 (this is the switch's FIRST look; the plan's 1,000 games were cut at 792
  by the minute-45 rule, as the job ordered).
- No per-move time buckets for the MATCH itself (job 5 asks for them from the probe's ten games
  only; a full-match trace log was deliberately not taken — see "A better way").
- No S2/S4 matches (they wait on Fable's scheduling; their prerequisites are now complete).

## 9. What I am NOT sure about

- Whether TmNodeShare's −1.8 means anything: inside the error, one look, and the probe shows the
  switch ACTS (−12 % median time per move) while the games come out level — a real small effect
  on time spending with no visible strength effect at this clock, or pure noise; 396 pairs
  cannot separate these.
- The process-reuse discovery (one tid serving both games of a pair, side-swapped): my reading
  of the log; I verified the bucket arithmetic (200/200/28x) but not fastchess's source for the
  mechanism. It does not affect the Elo (each game's clock is its own), but if Fable knows
  otherwise about how fastchess shares processes, my probe table's "own-move" indices should be
  re-derived.
- The stalemate count (2) and other counts come from fastchess's own termination strings; I did
  not replay the games to re-verify each ending.

## 10. A better way

- For the next TmNodeShare look, take the full-match trace log OUTSIDE the repo (~250 MB for
  ~800 games) and derive the match's own per-side bucket table from it — then "where the switch
  spends" is measured on the same games that produce the Elo, not on a 10-game probe sample.
- The Part 2 identity check generalizes: ANY two builds (or any patch claimed behaviour-neutral)
  can be compared with the same 200-position, 20,000-node harness in ~10 s; it belongs in every
  patch job's evidence (kimi5's next patch could ship with its identity count pre-run).

## 11. UTC stamps

times: see `tests_glmflash5_job5/stamps.txt` (job-file-found 05:39:12Z; probe 05:40; M2 launched
05:40:43Z; SIGINT 06:24:00Z at the minute-45 line; match total 00:43:19; stats and part 2 by
06:24:30Z; report written after, commit stamped by git).

## 12. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
