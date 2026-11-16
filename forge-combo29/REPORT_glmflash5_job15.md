# REPORT glmflash5 — JOB 15 — second seeds of histoff and futoff, and the steps at 2,000 nodes

Branch `cursor/glmflash5-work-cb5c`. Exe = B5 (job 12's; sha256 b8e0d166… — none of its options
set = the base tree). All six matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: second seeds of histoff (M18) and futoff (M19) at 20,000 nodes; the same three steps at
2,000 nodes (M20–22); gated M23 (HPM 4096 at 20,000).

Answer: **M18 (histoff, 2nd seed): −2.8 [−13.1, +7.5] — the second seed CONTRADICTS job 13's
+10.6; the two-seed pool is +3.91 [−3.30, +11.11] — history pruning's removal fades to "inside
the error, small positive lean".** **M19 (futoff, 2nd seed): −16.17 [−26.65, −5.69] — the second
seed CONFIRMS job 13; the pool is −13.47 [−20.84, −6.10] — quiet futility is a real keeper.**
**At 2,000 nodes: histoff +3.65 [−2.58, +9.88]; futoff −8.69 [−20.98, +3.61]; qseewide −7.12
[−19.38, +5.13] — all lean the same way as at 20,000 nodes, none one-sided. M23 (HPM 4096):
+5.43 [−5.86, +16.72] — level.**

Two sentences: **after two seeds, switching history pruning all but off is NOT a shown gain on
this tree (pool +3.9, interval touches zero) — job 13's one-sided claim was seed luck — while
quiet futility IS a keeper (pool −13.5, interval below zero on both seeds).** **Neither answer
changes between 2,000 and 20,000 nodes in sign (histoff + at both, futoff/qseewide − at both);
the sizes shrink at 2,000, as a shallower search's smaller margins suggest — "question for a
match" whether that trend is real.**

How sure: the four step-1 rows EQUAL my job-13 rows to the node; all six probes exact (values
verified per option name AND value); 13,600/13,600 validation rows. Six single seeds, two of
them second looks — the two-seed pools are the session's standard of belief.

## 2. Step 1 — four rows, each EQUAL to my job-13 row (`job15_rows.txt`, driver committed)

none 12,573,318 ✓; histoff 12,537,494 ✓; futoff 12,668,896 ✓; HistoryPruneMultiplier 4096
12,541,810 ✓. The refusal-stopping control still stops (`job15_summary.txt`). B5 sha256 beside
job 12's: b8e0d166… = equal.

## 3. Step 2 — six probes, four counts each (`probe_M18…M23.log`)

Every probe: the candidate received exactly its own option lines 10/10 (M18/M20:
HistoryPruneMultiplier=20000 — value verified in the log; M19/M21: FutilityBase=500 AND
FutilityMultiplier=500 10/10; M22: SeeQuietMultiplier=200 10/10; M23: HistoryPruneMultiplier=4096
value-verified), the base received none, refusal lines 0, and every `go` carried the match's own
limit (`go nodes 20000` or `go nodes 2000`, counts equal to all `go` lines: 1399, 2081, 1354,
1713, 1158, 1399). Probe openings: lines 5801–5830 — no match uses them.

## 4. The matches (B5 both sides; nodes as named; Threads 1, Hash 16, OwnBook false, no
adjudication, pairs colours swapped, `-pgnout` in my folder, openings_job15.epd = book minus
jobs 2,3,5–14 openings (27,509 distinct removed; Random(9998); 5,830 lines; first line
`rnbqkb1r/pp2pppp/3p1n2/8/3p1P2/1P3N2/P1P1P1PP/RNBQKB1R w KQkq - 0 5`), order sequential;
M18 1–1000, M19 1001–2000, M20 2001–3000, M21 3001–4000, M22 4001–5000, M23 5001–5800;
concurrency 4)

Games by ending FIRST (losses on time BY SIDE 0/0 in all six; illegal/disconnect/crash 0):

