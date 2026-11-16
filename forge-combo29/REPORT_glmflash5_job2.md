# REPORT glmflash5 — JOB 2 — TmFinishIteration and TmNodeShare on the real clock (tc=2+0.02)

Branch: `cursor/glmflash5-work-cb5c` (same session branch as job 1; tool-forced name, stated in
job 1's report first line and in NOTES_glmflash5.md). Same build as job 1 (6b98f2170a3210e71beed04bbd2553972c253ed7,
g++ 13.3, release, defaults; CPU has AVX-512/BMI2 so no portable flags). Step 0 was re-verified
this session in job 1 (all four numbers exact) and the same four numbers were re-proven
independently by deepseek5 on its own build — nothing changed on my side between job 1 and job 2.

## 1. What was asked, the answer, how sure

Asked: measure TmFinishIteration and TmNodeShare on a REAL clock at tc=2+0.02, with a noise-floor
control K0 and a time-odds control K1 first, and losses on time counted by side.

Answer: **K0 −1.7 [−27.2, +23.7]** (my pair interval; fastchess ±25.8), **zero losses on time,
zero abnormal endings** — this machine is fit for clock games at 2+0.02; **K1 +168.4 ± 30.6** for
the side with double time — the tool sees a clock difference clearly. **M1 (TmFinishIteration=true
vs none): −10.7 Elo, 95 % pair interval [−26.2, +4.8] — inside the error** (leaning negative,
LOS ≈ 8.8 % over 293 complete pairs). **M2 (TmNodeShare) and M3 (both) were NOT played** —
see "What I did NOT do" for exactly why.

How sure: sure of the mechanics (probes show the option arrived on the candidate only; controls
behave as they must; losses on time 0 everywhere). Not sure the M1 negative is real: 293 pairs
cannot separate −10.7 from 0; per the job, nothing below ~20 Elo is claimable here.

## 2. Known numbers of step 0

Step 0 belongs to this session, not this job; the four exact numbers and their files are in
`tests_glmflash5_job1/` (step0_bench11/13/16.txt, step0_perft5.txt): 312866 / 862329 / 3024920 /
4865609. deepseek5's independent build (with `-DFORGE_NNUE_HIDDEN=256`, its job-1 report)
reproduced the same four numbers — the build is stable across the two machines.

## 3. Games by ending, and losses on time BY SIDE (FIRST, as required)

| match | games | White mates | Black mates | 3-fold | fifty moves | insufficient mat. | stalemate | loss on time cand/base | illegal | disconnect | crash |
|-------|-------|-------------|-------------|--------|-------------|-------------------|-----------|------------------------|---------|------------|-------|
| K0    | 200   | 39          | 38          | 89     | 17          | 16                | 1         | 0 / 0                  | 0       | 0          | 0     |
| K1    | 200   | 65          | 47          | 63     | 11          | 14                | 0         | 0 / 0                  | 0       | 0          | 0     |
| M1    | 586   | 141         | 99          | 249    | 49          | 47                | 1         | 0 / 0                  | 0       | 0          | 0     |

No abnormal ending anywhere. The engine did not lose a single game on time at tc=2+0.02 on this
machine, in either colour, under any of the three configurations.

## 4. Table of all matches

Both sides same exe, Threads=1 Hash=16 OwnBook=false, UHO_Lichess_4852_v1.epd order=random,
`-repeat -games 2` (each opening twice with colours reversed), `timemargin=0`, no adjudication,
`-concurrency 2` (nproc shows 4; half = 2), `-recover`, no other load on the machine while a
match ran.

| name | options (cand) | tc | seed | games | pairs | W-L-D (cand) | Elo, 95 % pair interval | complete? |
|------|----------------|----|------|-------|-------|--------------|-------------------------|-----------|
| K0   | none | 2+0.02 both | 9300 | 200 | 100 | 38-39-123 | −1.7 [−27.2, +23.7] | complete |
| K1   | none; side A tc=2+0.02, side B tc=1+0.01 | odds | 9301 | 200 | 100 | 101-11-88 (A) | +168.4 [±30.6 fastchess] | complete |
| M1   | TmFinishIteration=true | 2+0.02 both | 9302 | 586 | 293 | 111-129-346 | −10.7 [−26.2, +4.8] | INCOMPLETE (cut at minute 50; 293 of 293 reached pairs are complete — the 587th game was started but not finished; no partial pair in the data) |
| M2   | TmNodeShare=true | — | 9303 | 0 | — | — | not played (rate) | — |
| M3   | both true | — | 9304 | 0 | — | — | not played (rate) | — |

Rate math, recorded: K0 200 games in 10:41 (18.7 games/min); K1 200 games in 8:06 (24.7/min).
Minute 0 = 03:56 UTC (when I read the job file); minute 50 = 04:46. M1 started 04:15:11 after the
probe; the G that would have let both M1 AND M2 end before minute 50 was ≈ 220 (2×220/18.7 ≈
23.5 min) — below 300 — so per the job I played only M1 with all the time and cut it at the
deadline with fastchess's interrupt.

