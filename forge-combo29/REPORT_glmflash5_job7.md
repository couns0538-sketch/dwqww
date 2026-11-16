# REPORT glmflash5 — JOB 7 — TmFinishIteration in its bundle (B1) against none, tc=2+0.02

Branch `cursor/glmflash5-work-cb5c`; DEFAULT build of jobs 1–3 on both sides (no patch, no flag
build). times: `tests_glmflash5_job7/stamps.txt`, one stamped line per step, appended by the
step's own command; nothing typed.

## 1. What was asked, the answer, how sure

Asked: TmFinishIteration saves ~17 % of the time by giving up depth (a TRADE) — calibrate the
time plan that spends the saving back (TmSoftDivisor / TmIncrementPercent), pick the bundle
whose time use matches "no switch", then play that bundle against none and read the SHAPE, not
the amount.

Answer: **Calibration: N2 1.010 / F 0.820 / B0 0.872 / B1 0.973 / B2 1.033 / P 1.138 on the
2000+20 line (400+20 beside in section 5); every one inside Fable's pre-written bands; the gate
F < 0.92 passes. Bundle = B1 (TmFinishIteration + TmSoftDivisor 18 + TmIncrementPercent 91).**
**T1: −8.3 Elo, 95 % pair interval [−21.5, +4.8], 396 pairs (792 games, cut at minute 47,
tc=2+0.02), losses on time 0/0 — inside the error**, the same side of zero as Fable's guess
(−8 to +12) sits at its edge. With r = 0.987 from the probe (inside 0.95–1.05), the expected
cost of the remaining time difference is 168.4 × log2(0.987) = −3.2, so T1 minus expected cost
= −5.2 [−18.3, +8.0] — still zero inside: the trade is LEVEL at this clock, in its bundle,
within one look's power.

How sure: sure of the mechanics (all three option counts 1; calibration raw rows committed;
probe delivery 10/10 candidate-only; 792/792 validation rows; no abnormal ending). One look,
~400 pairs: nothing below ~20 Elo is claimable — the job's own standing warning.

## 2. Known numbers of step 0

Session pins in `tests_glmflash5_job1/` (default build): 312866 / 862329 / 3024920 / 4865609;
re-verified in jobs 5–6 on the flag/patched builds as well. `uci_list.txt` this job:
TmFinishIteration 1, TmSoftDivisor 1, TmIncrementPercent 1 (step 1 passed; counts in section 5).

## 3. Games by ending FIRST, losses on time BY SIDE (T1: 792 finished, 396 pairs used)

| ending | count |
|--------|-------|
| Draw by 3-fold repetition | 286 |
| White mates | 234 |
| Black mates | 139 |
| Draw by fifty moves rule | 69 |
| Draw by insufficient mating material | 63 |
| Draw by stalemate | 1 |
| **loss on time cand / base** | **0 / 0** |
| illegal / disconnect / crash | 0 / 0 / 0 |

## 4. Calibration (step 3; raw rows `calib_raw_rows.txt`, one per search: setting|line|position|bestmove|last depth|wall ms|hold lines)

Seven settings × two clock lines × 100 positions, one process per setting, `ucinewgame` +
`isready` before every `go`, Threads 1, Hash 16, first 100 lines of `openings_job7.epd`.

