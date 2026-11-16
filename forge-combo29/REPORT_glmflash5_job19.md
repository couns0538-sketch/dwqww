# REPORT glmflash5 — JOB 19 — pv1 by nodes: the ladder 1,000 / 2,000 / 5,000 / 10,000 / 20,000

Branch `cursor/glmflash5-work-cb5c`. Exe = B6, sha256
9938d88062cdfa9b8d18752a76c35519d8d36307dbbf14ebeba5ecef771e0bb1 (as jobs 16–18). All six
matches COMPLETE — nothing was cut. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: M34's second seed at 2,000 nodes; which part of pv1 carries the gain (pvall = all six
steps exempt, vs pv1 = only late-move pruning); the node ladder down to 1,000; the tool-sees-it
control (2,000 vs 1,000 nodes).

Answer: **M36 (pv1 @2k, second seed): +76.25 [+64.08, +88.41] — REPRODUCES M34's +75.34; the
two-seed pool at 2,000 nodes is +75.79 [+67.03, +84.55] over 2,000 pairs.** **The ladder (pv1 −
S14, one seed per rung): 1,000 nodes +91.15 [+77.95, +104.36]; 2,000 +75.79 pool; 5,000 +27.68
[+16.67, +38.69]; 10,000 +20.52 [+9.96, +31.08]; 20,000 +11.21 [+3.99, +18.43] (pool) —
monotone DOWN as nodes rise: the exemption is worth ~9× more at 1,000 nodes than at 20,000.**
**M37 (pvall @2k): +41.54 [+28.93, +54.15] — pvall is BELOW pv1 (75.8 pool) by ~34: the five
extra exemptions cost about half the LMP exemption's gain at 2,000 nodes — the LMP exemption
alone carries it (one seed each).** **M41 (control): +209.91 [+172.27, +247.54] — the tool sees
the node doubling at shallow depth clearly.**

How sure: every table below comes from the committed `job19_stats.py` with all three identities
printed by the same command (mates = wins+losses; n5 sums to pairs; wins+losses+draws = games);
step-1's four rows exact (pvall = 9,966,105 = deepseek6's); six probes exact. The ladder's
rungs are one seed each; the 2,000 rung is two seeds.

## 2. Step 1 — rows beside the knowns (`job19_rows.txt`, driver `job19_rows.py` COMMITTED)

| setting | first-3 nodes | known | sum over 200 | known |
|---------|---------------|-------|--------------|-------|
| no option (ANCHOR) | 18407, 25756, 64000 | same ✓ | 12,573,318 | ✓ held |
| S14 | 41311, 24872, 28574 | same ✓ | 9,500,069 | ✓ |
| S14+pv1 | 17188, 26670, 44100 | same ✓ | 9,476,627 | ✓ |
| S14+pvall | 20126, 24962, 37387 | same ✓ (deepseek6's) | 9,966,105 | ✓ |

Pins: 312,866 / 862,329 / 4,865,609 ✓.

## 3. Step 2 — six probes (`probe_M36…M41.log`; probe openings lines 5201–5260, no match uses
them)

Every probe: base received its 14 setting lines ×10 (140) and nothing else; cand received the 14
plus its own lines with values (M36/M38/M39/M40: SoundPvArm=1 + SoundStepMask=1, 10/10 each;
M37: SoundPvArm=1 + SoundStepMask=63, 10/10 each; M41: NOTHING extra — cand 0, base 0); refusal
lines 0; every `go` carried the match's own nodes value (per-side for the one-sided probes:
M36/M37 2000, M38 1000, M39 5000, M40 10000 — counts equal to all `go` lines). **Honesty note:
the M41 PROBE was run with a one-sided nodes=2000 (my probe call's mistake — the base's `go`
lines carried 2000 too, 670/670, so the two-sided go check was not exercised there); the REAL
M41 command is hand-written with per-engine nodes and its own output line confirms
"2000 nodes - 1000 nodes".**

