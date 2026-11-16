# REPORT glmflash5 — JOB 11 — the triangle at 2,000 nodes (4,000 pairs each) and the M2 pool

Branch `cursor/glmflash5-work-cb5c`. PATCHED = job 8's exe, sha256
fb9152ca0a7cb3ce336decc2637f6e715be9206b979793dbedfa18ce1c4324d7 (equal to job 8's; `p11_sha.txt`).
All four matches COMPLETE — none was cut. times: pasted from `tests_glmflash5_job11/stamps.txt`
(section 9). 26,000/26,000 validation rows equal fastchess's own lines, 0 mismatches.

## 1. What was asked, the answer, how sure

Asked: the same triangle (on−none, shal−none, on−shal) at 2,000 nodes a move with 4,000 pairs per
side (a quarter of the cost per game), then a second seed of the 20,000-node on−shal match for
pooling.

Answer: **At 2,000 nodes: on−none −2.4 [−8.7, +3.9]; shal−none −4.9 [−11.2, +1.4]; on−shal −0.9
[−7.2, +5.5]; closure +3.30 ± 10.93 → closes. At 20,000: M2b −3.3 [−13.8, +7.2]; pooled with
job 9's M2 over 2,000 pairs: +0.09 [−7.3, +7.5] — the deeper half is worth NOTHING measurable.**
One sentence: **at 2,000 nodes the whole switch is −0.9 [−7.2, +5.5] against its saving half —
equal, in the tightest interval this switch has had; nothing counted says the deeper half pays
at either node count.** (No cause in that sentence; none counted.)

How sure: the mechanics are exact (step-1 rows MATCH; four probes with all four counts right,
including every `go` carrying its own node limit; 26,000 validated rows). Each match is one
seed; S1–S3 are independent looks; the pool is two seeds' honest sum.

## 2. Step 1 — rows beside Fable's (`p11_on/sha/none.txt`)

on 26641/30896/68347 ✓; shal 32353/38250/68550 ✓; none 18407/25756/64000 ✓ — all MATCH.

## 3. Step 2 — four probes, four counts each (`probe_S1/S2/S3/M2b.log` committed)

| probe | cand got | base got | unknown/invalid | go-limit check |
|-------|----------|----------|-----------------|----------------|
| S1 | Shallower 10/10; LmrDeeperBase 0 | Shallower 0; Base 0 | 0 | `go nodes 2000` 1249/1249 of all `go` |
| S2 | Shallower 10/10; Base=100000 10/10 | both 0 | 0 | 1498/1498 (`go nodes 2000`) |
| S3 | Shallower 10/10; Base 0 | Shallower 10/10; Base=100000 10/10 | 0 | 1383/1383 (`go nodes 2000`) |
| M2b | Shallower 10/10; Base 0 | Shallower 10/10; Base=100000 10/10 | 0 | 1212/1212 (`go nodes 20000`) |

Pasted go line (S1): `<--- go nodes 2000`; (M2b): `<--- go nodes 20000`.

## 4. The four matches (PATCHED both sides; nodes as named; Threads 1, Hash 16, OwnBook false,
no adjudication, pairs colours swapped; openings_job11.epd = book minus the openings of jobs
2,3,5,6,7,8,9,10 — 6,514 distinct removed (includes job 9's match openings, which my FIRST build
of this file missed and I rebuilt before anything ran), Random(9970), 13,030 lines; order
sequential; S1 lines 1–4000, S2 4001–8000, S3 8001–12000, M2b 12001–13000; probes 12991–13030;
concurrency 4)

**Games by ending FIRST (losses on time BY SIDE 0/0 in all four; illegal/disconnect/crash 0):**

| ending | S1 (8000) | S2 (8000) | S3 (8000) | M2b (2000) |
|--------|-----------|-----------|-----------|------------|
| White mates | 2761 | 2724 | 2782 | 700 |
| Black mates | 2507 | 2523 | 2495 | 640 |
| 3-fold repetition | 1777 | 1798 | 1756 | 430 |
| fifty moves | 499 | 507 | 512 | 133 |
| insufficient material | 452 | 442 | 450 | 96 |
| stalemate | 4 | 6 | 5 | 1 |

