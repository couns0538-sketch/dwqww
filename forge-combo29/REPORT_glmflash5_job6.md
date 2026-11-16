# REPORT glmflash5 — JOB 6 — kimi5's TmSmoothStability patch on my clock (tc=2+0.02)

Branch `cursor/glmflash5-work-cb5c`. times: `tests_glmflash5_job6/stamps.txt` (one stamped line
per step, appended by the step's own command). No engine source committed; the patch was applied
to a COPY (`/tmp/forge-patched`), never to the repo tree.

## 1. What was asked, the answer, how sure

Asked: kimi5's TmSmoothStability patch (66 lines, three files, new switch default off) — verify
it changes nothing without the clock (I0/I1), that the harness sees changes when they exist (I2),
that the switch is live on the clock (I3), then its FIRST match S1 (PATCHED both sides, switch
vs none, tc=2+0.02, new openings, cut at minute 47), read against the expected cost of the time
it saves.

Answer: **Step 1 clean (all four pins exact; patch applied without rejects; TmSmoothStability
count 1). I0 50/50, I1 50/50, I2 0/50 (control sees), I3 shows the switch LIVE (none-vs-none
ratio 0.988 with 0/50 positions >20% different; none-vs-TSS ratio 0.926 with 3/50; the sum with
the switch on is smaller, 5073.6 vs 5478.0 ms). S1: −2.2 Elo, 95 % pair interval [−15.4, +11.1],
404 pairs (809 games finished, cut at minute 47, tc=2+0.02, built-in net) — inside the error;
losses on time 0/0.** With r = 0.985 (probe mean ON/OFF), the expected cost of the saved time is
168.4 × log2(0.985) = −3.8 Elo, so **S1 minus the expected cost = +1.6** — the smoother shape is
worth somewhere in [−12.2, +14.9] (S1's interval shifted by +3.8); nothing is separable from
zero at this clock.

How sure: sure of the identity chain and the liveness demonstration (raw rows committed for
every search); S1 is ONE look on ~400 pairs — the same size limits as jobs 2/3/5 apply.

## 2. Step 0 (the job-5 probe table, redone by thread id + name)

`probe_M2.log`: **go lines 1365 = bestmove lines 1365 = moves paired 1365** — every bestmove
paired with its own `go`. The simple (tid, name) pairing reproduces my job-5 table EXACTLY
(cand 682 moves, mean 44.0, median 29.4, max 323.5; base 683, 46.5, 33.6, 325.5): my job-5
reconstruction was already paired per game — one line as the job allows, with the counts beside
it (`probe_M2_move_times_v2.txt`). Fable's correction of the JOB-3 table (probe_M1b) stands —
that table was made with the name-only script and is withdrawn; nothing in job 3's Elo used it.

## 3. Step 1 — two exes (raw files in tests_glmflash5_job6/)

- patch fetched from `for-fable-and-opus/kimi5-work:forge-combo29/tests_kimi5_job2/TmSmoothStability.patch.txt`
  (66 lines); `git apply --check` OK, `git apply` OK — `patch_apply.txt`.
- BASE = `/tmp/forgebuild/forge` sha256 e06310ec…; PATCHED = `/tmp/forgebuild_patched/forge`
  sha256 6f7edcff… (`exe_sha256.txt`), both built with the same cmake/g++ command.
- `uci_patched.txt`: TmSmoothStability count 1.
- PATCHED with no option: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 =
  4865609 (`patched_bench*.txt`, `patched_perft5.txt`) — all four exact.

## 4. Games by ending FIRST, losses on time BY SIDE (S1: 809 finished, 404 pairs used)

| ending | count |
|--------|-------|
| Draw by 3-fold repetition | 309 |
| White mates | 209 |
| Black mates | 166 |
| Draw by insufficient mating material | 62 |
| Draw by fifty moves rule | 62 |
| Draw by stalemate | 1 |
| **loss on time cand / base** | **0 / 0** |
| illegal / disconnect / crash | 0 / 0 / 0 |

## 5. Table of the match (+ the step-3/4 evidence rows)

| item | result |
|------|--------|
| S1 | PATCHED both sides; cand TmSmoothStability=true; tc=2+0.02 both; seed 9330 (mine; job names none); openings_job6.epd order=sequential start=51 (lines 1–50 went to step 3) |
| games | 809 finished, 404 complete pairs used (809 odd → game 809 dropped with its unplayed partner) |
| W-L-D (cand) | 185-190-433; n5 = [7, 99, 196, 96, 6] |
| Elo | −2.15, 95 % pair interval [−15.41, +11.11], LOS 37.5 % |
| complete/cut | INCOMPLETE — SIGINT at 07:12:02 to fastchess's own pid (pgrep at cut time); fastchess total 00:44:32 |
| losses on time by side | 0 / 0 |
| validation line | 809/809 gamelist rows equal fastchess's own "Finished game" lines, 0 mismatches |
| fastchess last 40 lines | `S1_last40.txt` (no Elo table after the interrupt; computed from game lines, pentanomial method validated in job 1) |

Step 3 rows (one raw row per search: position|fen|nodes|bestmove|wall-ms per side):

| run | equal nodes | equal bestmove | reading |
|-----|-------------|----------------|---------|
| I0 PATCHED-none vs BASE-none, go nodes 20000 | **50/50** | 50/50 | the patch without the switch is the base engine |
| I1 PATCHED-TSS vs PATCHED-none, go nodes 20000 | **50/50** | 50/50 | the switch changes NOTHING at fixed nodes — the known answer holds |
| I2 PATCHED-HD vs PATCHED-none (CONTROL) | **0/50** | 29/50 | the check is not blind (nodes column is the sensitive one) |
| I3 clocked, none (run 1) | sum 5478.0 ms | — | — |
| I3 clocked, none again (run 2) | sum 5413.9 ms; ratio 0.988; 0/50 positions >20% differ | — | two no-option runs are near-identical |
| I3 clocked, TmSmoothStability=true (run 3) | sum **5073.6 ms**; ratio 0.926; **3/50** positions >20% differ | — | the switch is LIVE on the clock; sum smaller, as the patch predicts |

(The I3 console print had a label bug of mine — it printed run 1's sum again under run 3's
label; the summary `identity_I3.txt` was recomputed from the three raw run files, which are
committed.)

## 6. The probe (TEN games, PATCHED both sides, option on the candidate only)

Raw `probe_S1.log`; delivery: cand received `setoption name TmSmoothStability value true` 10/10,
base received none; the clock line reached both sides. Per-move table by thread id and name
(`probe_S1_move_times.txt`, script `move_times_split.py`): **go 1388 = bestmove 1388 = paired
1388**; 10 games; per side:

| side | moves | mean | median | max | own 1–20 (n=196) | own 21–40 (n=180) | own 41+ (n=318) |
|------|-------|------|--------|-----|------------------|-------------------|------------------|
| cand (ON) | 694 | 44.8 | 30.5 | 420.5 | 82.2 / 62.4 / 420.5 | 42.5 / 34.2 / 228.3 | 23.0 / 18.6 / 120.5 |
| base (OFF) | 694 | 45.5 | 30.3 | 365.6 | 85.3 / 66.0 / 365.6 | 41.3 / 31.4 / 217.4 | 23.4 / 19.2 / 132.0 |

(mean/median/max ms per bucket.) **r = mean ON/OFF = 44.8/45.5 = 0.985.** The shape difference
sits where the patch says: the ON side gives back a little in its moves 1–20, takes a little more
in 21–40 (it holds searches longer when the bestmove keeps changing), and its single worst move
is LONGER (420.5 vs 365.6 ms) while its long tail beyond move 40 is shorter. In ten games the
MEAN barely moves (−1.5 %) — much less than I3's −7.4 % on isolated fresh searches; the two
settings measure different things and I do not equate them.

## 7. From my partners

- kimi5's patch is the object of this job; its model's predicted sign pattern (never later than
  the step function, earlier at counts 2/4/5) shows in my probe as: max move LONGER on the ON
  side, mid-game bucket slightly longer, early moves shorter. Its predicted "sum smaller" held
  in I3. Nothing to correct in the patch itself; the patch's own switch-off chain stayed intact
  (I0/I1 50/50 is the direct test).
- deepseek5: nothing of its newest work touches this job directly; its ucinewgame-per-search
  practice (from Opus's advice, quoted in Fable's file) is exactly what my I0–I3 driver does.
- Fable's rule now in force — every per-move table from a multi-game log prints "bestmove lines"
  beside "moves paired": done for both probes (1365/1365 and 1388/1388).

## 8. What I did NOT do

- No second seed for S1 (one look; the cut at minute 47 is the job's own rule).
- No full-match trace log (per-move buckets for S1 itself were not asked; the probe carries the
  time analysis).
- No calibration match 2+0.02 vs 1.5+0.015 (Fable names it as the NEXT job if r < 0.95 — r is
  0.985, so it is not triggered by that rule; S1 being inside its error is the other trigger and
  that is Fable's call, not mine).
- Did not verify the patch's piecewise anchors by reading search.cpp myself (kimi5's description
  taken from Fable's file; my scope was the measurements).

## 9. What I am NOT sure about

- Whether the smoother shape has any strength value: S1 −2.2 [−15.4, +11.1] minus the expected
  −3.8 cost leaves +1.6 with at least the same error — zero is inside, twice over.
- Whether r measured on a 10-game probe transfers to the match (the probe's openings are lines
  1–10; the match starts at 51): r is a time-use ratio, likely stable, but unproven on the
  match's own games.
- The I3 wall times are MY driver's send-to-receive times on an idle machine (deepseek5's floor:
  ~0.17 ms median round trip) — small against the ~110 ms mean per search, but present.

## 10. A better way

- The expected-cost arithmetic assumes the saving acts like a uniform time-odds r. A DIRECT
  calibration match (BASE 2+0.02 vs BASE 1.5+0.015, r = 0.75 measured how it converts) would
  replace the log2(r) model with a measured curve at this clock; two 300-game matches would do.
- My I0–I3 driver now does, in one run (~20 s), everything a "does this switch touch anything
  without the clock" check needs; it should run on every future patch job BEFORE any match
  (I0/I1 = the owner's-PC 100/100 check, in the exact form a cloud machine can reproduce).

## 11. UTC stamps

times: see `tests_glmflash5_job6/stamps.txt` (found 06:24:56Z; step 0 06:25; patch+build 06:26;
pins 06:27; openings 06:28; I0–I3 06:29–06:31; probe 06:31–06:32; S1 launched 06:32:2xZ; SIGINT
07:12:00Z; exited 07:12:02Z, total 00:44:32; stats 07:12–07:14; report 07:14–07:24, commit
stamped by git).

## 12. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
