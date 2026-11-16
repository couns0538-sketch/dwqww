# REPORT glmflash5 — JOB 17 — fut15 and the reduction's tt-pv term, under S14, two node counts

Branch `cursor/glmflash5-work-cb5c`. B7 = plain base tree 6b98f217 + kimi5's
`tests_kimi5_job7/LmrTtPv.patch.txt` (applied from the repository root on a COPY; the patch is
one option `LmrTtPv`, default 1, and one line: `if (ss->tt_pv) r -= tune::LmrTtPv;` — deepseek5's
LmrTerms.patch.txt was not needed, kimi5's applied clean). B7 sha256
926f48eba93f5583b6b6cb117de92852d85b7d4113c15526f537282cc18611c2. All five matches COMPLETE.
times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: under S14 (both sides), is the bare futility margin too tight (fut15 = 1.5× wider), and
what does the reduction's tt-pv term (LmrTtPv 0 = the discount removed) do — each at 20,000 and
2,000 nodes; plus M31 (futoff's incremental value on S14) if the gate allowed.

Answer: **M27 (S14+fut15 vs S14, 20k): +3.47 [−6.57, +13.52], 1,000 pairs — level, one seed.**
**M28 (S14+ttpv0 vs S14, 20k): −3.82 [−13.86, +6.21] — level, leaning the predicted negative,
one seed.** **M29 (fut15, 2k): −5.73 [−17.43, +5.96] and M30 (ttpv0, 2k): +4.69 [−7.33, +16.71]
— both FLIP the sign of their 20,000-node twins, both inside their errors: no depth story is
shown.** **M31 (S14+futoff vs S14, 20k, 600 pairs): −6.37 [−19.34, +6.60] — level, leaning
negative; it sits between Opus's PC −2.95 and my defaults' pool −13.47: under S14 the futility
step's marginal value shrinks toward the PC's.**

Step 4's sentence: **fut15 changed at least one game in 999 of 1,000 pairs at 20,000 nodes and
999 of 1,000 at 2,000; ttpv0 changed at least one game in 1,000 of 1,000 pairs at BOTH node
counts** (the identical-pairs count is 0 everywhere except M29's 1) — both switches act on
nearly every game; neither shows a strength sign at either depth.

How sure: all six step-1 rows exact (the anchor held; ttpv0's 8,572,032 and S14's rows equal
Fable's; S14+futoff 9,971,731 is MY first measurement — Fable held that one back); five probes
exact with values verified; every table below comes from the committed `job17_stats.py` with its
identity printed by the same command. Five single seeds.

## 2. Step 1 — six rows beside Fable's (`job17_rows.txt`, driver `job17_rows.py` COMMITTED)

| setting | first-3 nodes | Fable's known | sum over 200 | known |
|---------|---------------|---------------|--------------|-------|
| no option (ANCHOR) | 18407, 25756, 64000 | same ✓ | 12,573,318 | ✓ held |
| ttpv0 (no S14) | 13360, 26010, 35674 | (kimi5's/Fable's sum) | 8,572,032 | ✓ exact |
| S14 | 41311, 24872, 28574 | same ✓ | 9,500,069 | ✓ |
| S14 + ttpv0 | 11818, 14586, 39264 | same ✓ | 7,102,738 | ✓ |
| S14 + fut15 | 35294, 27286, 28958 | same ✓ | 9,432,393 | ✓ |
| S14 + futoff | 26422, 32757, 33032 | MINE (Fable held it back) | 9,971,731 | — |

Pins, no option: bench 11 = 312,866, bench 13 = 862,329, perft 5 = 4,865,609 ✓
(`b7_bench*.txt`, `b7_perft5.txt`). Refusal lines: 0 everywhere. (Honesty note: a first
sed-mangled driver produced two void rows — S14+pv1 printed S14's numbers and the ttpv0 rows
were missing; caught by reading the summary against the settings before use, redone with a
hand-written driver; the void run's files were overwritten by the redo in the commit.)

## 3. Step 2 — five probes (`probe_M27…M31.log`; probe openings lines 5001–5050, no match uses
them)

Every probe: base received its 14 setting lines in 10 of 10 games (140 = 14×10) and NOTHING else
(0 extras); the candidate the same 14 plus its own lines with their values (M27/M29:
FutilityBase=150 and FutilityMultiplier=165, 10/10 each; M28/M30: LmrTtPv=0, 10/10; M31:
FutilityBase=500 and FutilityMultiplier=500, 10/10); refusal lines 0; every `go` carried the
match's own nodes value (go-limit counts 1215, 2416, 1502, 1027, 1306 — all equal to all `go`
lines; pasted lines: `<--- go nodes 20000` (M27/M28/M31), `<--- go nodes 2000` (M29/M30)).

## 4. The matches (B7 both sides; S14 on BOTH sides; the candidate's own lines on top; nodes as
named; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours swapped, `-pgnout` in
my folder; openings_job17.epd = book minus jobs 2,3,5–16 openings (36,109 distinct removed;
Random(11503); 5,800 lines; first line `rnbq1rk1/pppp1pbp/4p1p1/3BP1N1/8/2P5/PP1P1PPP/RNBQK2R b
KQ - 0 7`), order sequential; M27 1–1000, M28 1001–2000, M29 2001–3000, M30 3001–4000, M31
4001–4600; concurrency 4)

**Every number below comes out of the committed `job17_stats.py` (output `job17_stats_out.txt`),
which prints the identity under each table. Games by ending FIRST (losses on time BY SIDE 0/0
in all five; illegal/disconnect/crash 0):**

| ending | M27 (2000) | M28 (2000) | M29 (2000) | M30 (2000) | M31 (1200) |
|--------|------------|------------|------------|------------|------------|
| White mates | 584 | 600 | 725 | 697 | 366 |
| Black mates | 466 | 480 | 664 | 634 | 298 |
| 3-fold repetition | 652 | 646 | 318 | 385 | 371 |
| fifty moves | 152 | 155 | 185 | 184 | 100 |
| insufficient material | 144 | 117 | 98 | 97 | 61 |
| stalemate | 2 | 2 | 10 | 3 | 4 |
| **identity: mates = wins+losses** | 584+466 = 535+515 = 1050 ✓ | 600+480 = 529+551 = 1080 ✓ | 725+664 = 678+711 = 1389 ✓ | 697+634 = 679+652 = 1331 ✓ | 366+298 = 321+343 = 664 ✓ |

| match | cand | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | complete? (duration) | identical pairs |
|-------|------|-------|------|-------|-------|----|-------------------------|----------------------|-----------------|
| M27 | S14+fut15 | 20000 | 9940 | 1000 | 535-515-950 | [51,231,406,271,41] | +3.47 [−6.57, +13.52] | COMPLETE (11:46) | 0 |
| M28 | S14+ttpv0 | 20000 | 9950 | 1000 | 529-551-920 | [49,251,420,233,47] | −3.82 [−13.86, +6.21] | COMPLETE (11:47) | 0 |
| M29 | S14+fut15 | 2000 | 9960 | 1000 | 678-711-611 | [102,208,403,195,92] | −5.73 [−17.43, +5.96] | COMPLETE (1:47) | 1 |
| M30 | S14+ttpv0 | 2000 | 9970 | 1000 | 679-652-669 | [93,223,355,222,107] | +4.69 [−7.33, +16.71] | COMPLETE (1:50) | 0 |
| M31 | S14+futoff | 20000 | 9980 | 600 | 321-343-536 | [30,154,252,136,28] | −6.37 [−19.34, +6.60] | COMPLETE (7:34) | 0 |

**One table — fut15 and ttpv0 at both node counts; M31 beside my defaults' futoff pool:**

| setting | 2,000 nodes | 20,000 nodes |
|---------|-------------|--------------|
| fut15 − S14 | −5.73 [−17.43, +5.96], 1,000 pairs | +3.47 [−6.57, +13.52], 1,000 pairs |
| ttpv0 − S14 | +4.69 [−7.33, +16.71], 1,000 pairs | −3.82 [−13.86, +6.21], 1,000 pairs |
| futoff − S14 | — | −6.37 [−19.34, +6.60], 600 pairs |
| (futoff − none, MY DEFAULTS, two seeds) | −8.69 [−20.98, +3.61] (job 15) | −13.47 [−20.84, −6.10] (pool M13+M19) |

predictions.txt (before M27): M27 +4 [−8,+16] — held; M28 −6 [−18,+6] — held; M29 +3 [−9,+15]
— held; M30 −5 [−15,+5] — held; M31 −4 [−16,+8] — held. All five held.

## 5. From my partners

- deepseek5's job-26 regret rows under S14 (1.5× margin: −38 % drops, −54 % regrets, tree 0.993)
  — my M27 is its games-side test: level (+3.5); the regrets it found are not buying Elo at this
  size.
- Opus's PC matches: cut-node term off −0.61, futoff −2.95, both-off −14.95 — my M31 (−6.4)
  sits near his futoff number: under S14 the two engines now roughly agree on futility's
  marginal value.
- Fable's correction of its own file-16 sentence (the cut-node term DOES move nodes internally,
  only the total stays) — noted; no number of mine depended on it.

## 6. What I did NOT do

- No second seeds (five single looks).
- No ttpv values between 0 and 1 (the option's range goes to 4; kimi5's design allows a discount
  of 2 — unmeasured).
- The 2,000-node matches are 1,000 pairs each; the job's "identical-pairs" lens showed the
  switches act everywhere — the size story (S-sign flips between depths) needs seeds, not more
  single looks.

## 7. What I am NOT sure about

- Whether fut15's +3.5 (20k) and −5.7 (2k) are ONE number seen through seed noise (the
  difference of the two is ~9.2 with ~10.1 combined error — nothing shown).