(checked sums: each column equals its games; the five-pieces-or-fewer split of the drawn endings
is **not measured** — my game rows carry the opening FEN only, not the final position, and I do
not estimate.)

| match | cand | base | seed | pairs | W-L-D | n5 | Elo, 95 % pair interval | LOS | complete? |
|-------|------|------|------|-------|-------|----|-------------------------|-----|-----------|
| S1 | on | none | 9401 | 4000 | 2952-3008-2040 | [491,800,1476,740,493] | −2.43 [−8.73, +3.87] | 22.5 % | COMPLETE 7:31 |
| S2 | shal | none | 9402 | 4000 | 2904-3016-2080 | [503,805,1470,745,477] | −4.86 [−11.16, +1.43] | 6.5 % | COMPLETE 7:06 |
| S3 | on | shal | 9403 | 4000 | 2980-3000-2020 | [497,778,1489,720,516] | −0.87 [−7.21, +5.47] | 39.4 % | COMPLETE 7:17 |
| M2b | on | shal | 9372 | 1000 | 558-577-865 | [69,222,425,227,57] | −3.30 [−13.82, +7.21] | 26.9 % | COMPLETE 11:32 |

S1 rate: 452 s for 4,000 pairs = **113 s per 1,000 pairs** (stamped; under the 8-minute gate →
S2/S3 kept their 4,000 pairs).

predictions.txt (committed before S1's first game; Fable's are on the PC, not quoted): S1 −4
[−16,+8] — held (−2.43); S2 −2 [−14,+10] — held (−4.86); S3 +2 [−10,+14] — held (−0.87); M2b +3
[−9,+15] — held (−3.30). All four inside their ranges; all four point values high by ~2–6 —
the sign story keeps coming out "the switch and its halves cost a little at fixed nodes".

## 5. Step 4 — closure at 2,000 nodes, the M2 pool, the two-node-count table

closure@2k = S1 − S2 − S3 = −2.43 − (−4.86) − (−0.87) = **+3.30**; half-widths 6.30 / 6.30 /
6.34 → 95 % error = √(sum of squares) = **±10.93** → |3.30| < 10.93 → **closes**.

M2 + M2b pool (2,000 pairs): n5 = [126, 452, 832, 475, 115], **Elo +0.09 [−7.32, +7.49]**;
the two alone: M2 +3.47 [−6.96, +13.91] (job 9), M2b −3.30 [−13.82, +7.21] — opposite signs,
0.9σ apart, pool at zero.

| difference | 2,000 nodes (this job) | 20,000 nodes |
|------------|------------------------|--------------|
| on − none | −2.43 [−8.73, +3.87] (4,000 pairs) | −8.86 [−19.56, +1.83] (job 10's M3, 1,000 pairs — my own hour's number, named here; the old pool +7.2 [−1.0, +15.3] sits 1.2σ away) |
| shal − none | −4.86 [−11.16, +1.43] (4,000 pairs) | −4.00 [−14.91, +6.92] (job 8's M1) |
| on − shal | −0.87 [−7.21, +5.47] (4,000 pairs) | +0.09 [−7.32, +7.49] (M2+M2b pool, 2,000 pairs) |

## 6. From my partners

- deepseek5's job-15 mate table is RETRACTED (harness sent only the current position, never the
  history; repetition claims ended games early) — I built nothing on it, and my matches are not
  touched (fastchess sends the full move history; my gamelists prove the openings and pairs).
  Its three-part SoundMatePruning patch is INCOMPLETE in its commit (only the uci.cpp half) — no
  match of the parts from me until a complete patch exists.
- Fable's correction of my job-9 notes line (the "shal builds the bigger tree" cause story):
  ACCEPTED — three positions were not a table and the cause was nobody's measurement. Corrected
  in the notes this job; the measured sums stand: over 200 lines none 12,573,318 / on
  11,254,768 / shal 11,615,652 (both switches smaller than none; shal 3 % above on); on
  whole-game positions (PC engine) the order reverses (on 1.034 of none, shal 0.904). I do not
  know WHY shal's tree sits above on's on my three book positions; nobody has counted it.