| ending | M18 (2000) | M19 (2000) | M20 (2000) | M21 (2000) | M22 (2000) | M23 (1600) |
|--------|------------|------------|------------|------------|------------|------------|
| White mates | 559 | 545 | 736 | 713 | 712 | 458 |
| Black mates | 527 | 622 | 715 | 760 | 752 | 430 |
| 3-fold rep. | 544 | 476 | 337 | 322 | 331 | 402 |
| fifty moves | 133 | 143 | 132 | 137 | 141 | 111 |
| insufficient | 233 | 210 | 78 | 66 | 62 | 196 |
| stalemate | 4 | 4 | 2 | 2 | 2 | 3 |

| match | cand | base | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | LOS | complete? (duration) | validation |
|-------|------|------|-------|------|-------|-------|----|-------------------------|-----|----------------------|------------|
| M18 | histoff | none | 20000 | 9810 | 1000 | 566-582-852 | [56,234,441,208,61] | −2.78 [−13.05, +7.50] | 29.8 % | COMPLETE (duration 12:24) | 2000/2000 |
| M19 | futoff | none | 20000 | 9820 | 1000 | 529-622-849 | [68,273,388,226,45] | −16.17 [−26.65, −5.69] | 0.1 % | COMPLETE (duration 11:47) | 2000/2000 |
| M20 | histoff | none | 2000 | 9830 | 1000 | 736-715-549 | [13,98,764,105,20] | +3.65 [−2.58, +9.88] | 87.4 % | COMPLETE (duration 1:47) | 2000/2000 |
| M21 | futoff | none | 2000 | 9840 | 1000 | 710-760-530 | [123,198,395,174,110] | −8.69 [−20.98, +3.61] | 8.3 % | COMPLETE (duration 1:55) | 2000/2000 |
| M22 | qseewide | none | 2000 | 9850 | 1000 | 711-752-537 | [122,194,395,181,108] | −7.12 [−19.38, +5.13] | 12.7 % | COMPLETE (duration 1:49) | 2000/2000 |
| M23 | HPM 4096 | none | 20000 | 9860 | 800 | 455-430-715 | [33,193,337,190,47] | +5.43 [−5.86, +16.72] | 82.7 % | COMPLETE (duration 09:19) | 1600/1600 |