- Whether ttpv0's true value is ~0 (both looks straddle zero from opposite sides).
- Whether S14+futoff's tree (9,971,731, +4.9 % over S14) and its −6.4 games say the same thing
  (a tree number says nothing about strength — job 13's rule, applied).

## 8. A better way

- The identical-pairs count is a cheap, strong "does the switch act in games" lens (0 vs 764 in
  job 15's M20 separated acting vs barely-acting switches instantly); it should be part of
  EVERY match's stats output — it is now, in `job17_stats.py`.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 13:23:53Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job17/
=== ls tests_glmflash5_job17:
b7_bench11.txt
b7_bench13.txt
b7_perft5.txt
cmd_M27.txt
cmd_M28.txt
cmd_M29.txt
cmd_M30.txt
cmd_M31.txt
config_M27.json
config_M28.json
config_M29.json
config_M30.json
config_M31.json
gamelist_M27.txt
gamelist_M28.txt
gamelist_M29.txt
gamelist_M30.txt
gamelist_M31.txt
job17_rows.py
job17_rows.txt
job17_stats_out.txt
job17_stats.py
job17_summary.txt
LmrTtPv.patch.txt
M27_last40.txt
M27_stdout.txt
M28_last40.txt
M28_stdout.txt
M29_last40.txt
M29_stdout.txt
M30_last40.txt
M30_stdout.txt
M31_last40.txt
M31_stdout.txt
make_openings_job17.py
openings_job17.epd
prediction.txt
probe_M27.log
probe_M28.log
probe_M29.log
probe_M30.log
probe_M31.log
stamps.txt
```
(the `??` line is the job folder itself before this commit.)

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