fastchess's last 40 lines for M1: `tests_glmflash5_job2/M1_last40.txt`. After the interrupt
fastchess printed no Elo table (same as deepseek5 observed); the numbers above are computed from
the per-game lines and the complete pairs, with `pool_stats.py` (committed in
tests_glmflash5_job1/, validated there against fastchess's own Elo/±/Ptnml output).

## 5. Probes (2 games before M1, trace log with engine I/O)

Raw: `tests_glmflash5_job2/probe_M1.log` (full trace); condensed `probe_M1_excerpt.txt`.
Candidate side received, once per game:
```
cand <--- setoption name TmFinishIteration value true
```
Base side received only Threads/Hash/OwnBook — no TmFinishIteration. (M2/M3 had no probe because
they were not played.)

## 6. From my partner (deepseek5) — read BEFORE this job, as the job asked

Read both `NOTES_deepseek5.md` and `REPORT_deepseek5_job1.md` from `for-fable-and-opus/deepseek5-work`
(fetches at 03:55 UTC). Quoted as the job asks:

- (a) floor of `go depth 1`: **median 0.17 ms, max 2.86 ms**.
- (b) largest overshoot it measured: **none — 0 of 3,600 searches exceeded its budget on any of
  the eleven `go` lines; the largest elapsed anywhere was 787 ms, at `go wtime 5000 …` (16 % of
  that budget)**. On `movetime` it stops ≈10 ms early (M−10 ≤ elapsed < M on all 300 searches per
  line), consistent with `Move Overhead 10`.
- (c) its losses on time: **tc=10+0.1: 0 in the 109 games reached (Part B was cut by its time
  limit); tc=1+0.01: NOT REACHED, so it has no number there**. My matches at tc=2+0.02 add the
  same answer on a faster control: 0 losses on time in 986 clocked games (K0+K1+M1).
- (d) lines beginning with "CORRECTION:" in its notes: **none** (I read the whole NOTES file).
- Applied: its Part B used `timemargin 0` — I used `timemargin=0` as my job also requires; its
  "no Elo table after interrupt" experience told me to compute M1's numbers from per-game lines
  myself instead of waiting for a table that never comes. Its move-overhead finding is why I
  report 2+0.02 as safe: even at wtime=20 ms the engine's max elapsed was 2.07 ms, so 2 s budgets
  are nowhere near the danger zone on this machine.
- Checked (its numbers vs mine): its four step-0 numbers are identical to mine on an independent
  build — the strongest cross-check available so far, and it passed. Its 109-game ending counts
  (53 mate, 56 draw by rule, 0/0 losses on time) are internally consistent with its games file.

## 7. What I did NOT do

- **M2 (TmNodeShare) and M3 (both true): not played.** Reason: with the measured rate, an even G
  that would let both M1 and M2 finish before minute 50 came out ≈220 < 300, and the job says in
  that case play only M1 with all the time. TmNodeShare therefore has still no valid match —
  Fable should re-list it with a fresh seed.
- No second seed for M1 (the cut match consumed the whole window).
- No losses-on-time analysis by opening (none occurred; nothing to analyze).
- K1's Elo quoted from fastchess directly (my script validates on even-node data; K1's odds make
  the pair-interval path differ — I did not recompute it, I report fastchess's ±).

## 8. What I am NOT sure about

- Whether M1's negative lean (−10.7, LOS ≈ 8.8 %) is a real small loss or noise: 293 pairs cannot
  settle it; the interval [−26.2, +4.8] includes 0.
- Whether the 586-game M1 count is biased by the cut point: the interrupt fell mid-pair-294 (game
  587 unfinished); I excluded nothing (both games of every pair ≤ 293 had finished) — but a cut
  always raises the question, so treat M1 as one look, not two.
- The K0 noise floor sits at DrawRatio 52 % (much drawier than my fixed-nodes matches at 38–46 %)
  — clock games change the draw structure; small-Elo reads from few clocked games are even weaker
  than the fixed-nodes case, which is exactly the job's own warning.

## 9. A better way

- My per-game extractor (`make_gamelist.py`, committed) now feeds the whole pipeline: endings by
  side, complete-pair filtering, pooled intervals — one script for every future match, clocked or
  fixed-nodes. For clocked matches it needs one addition: parsing fastchess's loss-on-time
  wording per side into two columns (cand/base) automatically; today I did it by grep because no
  loss on time occurred.
- For the remaining switch (TmNodeShare) the clean design is the one this job would have used
  with more time: two 1,000-game matches with fresh seeds, run only when the rate allows both;
  if the rate stays ~19/min, that is two hours of machine time — a job file should say whether
  the session may span multiple hours for one standing job.

## 10. UTC stamps (recorded; minute 0 of the job = 03:56, when I read the file)

- 03:55:36 waiting command fired; FOUND FABLE_TO_glmflash5_2.md at attempt 1; partner branch
  fetch succeeded same second.
- 03:55–03:56 partner NOTES + REPORT read (quoted above); job file read at 03:56.
- 03:55:58–04:06:39 K0 (200 games, 10:41): −1.7 ± 25.8, 0 losses on time.
- 04:06:46–04:14:52 K1 (200 games, 8:06): +168.4 ± 30.6, 0 losses on time.
- 04:15:08 probe M1 (2 games, logged): option arrived on cand, not on base.
- 04:15:11 M1 launched in background (recorded PID and stamp).
- 04:45:55 planned interrupt; the sleeping command was backgrounded by my tooling at 28.3 min
  and kept running (shell id recorded); the first SIGINT went to the wrong PID (the nohup
  wrapper) and did not stop fastchess; the real SIGINT reached fastchess at ≈04:47.
- 04:47:xx fastchess exited ("Tournament was interrupted ... Finished match", 00:31:10 total,
  586 games finished); 04:47–04:52 gamelist, endings, pair stats computed.
- 04:52–05:00 this report and the notes written, committed, pushed.

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5.