## 4. The matches (B6 both sides; S14 both sides; candidate's lines on top; nodes as named
(per-engine for M41: cand 2000, base 1000); Threads 1, Hash 16, OwnBook false, no adjudication,
pairs colours swapped, `-pgnout` in my folder; openings_job19.epd = book minus jobs 2,3,5–18
openings (43,709 distinct removed; Random(11703); 5,260 lines; first line
`r1b2rk1/ppqn1ppp/2pb1n2/3pp3/8/3PPPP1/PPPN1NBP/R1BQK2R w KQ - 3 9`), order sequential; M36
1–1000, M37 1001–2000, M38 2001–3000, M39 3001–4000, M40 4001–5000, M41 5001–5150; concurrency
4; `job19_match.sh` (committed) wrote each exact `cmd_<M>.txt` before the run — M41's command
hand-written because the driver is one-nodes-shaped)

All numbers below from the committed `job19_stats.py` (output `job19_stats_out.txt`), which
prints the identities. Games by ending FIRST (losses on time BY SIDE 0/0 in all six;
illegal/disconnect/crash 0):

| ending | M36 (2000) | M37 (2000) | M38 (2000) | M39 (2000) | M40 (2000) | M41 (300) |
|--------|------------|------------|------------|------------|------------|-----------|
| White mates | 738 | 781 | 837 | 671 | 625 | 124 |
| Black mates | 652 | 617 | 682 | 576 | 515 | 118 |
| 3-fold repetition | 319 | 320 | 232 | 433 | 558 | 31 |
| fifty moves | 177 | 178 | 150 | 194 | 156 | 15 |
| insufficient material | 105 | 97 | 87 | 116 | 142 | 11 |
| stalemate | 9 | 7 | 12 | 10 | 4 | 1 |
| identity mates = W+L | 738+652 = 911+479 = 1390 ✓ | 781+617 = 818+580 = 1398 ✓ | 837+682 = 1016+503 = 1519 ✓ | 671+576 = 703+544 = 1247 ✓ | 625+515 = 629+511 = 1140 ✓ | 124+118 = 202+40 = 242 ✓ |

| match | cand | base | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | complete? (duration) |
|-------|------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M36 | S14+pv1 | S14 | 2000 | 10030 | 1000 | 911-479-610 | [46,132,353,282,187] | +76.25 [+64.08, +88.41] | COMPLETE (2:01) |
| M37 | S14+pvall | S14 | 2000 | 10040 | 1000 | 818-580-602 | [84,164,341,252,159] | +41.54 [+28.93, +54.15] | COMPLETE (1:56) |
| M38 | S14+pv1 | S14 | 1000 | 10050 | 1000 | 1016-503-481 | [53,127,319,256,245] | +91.15 [+77.95, +104.36] | COMPLETE (1:15) |
| M39 | S14+pv1 | S14 | 5000 | 10060 | 1000 | 703-544-753 | [51,199,387,266,97] | +27.68 [+16.67, +38.69] | COMPLETE (3:35) |
| M40 | S14+pv1 | S14 | 10000 | 10070 | 1000 | 629-511-860 | [44,212,407,256,81] | +20.52 [+9.96, +31.08] | COMPLETE (6:41) |
| M41 | S14@2000 | S14@1000 | 2000/1000 | 10080 | 150 | 202-40-58 | [1,8,33,44,64] | +209.91 [+172.27, +247.54] | COMPLETE (0:15) |