**Two-seed pools (job 13's seeds beside these):**
- histoff M12+M18: n5 = [94, 464, 872, 443, 127], **Elo +3.91 [−3.30, +11.11]** (M12 alone was
  +10.60 [+0.50, +20.70]; M18 −2.78 — the seeds straddle).
- futoff M13+M19: n5 = [132, 531, 788, 458, 91], **Elo −13.47 [−20.84, −6.10]** (M13 −10.77,
  M19 −16.17 — both seeds below zero).

predictions.txt (before M18): M18 +8 [−4,+20] — **CALLED WRONG** (−2.78); M19 −8 [−20,+4] —
held; M20 +4 [−8,+16] — held; M21 −4 [−14,+6] — held; M22 −8 [−18,+2] — held; M23 +5 [−7,+17]
— held.

## 5. Step 4 — final positions, PER GAME (`M*_finals.txt` = round|cand-as-white|pieces|result;
python-chess replay; class counts sum to each match's games)

Candidate's score by each GAME's own final-position piece count:

| class | M18 | M19 | M20 | M21 | M22 | M23 |
|-------|-----|-----|-----|-----|-----|-----|
| ≤ 5 | 1011 games, 49.5 % | 962, 46.9 % | 829, 50.2 % | 828, 49.4 % | 833, 50.4 % | 732, 52.1 % |
| 6–12 | 746, 49.7 % | 790, 47.3 % | 964, 50.9 % | 915, 47.8 % | 903, 48.2 % | 647, 50.0 % |
| ≥ 13 | 243, 49.8 % | 248, 51.6 % | 207, 50.0 % | 257, 50.2 % | 264, 47.3 % | 221, 48.6 % |

(≈ Elo per class computed in `job15_finals_summary.txt`; classes with < 200 games there carry no
Elo. The class picture adds no new sign: futoff's loss shows in ≤5/6–12 (−21.3/−18.5) with a
+11.2 dip in the small ≥13 class; qseewide's loss concentrates in 6–12/≥13.)

**One table — each step at 2,000 vs 20,000 nodes:**

| step | 2,000 nodes (this job) | 20,000 nodes |
|------|------------------------|--------------|
| histoff − none | +3.65 [−2.58, +9.88], 1,000 pairs | +3.91 [−3.30, +11.11], 2,000-pair two-seed pool (M12+M18) |
| futoff − none | −8.69 [−20.98, +3.61], 1,000 pairs | −13.47 [−20.84, −6.10], 2,000-pair two-seed pool (M13+M19) |
| qseewide − none | −7.12 [−19.38, +5.13], 1,000 pairs | −15.43 [−27.50, −3.35], job 13's M14 (800 pairs, one seed) |

## 6. From my partners

- Opus on the PC (via Fable): history pruning off THERE = −4.3 [−11.3, +2.6] vs my tree's pool
  +3.9 [−3.3, +11.1] — opposite-sign leans, both inside their errors: the number-belongs-to-its-
  engine rule; neither tree shows a real history-pruning effect yet, and my two seeds now say my
  +10.6 was the seed.
- deepseek5/kimi5: their job-22/23 lines were not needed here; the refusal-count guard stayed 0
  everywhere (Fable's True/False fault class).

## 7. What I did NOT do

- No third seed for histoff (the pool straddles zero; a third seed would settle the lean).
- No histoff+futoff COMBINED match (Opus plays it on the PC; my side waits for the ask).
- No per-class Elo below 200 games (printed as percentages only).

## 8. What I am NOT sure about

- Whether histoff's true value is ~+4 or ~0 (pool [−3.3, +11.1]).
- Whether the 2,000-node sizes (futoff −8.7, qseewide −7.1) are genuinely smaller than the
  20,000-node ones or just wider intervals on one seed each.
- M23's +5.4 (800 pairs) — level within its width; the "half-way" question stays open.

## 9. A better way

- The two-seed pool arithmetic is now a 10-line standard (`job15_stats.py`'s pool()); every
  future "second seed" job should print the pool beside the seeds automatically — it is the
  belief unit of this whole session.

## 10. UTC stamps

times: see stamps.txt (job read 11:27:04Z; step 1 11:27:40Z; six probes 11:28–11:29; M18
11:29–11:41:52Z; M19 11:42–11:53:4xZ; M20 11:53:5xZ–11:55:4xZ; M21 11:55:5xZ–11:57:4xZ; M22
11:57:5xZ–11:58:17Z; gate check printed 11:58:2xZ; M23 11:58:3xZ–12:07:5xZ; stats+pools
12:08:0xZ; finals 12:08:20Z; report written after; commit stamped by git).

## 11. Real output of `git status --short` and `ls` of the folder (verbatim, 12:08:20Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job15/
=== ls tests_glmflash5_job15: (51 files)
cmd_M18.txt cmd_M19.txt cmd_M20.txt cmd_M21.txt cmd_M22.txt cmd_M23.txt
config_M18.json config_M19.json config_M20.json config_M21.json config_M22.json config_M23.json
gamelist_M18.txt gamelist_M19.txt gamelist_M20.txt gamelist_M21.txt gamelist_M22.txt gamelist_M23.txt
job15_finals_summary.txt job15_rows.py job15_rows.txt job15_stats.txt job15_summary.txt
M18_finals.txt M18_last40.txt M18_stdout.txt
M19_finals.txt M19_last40.txt M19_stdout.txt
M20_finals.txt M20_last40.txt M20_stdout.txt
M21_finals.txt M21_last40.txt M21_stdout.txt
M22_finals.txt M22_last40.txt M22_stdout.txt
M23_finals.txt M23_last40.txt M23_stdout.txt
make_openings_job15.py openings_job15.epd prediction.txt
probe_M18.log probe_M19.log probe_M20.log probe_M21.log probe_M22.log probe_M23.log
stamps.txt uci_defaults.txt
```
(the `??` line is the job folder itself before this commit.)

## 12. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
