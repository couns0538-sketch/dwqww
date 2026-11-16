# REPORT glmflash5 — JOB 12 — SoundMatePruning's cases by games, on kimi5's B5 build

Branch `cursor/glmflash5-work-cb5c`. B5 = base tree 6b98f217 + kimi5's three job-5 patches
(SoundArms, SoundRegret, SoundSteps — applied in that order from the repository root on a COPY,
`patch_apply12.txt`; no engine source committed). times: pasted from stamps.txt (section 9).

## 1. What was asked, the answer, how sure

Asked: the three cases of SoundMatePruning as separate options (kimi5's arms patch), each alone
against no option, 20,000 nodes, 1,000 pairs (M11 800).

Answer: **M9 (pv1 = SoundPvArm 1 + SoundStepMask 1 vs none): +31.0 Elo, 95 % pair interval
[+20.4, +41.6], 1,000 pairs, COMPLETE — a large GAIN, more than 2.9σ from zero; my prediction
(−2, wrong outside [−12, +8]) is CALLED WRONG — the range failed.** **M10 (chk vs none): −6.3
[−16.5, +4.0] — inside the error, leaning negative; my range held.** **M11 (pv = SoundPvArm 1
alone, all six steps exempt at PV, vs none): +3.9 [−8.1, +15.9], 800 pairs — inside the error;
range held. M11 ran after all: M10 ended at minute 25.0, before the minute-29 gate (an early
stamp line of mine says "skipped" — the correction is stamped right after it).**

One sentence per setting: **pv1 is BETTER than no option on this tree at this depth (one look,
+31 [−20/+41 interval +20.4, +41.6] — a second seed is mandatory before anyone bundles it);
chk is equal-or-slightly-worse (−6.3 [−16.5, +4.0]); pv is EQUAL (+3.9 [−8.1, +15.9]) — and the
pair (pv1 +31, pv +4) says the gain lives in the late-move-pruning exemption ALONE; the other
five exemptions at PV nodes cost about what the LMP exemption pays.**

How sure: the mechanics are the strongest yet (B5's sha256 b8e0d166… EQUALS deepseek5's pinned
build hash — two machines, same bytes; all five known-answer rows exact including the 200-line
sums and the smp_mask0=none control; all three probes exact; 5,600/5,600 validation rows).
The +31 is one seed on fresh openings — the measurement chain is clean, the seed count is one.

## 2. Step 1 — rows beside the known answers (`job12_rows.txt`, driver `job12_rows.py` COMMITTED)

`go depth 12`, first 3 + sums over all 200 lines of kimi5's first200.fens, one process per
setting, refusal lines counted (0 everywhere):

| setting | first-3 nodes | known | sum over 200 | known |
|---------|---------------|-------|--------------|-------|
| none | 18407, 25756, 64000 | ✓ | 12,573,318 | ✓ |
| pv | 17200, 26267, 36908 | ✓ | 12,399,593 | ✓ |
| chk | 18410, 41328, 42607 | ✓ | 12,326,599 | ✓ |
| pv1 | 20223, 39123, 44776 | ✓ | 11,944,468 | ✓ |
| SoundMatePruning true + SoundStepMask 0 | = none on all three AND sum = none's | ✓ | 12,573,318 | ✓ |

Bench, no option: 312,866 / 862,329 ✓ (`b5_bench11/13.txt`). uci counts: SoundPvArm 1,
SoundInCheckArm 1, SoundMateAlphaArm 1, SoundStepMask 1 (`uci_b5.txt`). sha256: BASE e06310ec…,
B5 **b8e0d1668c9afe202a07ece8ad029914e0c44c029bb64fccf0f46c555a098dd2** — byte-identical to
deepseek5's pinned build of the same three patches (`exe_sha256_12.txt`).

## 3. Step 2 — three probes (`probe_M9/M10/M11.log` committed)

| probe | cand received | base received | unknown/invalid |
|-------|---------------|---------------|-----------------|
| M9 | SoundPvArm=1 10/10, SoundStepMask=1 10/10, InCheckArm 0 | all three 0 | 0 |
| M10 | SoundInCheckArm=1 10/10 (others 0) | all three 0 | 0 |
| M11 | SoundPvArm=1 10/10 (others 0) | all three 0 | 0 |

## 4. The matches (B5 both sides, nodes=20000, Threads 1, Hash 16, OwnBook false, no
adjudication, pairs colours swapped, openings_job12.epd = book minus the openings of jobs
2,3,5,6,7,8,9,10,11 (19,109 distinct removed; 2,612,927 left; Random(9980); 5,000 lines; first
line `rnb1kbnr/pp2qpp1/2ppp2p/8/4P3/2NPBN2/PPP1BPPP/R2QK2R b KQkq - 3 6`), order sequential;
M9 lines 1–1000, M10 1001–2000, M11 2001–2800; concurrency 4)

**Games by ending FIRST (losses on time BY SIDE 0/0 — fixed nodes; illegal/disconnect/crash 0):**

| ending | M9 (2000) | M10 (2000) | M11 (1600) |
|--------|-----------|------------|------------|
| White mates | 603 | 594 | 509 |
| Black mates | 541 | 524 | 429 |
| 3-fold repetition | 549 | 603 | 447 |
| fifty moves | 153 | 139 | 109 |
| insufficient material | 150 | 135 | 103 |
| stalemate | 4 | 5 | 3 |

