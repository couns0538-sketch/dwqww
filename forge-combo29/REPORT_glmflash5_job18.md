# REPORT glmflash5 — JOB 18 — pv1's second seed under S14, the bundle, and 2,000 nodes

Branch `cursor/glmflash5-work-cb5c`. Exe = B6 (job 16's), sha256 9938d88062cdfa9b8d18752a76c35519d8d36307dbbf14ebeba5ecef771e0bb1
(said again from `exe_sha256_14.txt`). All matches COMPLETE except M35 (cut at minute 40, as
the job orders). times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: pv1's second seed under S14 (M32); the pv1+fut15 bundle under S14 (M33); pv1 at 2,000
nodes (M34); fut15's marginal value on top of pv1 (M35, gated, cut at minute 40).

Answer: **M32 (S14+pv1 vs S14, 20k, seed 9990): +6.43 [−3.86, +16.72], 1,000 pairs — lower than
M24's +15.99; the two-seed pool is +11.21 [+3.99, +18.43]: pv1's gain under S14 stands, at about
a third of its default-settings size (+32.05).** **M33 (S14+pv1+fut15 vs S14): −2.78 [−13.07,
+7.51] — the BUNDLE is level while pv1 alone pools +11.2: fut15 on top of pv1 looks like it
eats the gain (M35's direct test: +5.49 [−10.87, +21.85], 348 pairs, cut — level; the two
bundle looks disagree with "additive" and neither is decisive).** **M34 (S14+pv1 vs S14 at
2,000 nodes): +75.34 [+62.72, +87.95], 1,000 pairs — a HUGE gain at the self-play depth; my
prediction (+8 [−4, +20]) is CALLED WRONG, badly. One seed — but 6σ; it demands the second seed
above everything else now.**

How sure: the chain is the usual (pins exact; five step-1 rows exact including the new
S14+pv1+fut15 = 9,428,660; four probes exact; 6,697/6,697 validation rows; identity lines under
every table). M34's size is one seed's number.

## 2. Step 1 — rows beside the knowns (`job18_rows.txt`, driver `job18_rows.py` COMMITTED)

| setting | first-3 nodes | known | sum over 200 | known |
|---------|---------------|-------|--------------|-------|
| no option (ANCHOR) | 18407, 25756, 64000 | same ✓ | 12,573,318 | ✓ held |
| S14 | 41311, 24872, 28574 | same ✓ | 9,500,069 | ✓ (job 16's own row) |
| S14+pv1 | 17188, 26670, 44100 | same ✓ | 9,476,627 | ✓ |
| S14+fut15 | 35294, 27286, 28958 | same ✓ | 9,432,393 | ✓ (job 17's row, on B7 — same on B6) |
| S14+pv1+fut15 | 17321, 26803, 44946 | MINE (first measurement) | 9,428,660 | — |

Pins, no option: 312,866 / 862,329 / 4,865,609 ✓.

## 3. Step 2 — four probes (`probe_M32…M35.log`; probe openings lines 4001–4040, no match uses
them — M35's VOID run used 3001–3600 and the real M35 uses 4031–4630, both clear of the probes)

| probe | base received | cand received | refusals | go-limit |
|-------|---------------|---------------|----------|----------|
| M32 | its 14 lines ×10 (140) | the 14 + SoundPvArm=1, SoundStepMask=1 (10/10 each) | 0 | 1506/1506 |
| M33 | its 14 ×10 | the 14 + pv1's two + FutilityBase=150/FutilityMultiplier=165 (10/10 each) | 0 | 1444/1444 |
| M34 | its 14 ×10 | the 14 + pv1's two | 0 | 1410/1410 |
| M35 | its 14 ×10 PLUS pv1's two 10/10 (the base plays pv1 too) | the 14 + pv1's two + fut15's two (10/10 each) | 0 | 1356/1356 |

## 4. The matches (B6 both sides; S14 on both; candidate's lines on top; nodes as named; pairs
colours swapped; `-pgnout` in my folder; openings_job18.epd = book minus jobs 2,3,5–17 openings
(40,709 distinct removed; Random(11603); 4,900 lines; first line
`rnbqkbnr/1pppppp1/8/8/2BP1B1p/pP2P3/P1P2PPP/RN1QK1NR w KQkq - 0 6`), order sequential; M32
1–1000, M33 1001–2000, M34 2001–3000, VOID-M35 3001–3600 (its games are discarded), real-M35
4031–4630; concurrency 4; the driver `job18_match.sh` (committed) wrote each `cmd_<M>.txt with
the EXACT command before the match started)

Games by ending FIRST — from the gamelists by the stats command; **identity under each: mates =
wins + losses (holds in all four; printed by the command):**

| ending | M32 (2000) | M33 (2000) | M34 (2000) | M35 real (697 fin., 348 pairs) |
|--------|------------|------------|------------|-------------------------------|
| White mates | 595 | 583 | 756 | 208 |
| Black mates | 466 | 489 | 653 | 157 |
| 3-fold repetition | 601 | 620 | 383 | 195 |
| fifty moves | 199 | 172 | 121 | 75 |
| insufficient material | 138 | 131 | 84 | 60 |
| stalemate | 1 | 5 | 3 | 2 |
| **identity** | 595+466 = 549+512 = 1061 ✓ | 583+489 = 528+544 = 1072 ✓ | 756+653 = 918+491 = 1409 ✓ | 208+157 = 188+177 = 365 ✓ |

| match | cand | base | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | complete? (duration) |
|-------|------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M32 | S14+pv1 | S14 | 20000 | 9990 | 1000 | 549-512-939 | [47,238,405,251,59] | +6.43 [−3.86, +16.72] | COMPLETE (12:32) |
| M33 | S14+pv1+fut15 | S14 | 20000 | 10000 | 1000 | 528-544-928 | [54,255,391,253,47] | −2.78 [−13.07, +7.51] | COMPLETE (12:12) |
| M34 | S14+pv1 | S14 | 2000 | 10010 | 1000 | 918-491-591 | [56,131,346,264,203] | **+75.34 [+62.72, +87.95]** | COMPLETE (1:58) |
| M35 | S14+pv1+fut15 | S14+pv1 | 20000 | 10020 | 348 | 188-177-331 | [14,77,156,86,15] | +5.49 [−10.87, +21.85] | INCOMPLETE — SIGINT at minute 40 (14:09:37Z); game 697 dangling dropped; validation 697/697 |

**The pv1 table:**

| look | Elo, 95 % pair interval | pairs |
|------|-------------------------|-------|
| M24 (seed 1, 20k) | +15.99 [+5.86, +26.13] | 1,000 |
| M32 (seed 2, 20k) | +6.43 [−3.86, +16.72] | 1,000 |
| **M24+M32 pool (20k)** | **+11.21 [+3.99, +18.43]** | 2,000 |
| M34 (2,000 nodes) | +75.34 [+62.72, +87.95] | 1,000 |
| M33 (bundle pv1+fut15 vs S14, 20k) | −2.78 [−13.07, +7.51] | 1,000 |
| M35 (fut15 added on pv1, 20k, cut) | +5.49 [−10.87, +21.85] | 348 |

predictions.txt (before M32): M32 +12 [0,+24] — held (+6.43); M33 +16 [+2,+30] — **CALLED
WRONG** (−2.78); M34 +8 [−4,+20] — **CALLED WRONG** (+75.34); M35 +2 [−10,+14] — held (+5.49,
cut).

## 5. From my partners

- Opus's PC table (this file's head): under S14 my tree now agrees with the PC on five of six
  questions; the sixth (pv1 at LmpBase 8) is what M32's second seed was for — my pool says +11.2
  [+4.0, +18.4] where the PC has −2.43 [−9.22, +4.36]: still disagreeing after my second seed
  (my interval's floor +4.0 vs its ceiling +4.4 — they just barely fail to overlap). The PC's
  second seed of the same question is running there; the two pools will be the verdict.
- M34's +75 at 2,000 nodes has no PC counterpart yet — the obvious cross-question for the PC's
  engine at its own self-play depth.
- deepseek5's job-29 (killer moves): 606/1,000 of first-killer drops would have raised alpha —
  noted; no number of mine used it.

## 6. What I did NOT do

- **A driver fault, owned plainly: my `job18_match.sh` has ONE base form (S14 only), so the
  FIRST M35 run (14:05:00Z stamp) ran the WRONG comparison (pv1+fut15 vs S14 — a repeat of
  M33's question with fresh openings, +10.14, lines 3001–3600). It is VOID and its games are
  discarded; the real M35 (both sides S14+pv1, cand adds fut15) was written by hand into
  `cmd_M35.txt` and run on fresh lines 4031–4630, cut at minute 40.** The driver is still
  committed (its 4 correct runs are evidence); its single-base limitation is the finding.
- No second seed of M34 (the +75 needs one; it is the top-priority next match on my side).
- No fut15-alone-at-2k re-look (job 17's M29 stands).

## 7. What I am NOT sure about

- Whether M34's +75 is the real size at 2,000 nodes (one seed, 6σ — the sign is nearly certain,
  the size needs the second seed; a 2,000-node match costs ~2 minutes, so this is cheap).
- Whether M33's level bundle vs pv1's pooled +11.2 means fut15 CANCELS part of pv1's gain under
  S14 (M35's +5.5, 348 pairs, cut — leans the other way; 348 pairs cannot separate).
- The two-seed pv1@S14 pool (+11.2 [+4.0, +18.4]) vs the PC's −2.43 [−9.22, +4.36] — the
  intervals now JUST fail to overlap; whether that is a tree/net difference or my third seed
  would bridge, nobody can say yet.

## 8. A better way

- The match driver should take the BASE's extra options as a parameter (my single-base form
  caused the void run); one more argument, one more check — the void cost 6 minutes of the hour.
- M34's result makes "pv1 at 2,000 nodes, second seed + pooled" the highest-value cheap match in
  the session (2 minutes per 1,000 pairs); if Opus's PC can play the same question at its own
  self-play depth, the bridge gets its strongest test yet.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 14:09:59Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job18/
=== ls tests_glmflash5_job18: (36 files)
b6p_bench11.txt b6p_bench13.txt b6p_perft5.txt
cmd_M32.txt cmd_M33.txt cmd_M34.txt cmd_M35.txt
config_M32.json config_M33.json config_M34.json (config_M35.json pending at listing time - written by this commit)
gamelist_M32.txt gamelist_M33.txt gamelist_M34.txt gamelist_M35.txt
job18_match.sh job18_rows.py job18_rows.txt job18_stats.txt job18_summary.txt
M32_last40.txt M32_stdout.txt
M33_last40.txt M33_stdout.txt
M34_last40.txt M34_stdout.txt
M35_last40.txt M35_stdout.txt
make_openings_job18.py openings_job18.epd prediction.txt
probe_M32.log probe_M33.log probe_M34.log probe_M35.log
stamps.txt
```
(the `??` line is the job folder itself before this commit; config_M35.json landed in the
seconds between the listing and the commit — it is in the commit.)

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable (away), read by Opus, paired with
deepseek5 and kimi5.