**The pv1-by-nodes table (the job's ask):**

| nodes | pv1 − S14, Elo, 95 % pair interval | pairs | source |
|-------|-------------------------------------|-------|--------|
| 1,000 | +91.15 [+77.95, +104.36] | 1,000 | M38, one seed |
| 2,000 | **+75.79 [+67.03, +84.55]** | 2,000 | **M34+M36 pool, two seeds** |
| 5,000 | +27.68 [+16.67, +38.69] | 1,000 | M39, one seed |
| 10,000 | +20.52 [+9.96, +31.08] | 1,000 | M40, one seed |
| 20,000 | +11.21 [+3.99, +18.43] | 2,000 | M24+M32 pool (job 18), two seeds |
| pvall at 2,000 (beside pv1's 75.8) | +41.54 [+28.93, +54.15] | 1,000 | M37, one seed |

predictions.txt (before M36): M36 +70 [+55,+85] — held (+76.25); M37 +55 [+30,+80] — held
(+41.54); M38 +90 [+65,+115] — held (+91.15); M39 +40 [+20,+60] — held (+27.68); M40 +25
[+8,+42] — held (+20.52); M41 +180 [+120,+240] — held (+209.91). All six held.

## 5. From my partners

- Opus's PC ladder counterpart does not exist yet for 2,000 (its SPRT at `go softnodes 2000` is
  running there); my ladder gives the shape it will be compared against.
- deepseek6's pvall row reproduced to the node on my B6 (step 1) — its patch-chain work checks
  out on my side.
- kimi5's job-9 null-move findings and deepseek5's killer-regret shares — noted for the queue;
  nothing of mine used them this job.

## 6. What I did NOT do

- No second seeds for the ladder rungs 1,000 / 5,000 / 10,000 (one seed each; the 2,000 and
  20,000 rungs are the two-seed ones).
- No pvall rung beyond 2,000 (the job asked one).
- The M41 probe defect (one-sided nodes) — the probe's delivery counts stand, its go-limit check
  did not exercise the two-sided case; the real match's own output line is the proof of form.

## 7. What I am NOT sure about

- The exact SHAPE between rungs (my five points are single seeds; the 2k→5k drop (76→28) is the
  steepest and the one a second seed would sharpen first).
- Whether pvall's +41.5 vs pv1's +75.8 difference (~34) is the five exemptions' cost or partly
  seed noise (one seed each).
- Whether the ladder transfers to the PC's engine (its 20,000-node pv1 number disagrees with my
  tree's at the same settings — the disagreement is now bounded: at 2,000 nodes my tree says
  +75.8 two-seed; the PC's answer there is being played).

## 8. A better way

- The ladder design (same exe, same settings, only `nodes` changes, one openings file with
  disjoint line ranges) is the cheapest way to map any switch's node-dependence: ~16 minutes
  bought five rungs + a control. It should be the standard follow-up whenever a switch shows a
  big effect at one node count (job 18's M34 → this job in one hour).

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 14:44:05Z)

```
=== git status --short:
?? forge-combo29/REPORT_glmflash5_job19.md
?? forge-combo29/tests_glmflash5_job19/
=== ls tests_glmflash5_job19:
b6p_bench11.txt
b6p_bench13.txt
b6p_perft5.txt
cmd_M36.txt
cmd_M37.txt
cmd_M38.txt
cmd_M39.txt
cmd_M40.txt
cmd_M41.txt
config_M36.json
config_M37.json
config_M38.json
config_M39.json
config_M40.json
config_M41.json
gamelist_M36.txt
gamelist_M37.txt
gamelist_M38.txt
gamelist_M39.txt
gamelist_M40.txt
gamelist_M41.txt
job19_match.sh
job19_rows.py
job19_rows.txt
job19_stats_out.txt
job19_stats.py
job19_summary.txt
M36_last40.txt
M36_stdout.txt
M37_last40.txt
M37_stdout.txt
M38_last40.txt
M38_stdout.txt
M39_last40.txt
M39_stdout.txt
M40_last40.txt
M40_stdout.txt
M41_last40.txt
M41_stdout.txt
make_openings_job19.py
openings_job19.epd
prediction.txt
probe_M36.log
probe_M37.log
probe_M38.log
probe_M39.log
probe_M40.log
probe_M41.log
stamps.txt
```
(the `??` lines are the report and the job folder before this commit. The pin files' names are
`b6p_*` — the same files job 18 used, copied into this folder so the pins travel with the job.)

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable (away), read by Opus, paired with
deepseek5, kimi5 and deepseek6.
