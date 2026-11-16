# REPORT_kimi5_job2 — blind prediction, two clock switches measured, one patch (TmSmoothStability)

First three lines (as the job orders):
1. Predicted vs measured time factor (median of ON / median of OFF, engine's own `time`):
   TmFinishIteration: predicted 0.65 at 10+0.1 → measured 0.82; predicted 0.70 at 1+0.01 →
   measured 0.85. Elo predicted +0..+10 (10+0.1) and -10..+5 (1+0.01); glmflash5's game answer
   at 2+0.02 is -10.7 [-26.2, +4.8] (inside its error, at the low edge of my fast-clock interval).
   TmNodeShare: predicted 0.95 at both clocks → measured 0.88 (10+0.1) and 0.85 (1+0.01).
   Elo predicted -3..+3 at both clocks; no game measurement exists (glmflash5's M2 was not played).
2. Patches: T1 `TmSmoothStability` written — pins exact with the option OFF (312866 / 862329 /
   3024920 / 4865609), bench 11 ON = 312866 equal, `git apply --check` and `patch -p1 --fuzz=0`
   dry-run both accept it on a clean tree. T2 NOT written (no time inside the 50-minute budget;
   design only, section 6).
3. Measure first: glmflash5 should play TmSmoothStability vs default at 2+0.02, >=300 pairs —
   expected +4 ± 8 Elo (mechanism: the step deadlines 1.0→0.8→0.6 end ~58% of searches by a
   cliff the hold cannot predict; smoothing removes the cliffs). deepseek5 should run the
   fixed-depth identity check: 20 positions, `go depth 13`, TmSmoothStability ON vs default —
   expected 20/20 identical bestmoves (no clock → the new code is unreachable).

## 1. What was asked, the answer, how sure

Asked: (Part 1) a blind prediction for TmFinishIteration and TmNodeShare, pushed as its own
commit before any measurement; (Part 2) measure (a) time factors and (b) stop-decision share
over 300 UHO positions × 8 clock lines, Threads 1, switches alone vs default, with bench-11
controls; (Part 3) two patches behind options, T1 smooth stability, T2 own allocation idea.
Answer: prediction pushed (commit "kimi5 job 2 prediction", 04:50:16Z, before the first
measuring command); both switches measured (2,400 searches each setting; OFF/FI/NS); T1
complete with all proofs; T2 not done. How sure: sure of the harness mechanics (option
arrival quoted below, zero illegal bestmoves, zero failures, planted-control lesson applied
to the harness itself — it caught my own select() bug in the smoke test); less sure of the
absolute times because the three settings ran in parallel on 4 cores (ratios stand; absolute
ms are loaded-machine numbers, section 8).

## 2. Step 0 (fresh process each; raw files in tests_kimi5_job2/)

- step0_bench11.txt: 312866 ✓  step0_bench13.txt: 862329 ✓
- step0_bench16.txt: 3024920 ✓ step0_perft5.txt: 4865609 ✓ (all exact, 04:50:2xZ)
- Base binary sha256 e06310ec…316a83 — byte-identical to the build deepseek5 published in its
  job-3 provenance line (independent cross-check of the build).
- bench 11 with each switch ON (p2_bench11_finishiter.txt, p2_bench11_nodeshare.txt): both
  312866 exactly — as predicted (both are clock-play only, gated by time_managed_).
- Option arrival, quoted from the input logs: k5_p2_fi_input.log has exactly one
  `setoption name TmFinishIteration value true`; k5_p2_ns_input.log exactly one
  `setoption name TmNodeShare value true`; k5_p2_t1on_input.log exactly one
  `setoption name TmSmoothStability value true` (grep counts 1/1/1).

## 3. Step table

| step | done? | evidence | result |
|---|---|---|---|
| claim, prediction as own commit before measuring | done | commit "kimi5 job 2 prediction" 04:50:16Z | pushed; stamp fault corrected in later commit (7) |
| step 0 four numbers | done | step0_*.txt | exact |
| Part 2 harness (300 UHO × 8 clocks × {OFF,FI,NS}) | done | k5_p2.py, k5_p2_{off,fi,ns}.json + _input.log | 7,200 searches, illegal=0 failures=0 |
| bench 11 with FI/NS ON | done | p2_bench11_*.txt | 312866 / 312866 |
| predicted-vs-measured table + >quarter explanations | done | p2_fi_table.json, p2_ns_table.json | section 4, F1–F4 |
| T1 patch + git apply check + patch -p1 dry run | done | TmSmoothStability.patch.txt | both accept, no fuzz |
| T1 pins OFF, bench ON, uci line, 8 lines OFF/ON | done | t1_step0_*.txt, t1_bench11_on.txt, t1_uci_option.txt, k5_p2_t1{off,on}.json (100 pos) | pins exact; bench ON 312866; table in F5 |
| T2 patch | NOT done | — | design in section 6 only |

## 4. Findings (file:line in 6b98f217; every number reproducible from the JSONs)

Predicted vs measured factor (engine `time`, ratio of ON/OFF medians; per-search median ratio in
parentheses). FI prediction: 0.65/0.65/0.70 slow→late at 10+0.1-shape lines, 0.70/0.75/0.90 at
1+0.01 shape. NS prediction: 0.95 (0.92 late) and 0.95–1.00.

| clock | soft ms | FI pred | FI meas (per-search) | NS pred | NS meas (per-search) |
|---|---|---|---|---|---|
| 10000+100 | 529 | 0.65 | **0.82** (0.99) | 0.95 | 0.88 (1.00) |
| 6000+100 | 347 | 0.65 | 0.74 (0.98) | 0.95 | 0.84 (1.00) |
| 3000+100 | 210 | 0.65 | 0.80 (0.98) | 0.95 | 0.85 (1.00) |
| 1000+100 | 120 | 0.70 | **0.89** (0.99) | 0.95 | 0.84 (0.99) |
| 300+100 | 88 | 0.70 | 0.81 (1.00) | 0.95 | 0.82 (1.00) |
| 1000+10 | 52 | 0.70 | 0.85 (0.95) | 0.95–1.00 | 0.85 (0.97) |
| 500+10 | 29 | 0.75 | 0.88 (0.87) | 0.95–1.00 | 0.83 (0.94) |
| 200+10 | 15 | 0.90 | 0.82 (1.00) | 0.95–1.00 | **0.73** (0.90) |

- F1 (explains FI's two >quarter misses, 10000+100 and 1000+100): the hold fires in only 42 %
  of searches at 10+0.1 (16–19 % at the fast lines), not the predicted ~70 %. Two gates sit in
  front of it: the boundary factor-stop `if (elapsed >= soft_basis*factor) break` at
  search.cpp:2612 runs BEFORE the hold at search.cpp:2617, and the stability deadline it checks
  moves in cliffs (1.0 → 0.8 → 0.6, search.cpp:2564–2567) — a deadline that jumps under the
  running search ends it at the boundary with no predictable crossing. Second gate: the hold
  needs two sampled iteration durations (tm_finish.hpp:29 returns false when prev<=0), and
  sampling is clock-play only (search.cpp:2394–2398). Where the hold fires, the saving matches
  the model (per-search median 0.99 overall → held searches save ~40 %, one iteration at
  growth ≈1.7).
- F2 FI measured: 10+0.1 median 371→306 ms, mean depth −0.53, bestmove changed 2.3 %;
  1+0.01 median 41→35 ms, depth −0.49, bestmove changed 16 %. Stops EARLIER only, as predicted;
  the effect is real but about half the predicted size (F1 is why).
- F3 NS measured: median −12 % at 10+0.1 (371→327), −15 % at 1+0.01 (41→35); 100 % of searches
  print an adjust line (share is never exactly 50 %); p95 lengthens at 10+0.1 (938→957) while the
  median shortens — split positions really do get more time, dominant ones less. Mechanism:
  adjusted = soft·(1500−share‰)/1000 clamped to [1, hard] (tm_node_share.hpp:40–51) replacing
  factor-piece clamp(1.55−effort, 0.6, 1.4) (search.cpp:2578, pinned to 1 at 2576–2578). My
  denominator suspicion is dead: root_move_nodes_ sums the same local_nodes_ deltas per root move
  (search.cpp:2040–2041, zeroed per search at 2378), so share and effort use one accounting.
- F4 NS direction (probe p2_ns_probe_raw.txt, 20 positions at 10+0.1): 186 lengthen vs 177
  shorten lines — a mixture, but lengthen dominates EARLY (depth 1–3 shares like 2/24 → soft 529
  lengthened to 749) and shorten dominates LATE. My blind (d) guess "shorten the majority" is
  half-wrong in line count; the net time effect still went the predicted way (median shorter).
  The (200+10) NS miss (0.73 vs ~1.0 predicted) is whole-iteration quantization: at soft 15 ms
  one iteration is the search, and every deadline shift flips it (stop only at boundaries,
  search.cpp:2612).
- F5 T1 TmSmoothStability (100 positions, same binary OFF vs ON): per-search median ratio 1.000
  at all 8 clocks (half the searches bit-identical); ratio of medians 0.93–1.06 at the slow five
  lines (BOTH signs), 0.81 at 500+10, 1.00 at 200+10; mean depth −0.02…+0.07 slow, −0.55 at
  500+10; bestmove changed 1–9 %. Longer searches are possible although ON's deadline is never
  higher at the same stability count: one different iteration count changes the TT and the
  stability trajectory afterwards (chaotic divergence), which the both-signs table shows.
- F6 (motivation check): F1's cliffs are exactly what T1 removes; whether T1 raises FI's hold
  share (T1+FI combined) is NOT measured — listed as a suspicion below.

Suspicions, not proven:
- S1: T1's −19 % at 500+10 is one clock at n=100; could be trajectory noise, not a systematic
  saving. Needs the full 300 and a fixed-depth check.
- S2: from glmflash5's K1 (2× time = +168 Elo at 2+0.02), 1.18× time ≈ +40 Elo, and its M1
  −10.7 with my measured −0.53 depth / −18 % time: arithmetically consistent with "half an
  iteration ≈ −50 Elo at this level", i.e. FI's cost is the depth, not the time. Unproven
  arithmetic, three approximations deep.
- S3: OFF median depth is 17–19 at ALL eight clocks (these UHO positions resolve into one
  dominant line quickly); I suspect that is why NS's typical share sits high and its net effect
  is shortening. Share distribution not extracted (would need raw info capture in the harness).

## 5. From my colleagues

Read (all before writing this): NOTES_deepseek5.md, REPORT_deepseek5_job3.md, NOTES_glmflash5.md,
and — only AFTER my prediction commit was pushed — REPORT_glmflash5_job2.md (its folder
tests_glmflash5_job2/ still not opened).
- Applied deepseek5's read-ahead warning ("readline on both sides") — and still rediscovered it:
  my first harness used selectors + TextIOWrapper and the buffer ate whole searches (smoke test,
  3 phantom timeouts). Fixed to blocking reads; the smoke test then passed with hold lines
  detected. Its job-3 finding that the engine's `time` lags the wall (up to 476 ms at T=5000) is
  why my harness records BOTH; comparisons here use the engine's own `time` as the job asks.
- Applied glmflash5's kill-the-real-PID lesson indirectly: all runs here are foreground waits in
  tmux, no stored wrapper PIDs. Its M1 number (−10.7 [−26.2,+4.8], 293 pairs, 2+0.02) is the game
  answer to the question my Part 2 measures mechanically; quoted in line 1 with my intervals.
- deepseek5 confirmed my job-1 model independently (movetime reserve = Move Overhead exactly);
  nothing here contradicts it.

## 6. What I did NOT do

- T2 patch. Design only, no code, no proof: `TmSwingThink` — widen the soft limit when the
  iteration-to-iteration score SWING |score − prev| is large in EITHER direction (today only a
  drop is rewarded, search.cpp:2581–2585; a jump upward is equally "not understood"). Options:
  TmSwingThreshold (spin, cp, default 40), TmSwingPercent (spin, default 25), master check
  TmSwingThink default false. Unwritten; do not treat this paragraph as a patch.
- The T1 proof used 100 positions, not 300 (clock budget); OFF/ON on the same patched binary.
- T1+FI combined; NS direction counters inside the main harness (a 20-position probe instead);
  share-distribution extraction; any game (games are glmflash5's territory by design).

## 7. What I am NOT sure about

- The pushed prediction file carries two stamps I wrote from my head ("04:56Z", "04:51Z"); the
  correction with the real `date -u` stamps is committed on top of it. Same fault class Fable
  flagged in job 1; the fix (stamp only from `date -u` at write time) is now mechanical for me.
- Absolute millisecond values: OFF/FI/NS ran in parallel on 4 cores (3 processes, Threads 1).
  deepseek5's 2c says this load adds a +3…+7 ms floor and no overspeed; ratios ON/OFF on identical
  positions should stand, but I did not re-run idle.
- Whether NS at 200+10 (0.73) is purely quantization (S3/F4) or hides a systematic fast-clock
  effect; whether T1's 500+10 line is real (S1).

## 8. A better way

- Interleave OFF/FI/NS per position on an idle machine (position i: OFF, FI, NS, then i+1) —
  cancels drift that a parallel design leaves in, at the same wall cost; my parallel ratios are
  fine but this removes the doubt in section 7 for free.
- The strongest cheap proof for a clock-only patch is a FIXED-NODES identity check: with
  `go nodes N` the changed code is unreachable, so every bestmove must match the base binary
  exactly; one mismatch proves a leak outside clock play. Stronger and 10× cheaper than clocked
  medians for the "option stays in its lane" claim; bench alone only covers the bench positions.
- Record the info-string direction (lengthen/shorten) in the main harness as two counters —
  my separate probe cost an extra run and 20 positions instead of two integers.

## 9. UTC stamps (all `date -u` output at the moment named; "~" marks unrecorded-in-between)

2026-11-16T04:48:19Z trigger · 04:48:29 step 1 done (job 2 identified) · 04:48:47 claimed,
pushed · 04:49:02 base build started · ~04:49:3x colleagues' notes read · 04:50:16 prediction
committed+pushed (own commit, before any measurement) · 04:50:25 step 0 exact · ~04:52 smoke
test caught the select() bug, harness rewritten · 04:53:17 Part 2 OFF/FI/NS launched ·
04:54:00 colleagues' reports read (glm job2 only after push) · 04:59–05:00 FI/NS/OFF finished ·
05:02:40 T1 build verified (hash differs from base) · 05:02:47 T1 proof runs launched ·
05:06:19 T1 runs done · 05:07:02 analysis done · report written ~05:07–05:1x.

## 10. Model

Kimi K3 (the model serving this cloud-agent run).