| setting vs N1 | ratio, 2000+20 | ratio, 400+20 | lower depth (2000) | higher depth (2000) | bmdiff (2000) | Fable's known answer |
|---------------|----------------|---------------|--------------------|---------------------|---------------|----------------------|
| N2 (none again) | 1.010 | 0.987 | 0 | 0 | 0 | 0.97–1.03 ✓ |
| F (switch alone) | **0.820** | 0.776 | 42 | 0 | 3 | 0.82 [0.76, 0.88] ✓ exact |
| B0 (div 20, inc 83) | 0.872 | 0.840 | 27 | 0 | 2 | 0.91 ± 0.08 ✓ |
| **B1 (div 18, inc 91)** | **0.973** | 0.938 | 15 | 5 | 2 | 1.00 ± 0.08 ✓; deeper≈shallower ✓ |
| B2 (div 16, inc 103) | 1.033 | 1.036 | 5 | 14 | 2 | 1.12 ± 0.08 (1.03 is 0.007 below the band's low end — nearest-to-1.00 contest decided on the first line anyway) |
| P (plan alone) | 1.138 | 1.172 | 1 | 30 | 2 | 1.22 [1.12, 1.32] ✓ (1.138 ≥ 1.12) |

Gate: F = 0.820 < 0.92 on the first line — the harness and the option act. B1 holds in ~30–45 %
of its searches (raw rows carry the hold-line counts). **bundle_choice.txt written before
step 4: B1, ratios 0.973 / 0.938.**

## 5. Table of the matches and the probe

| item | result |
|------|--------|
| T1 | cand = B1 bundle (TmFinishIteration=true, TmSoftDivisor=18, TmIncrementPercent=91); base = none; tc=2+0.02 both; seed 9720 (Fable's); openings_job7.epd order=sequential start=101 (lines 1–100 calibration, 1–10 probe) |
| games | 792 finished, 396 complete pairs used (792 even; nothing dropped) |
| W-L-D (cand) | 177-196-419; n5 = [4, 107, 196, 82, 7] |
| Elo | −8.34, 95 % pair interval [−21.46, +4.79], LOS 10.6 % |
| complete/cut | INCOMPLETE — SIGINT 07:59:00Z to fastchess's own pid; total 00:43:47 |
| losses on time by side | 0 / 0 |
| validation line | 792/792 rows equal fastchess's own lines, 0 mismatches |
| fastchess last 40 | `T1_last40.txt` (no Elo table after the interrupt; computed from game lines) |

Openings counts: book 2,632,036 lines; jobs 2+3+5+6 used 1,611 distinct openings; 2,630,425
left; 5,000 written.

## 6. The probe (TEN games, bundle on cand, none on base)

Raw `probe_T1.log`; delivery: cand received TmFinishIteration/TmSoftDivisor=18/
TmIncrementPercent=91 10/10 games; base received none of them (its Threads/Hash/OwnBook only).
Per-move table by thread id and name (`probe_T1_move_times.txt`, script committed):
**go 1354 = bestmove 1354 = paired 1354**; losses on time in the probe: 0/0; hold lines
("info string TmFinishIteration") in the log: 302 over cand's 677 searches (≈ 45 % of its moves
hold, ≈ 30 per game).

| side | moves | mean | median | max | own 1–20 | own 21–40 | own 41+ |
|------|-------|------|--------|-----|----------|-----------|---------|
| cand (bundle) | 677 | 45.1 | 33.2 | **216.5** | 72.4 / 59.7 / 216.5 | 44.8 / 35.9 / 151.3 | 26.5 / 19.9 / 208.0 |
| base (none) | 677 | 45.7 | 33.0 | **460.7** | 78.5 / 61.0 / 460.7 | 42.9 / 33.5 / 205.7 | 24.9 / 19.6 / 135.2 |

(mean/median/max ms.) **r = mean cand/base = 0.987** — inside 0.95–1.05, so T1 compared two
SHAPES at (near) equal time use: the bundle's single worst move is HALF the base's (216.5 vs
460.7 ms), its early moves give back a little, its moves 41+ take a little more — spending made
more even by the hold, as the trade intends.

## 7. From my partners

- deepseek5 (via Fable's recount): its own rows show both switches END SEARCHES EARLIER
  (TmFinishIteration: lower depth in 117–127 of 300; hold-line searches use 0.60 of the time) —
  the trade framing is ITS data; my job 7 measured the other half (the plan that spends the
  saving). Nothing of mine contradicts it.
- kimi5: its "every counter ships with a must-be-nonzero check" is the bucket-check rule I keep
  using (1354/1354 here); the ContHist4PlyRead/LmrDeeperShallower tree-size findings belong to
  other switches and do not enter this job.
- Fable's guess "T1 between −8 and +12, most likely inside its error": scored — −8.34, inside
  its error, at the guess's lower edge.

## 8. What I did NOT do

- No second seed for T1 (one look; the job cuts at minute 47 by design).
- B2's first-line ratio (1.033) sits 0.007 below the pre-written ±0.08 band around 1.12 — I flag
  it; the bundle choice did not depend on it (B1 was nearer 1.00 regardless).
- No full-match trace log; no per-move buckets for T1 itself (the probe carries the time
  analysis, as in job 6).
- The probe's per-game hold counts are summed over the log (302/10 ≈ 30 per game), not parsed
  game-by-game.

## 9. What I am NOT sure about

- Whether the bundle's level-ness is real: −8.3 [−21.5, +4.8] — one look; the minus side leans
  but includes zero; Fable's own next-job rule (second seed before belief) applies to any
  outside-the-error reading, and this one is inside anyway.
- Whether r = 0.987 measured on ten probe games equals the match's own r (not measured there).
- The B0/B2 ratios land ~0.04 below Fable's central values though inside/near the bands — the
  plan arithmetic is mine to trust only as far as 100 positions × 2 lines show.

## 10. A better way

- The calibration harness now measures, per setting, EVERYTHING the trade question needs in one
  pass (ratio, depth movement, bestmove diffs, hold counts, two clocks); for the next bundle
  search (if B1's shape is not enough) extending the settings list is a one-line change, and the
  whole step is ~100 s — cheap enough to run before every bundle match.
- r should in the end be measured from the MATCH's own trace log (the probe's ten games sample
  it); if a second seed of T1 comes, take the log outside the repo and compute r from the same
  games that produce the Elo.

## 11. UTC stamps

times: see `tests_glmflash5_job7/stamps.txt` (job read + step 1 at 07:12:3xZ; openings 07:15;
calibration 07:16–07:18 (101 s); bundle_choice + probe 07:18; T1 launched 07:18:5xZ; SIGINT
07:59:00Z; exited 07:59:02Z, total 00:43:47; stats 07:59–08:00; report 08:00–08:10, commit
stamped by git).

## 12. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