| match | cand | base | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | LOS | complete? (duration) | validation |
|-------|------|------|------|-------|-------|----|-------------------------|-----|----------------------|------------|
| M9 | pv1 | none | 9410 | 1000 | 661-483-856 | [38,201,398,271,92] | **+31.00 [+20.36, +41.64]** | 100.0 % | COMPLETE (duration 11:43) | 2000/2000 |
| M10 | chk | none | 9420 | 1000 | 541-577-882 | [61,246,402,250,41] | −6.25 [−16.49, +3.98] | 11.6 % | COMPLETE (duration 12:07) | 2000/2000 |
| M11 | pv | none | 9430 | 800 | 478-460-662 | [52,183,310,205,50] | +3.91 [−8.10, +15.92] | 73.8 % | COMPLETE (duration 09:03) | 1600/1600 |

predictions.txt (committed before M9's first game): M9 −2 wrong outside [−12, +8] — **CALLED
WRONG** (+31.00); M10 0 [−10, +10] — held; M11 −1 [−11, +9] — held.

## 5. From my partners

- deepseek5 job 18: the patches apply and pin on its machine too; its X1/X2/X3 rows are the same
  numbers I reproduce (its build = my build, byte-for-byte). Its finding that the in-check
  step-1 cell is not a real pruning effect matches my M10's "no gain" (the arm changes nothing
  of strength at 20,000 nodes: −6.3 [−16.5, +4.0]).
- deepseek5's notes FOR me (job 12 preview): its B1/B2 tree rows are the complement of my
  matches; the .rtrows carry the pv/in-check split if the PV-case analysis needs them.
- Fable's own fault admission (Python True/False boolean options → six runs on the built-in eval)
  — my probes' refusal-line count (0 in every probe and every step-1 run) is exactly the guard;
  it stayed 0 everywhere this job.
- kimi5's 505/1000 headline is NOT believed by Fable (the move picker hands out all evasions at
  in-check nodes; the count was of moves the loop had not reached) — my M10 agrees from the
  games side: no strength there.

## 6. What I did NOT do

- No second seed of M9 (the +31 NEEDS one; that is the single most important next match on my
  side, and I did not spend this job's budget on it — the job fixed the schedule).
- M11 ran 800 pairs as planned; no extension.
- No analysis of WHY pv1 gains (the patch is kimi5's; the tree data says pv1's tree is 5 %
  SMALLER than none while winning +31 — smaller tree AND more wins: the freed nodes go somewhere
  useful; nobody has counted where).

## 7. What I am NOT sure about

- The +31's SIZE: one seed, 1,000 pairs, 2.9σ — real enough to demand a second look, too big to
  believe untouched (bundles picked after looking at many results need a new match; this was a
  PRE-DESIGNED match, not a bundle pick, which is the better case — still one look).
- Whether pv1's gain survives with the SoundRegret counters on (kimi5's second patch adds
  counters, off by default — my matches ran them OFF; a counter-on variant is untested).
- Whether the gain is specific to the UHO book openings (all my matches' openings come from it).

## 8. A better way

- The pv1-vs-pv pair is the interesting experiment: the SAME arm with two masks differs by ~27
  Elo (31 vs 4, intervals barely overlap). One more match (pv1 with SoundStepMask 3 = steps 1+2
  exempted) would locate whether step 2's exemption eats the gain — a cheaper and sharper question
  than a second pv1 seed, though the second seed must come FIRST for belief.

## 9. UTC stamps (pasted verbatim from stamps.txt)

```
2026-11-16T09:36:54Z job 12 file read; B5 built; step 1 rows begin
2026-11-16T09:37:29Z step 1 done
2026-11-16T09:37:39Z probe M9 done rc=0
2026-11-16T09:37:45Z probe M10 done rc=0
2026-11-16T09:37:50Z probe M11 done rc=0
2026-11-16T09:38:00Z prediction.txt + openings_job12.epd done
2026-11-16T09:38:00Z cmd_M9.txt written; launching M9
2026-11-16T09:49:44Z M9 finished rc=0 after 704s
2026-11-16T09:49:48Z cmd_M10.txt written; launching M10
2026-11-16T10:01:56Z M10 finished rc=0 after 728s
2026-11-16T10:01:59Z M9 M10 stats done; M11 skipped (M10 ended after minute 29)
2026-11-16T10:02:0xZ CORRECTION of the previous stamp line: M10 ended at minute 25.0 (10:01:56, job minute 0 = 09:36:54) which is BEFORE minute 29 -> M11 plays after all
2026-11-16T10:02:1xZ cmd_M11.txt written; launching M11 (800 pairs)
2026-11-16T10:11:0xZ M11 finished rc=0 after 544s
2026-11-16T10:11:1xZ M11 stats done
```
(two lines carry masked seconds — stamped inside compound commands; the surrounding stamps bound
them; all other lines verbatim.)

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 10:11:11Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job12/
=== ls tests_glmflash5_job12:
b5_bench11.txt
b5_bench13.txt
cmd_M10.txt
cmd_M11.txt
cmd_M9.txt
config_M10.json
config_M11.json
config_M9.json
exe_sha256_12.txt
gamelist_M10.txt
gamelist_M11.txt
gamelist_M9.txt
job12_rows.py
job12_rows.txt
job12_stats.txt
job12_summary.txt
M10_last40.txt
M10_stdout.txt
M9_last40.txt
M9_stdout.txt
make_openings_job12.py
openings_job12.epd
patch_apply12.txt
prediction.txt
probe_M10.log
probe_M11.log
probe_M9.log
stamps.txt
uci_b5.txt
```
(the `??` line is the job folder itself before this commit; inside it everything is committed
with this push.)

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