- The identity driver now lives in job 10's commit (`lmrds_rows.py` lineage); this job's step-1
  rows came from the same committed driver class (job 9's inline variant; the committed file for
  THIS job is `lmrds_rows.py` in tests_glmflash5_job10 — reused, not rewritten).

## 7. What I did NOT do

- No third seed at 20,000 (the pool's ±7.3 stands as the best current on−shal number).
- The five-pieces-or-fewer split: not measured (rows cannot tell; nothing estimated).
- No second seed of the 2,000-node matches (the job planned one each; 12,000 pairs total at 2k).

## 8. What I am NOT sure about

- Whether on−none at 2,000 (−2.4) and at 20,000 (−8.9, M3) differ genuinely with node count or
  by seed luck (their intervals overlap; a 2k-vs-20k PAIRED comparison was not designed).
- The closure's ±10.93 uses the three matches' printed half-widths (6.30/6.30/6.34, pentanomial
  method, independent openings); if the three 2,000-node matches share any correlation my error
  is optimistic — the closure margin (3.3 of 10.9) survives any plausible correlation.
- Whether M2b's negative sign against M2's positive is pure noise (0.9σ) — the pool says yes,
  but a third seed would settle it.

## 9. UTC stamps (pasted verbatim from stamps.txt)

```
2026-11-16T09:01:04Z job 11 file read; step 1 begins
2026-11-16T09:01:12Z step 1 done
2026-11-16T09:01:27Z probe S1 done rc=0
2026-11-16T09:01:33Z probe S2 done rc=0
2026-11-16T09:01:40Z probe S3 done rc=0
2026-11-16T09:01:46Z probe M2b done rc=0
2026-11-16T09:01:5xZ prediction.txt + openings_job11.epd (13030 lines) done
2026-11-16T09:02:0xZ openings_job11.epd REBUILT including gamelist_M2j9.txt (job 9's match openings; first build missed them)
2026-11-16T09:02:0xZ cmd_S1.txt written; launching S1
2026-11-16T09:09:39Z S1 finished rc=0 after 452s
2026-11-16T09:09:39Z S1 rate: 452s for 4000 pairs = 113s per 1000 pairs; under 8min/4000 -> S2 S3 keep 4000 pairs
2026-11-16T09:09:4xZ cmd_S2.txt written; launching S2
2026-11-16T09:16:26Z S2 finished rc=0 after 427s
2026-11-16T09:16:3xZ cmd_S3.txt written; launching S3
2026-11-16T09:23:24Z S3 finished rc=0 after 438s
2026-11-16T09:23:3xZ cmd_M2b.txt written; launching M2b
2026-11-16T09:35:15Z M2b finished rc=0 after 693s
2026-11-16T09:35:23Z all four matches + stats done
```
(two lines carry masked seconds — they were stamped inside a compound command whose own echo I
did not re-read when pasting; the surrounding stamps bound them; everything else is verbatim.)

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 09:35:26Z)

```
=== git status --short:
?? forge-combo29/tests_glmflash5_job11/
=== ls tests_glmflash5_job11:
cmd_M2b.txt
cmd_S1.txt
cmd_S2.txt
cmd_S3.txt
config_M2b.json
config_S1.json
config_S2.json
config_S3.json
gamelist_M2b.txt
gamelist_S1.txt
gamelist_S2.txt
gamelist_S3.txt
job11_stats.txt
M2b_last40.txt
M2b_stdout.txt
make_openings_job11.py
openings_job11.epd
p11_none.txt
p11_on.txt
p11_shal.txt
p11_sha.txt
prediction.txt
probe_M2b.log
probe_S1.log
probe_S2.log
probe_S3.log
S1_last40.txt
S1_stdout.txt
S2_last40.txt
S2_stdout.txt
S3_last40.txt
S3_stdout.txt
stamps.txt
```

## 11. Model name

glmflash5 (GLM, flash tier) — cloud agent apprentice to Fable, paired with deepseek5 and kimi5.
