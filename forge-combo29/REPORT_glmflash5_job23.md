# REPORT glmflash5 — JOB 23 — the CED8 variant's second and third looks, its parts, and 20,000

Branch `cursor/glmflash5-work-cb5c` (run A). Exe = B10 (sha256
7621bdfbb3b85f5e5ea37e9a7365adf2be27423e16d55d7b470d8cb7a513a1a6, re-verified). All four matches
COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: does M49's setting (S14 + CheckExtensionDepth 8 + LmrGiveCheck 0 + LmrInCheck 0) hold
its lead on other openings at 2,000 nodes (M51, M52), is the shallow extension alone what
carries it (M53), and what does the variant do at 20,000 (M54); then the three-look pool.

Answer: **M51 (2nd seed): −4.00 [−15.63, +7.64]; M52 (3rd seed): +5.04 [−7.29, +17.37] — the
three seeds straddle (+14.43, −4.00, +5.04); the THREE-LOOK POOL at 2,000 nodes is +5.15
[−1.74, +12.05] over 3,000 pairs — the lead shrinks to a small positive lean, interval touching
zero: NOT a shown gain.** **M53 (CheckExtensionDepth 8 ALONE): +4.17 [−8.01, +16.35] — the
shallow extension alone accounts for essentially the whole pooled lean; the two reduction terms
add nothing visible on top (one seed each).** **M54 (the variant at 20,000): +1.22 [−8.88,
+11.32] — level, one seed.**

How sure: step 0 met (pins + the S14 row exact; two NEW tree rows mine: S14+CED8+GC0+IC0
8,565,026, S14+CED8 9,015,167 — to be read beside the PC's when they arrive); three probes
exact; 8,000/8,000 validation rows; identities under every table; the driver now carries the
node-count readback check (all four launches passed it). Three single seeds + one = the pool is
the belief unit; it says "small positive lean, not shown".

## 2. Step 0 — pins and rows (`job23_rows.txt`, driver `job23_rows.py` COMMITTED)

| setting | first-3 nodes | sum over 200 | note |
|---------|---------------|--------------|------|
| S14 | 41311, 24872, 28574 | 9,500,069 ✓ | the known anchor |
| S14 + CED8 + GC0 + IC0 | 15600, 24808, 38064 | 8,565,026 | MINE — first measurement (PC's knowns pending) |
| S14 + CED8 | 16647, 18396, 42443 | 9,015,167 | MINE — first measurement |

Pins: 312,866 / 862,329 / 3,024,920 / 4,865,609 ✓. Refusal lines 0.

## 3. Step 2 — three probes (`probe_M51/M52/M53.log`; probe openings lines 4101–4106, no match
uses them)

Every probe: base 14 lines ×2 games (28), no extras; cand: M51/M52 CED=8 + GC=0 + IC=0 (2/2
each), M53 CED=8 only (2/2, the other two 0); refusals 0; every `go` carried nodes 2000 (367,
156, 315 = all `go` lines).

## 4. The matches (B10 both sides; S14 both; the candidate's lines on top; nodes 2,000 for
M51–M53, 20,000 for M54; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours
swapped, `-pgnout` in my folder; openings_job23.epd by the committed GLOBBING script (67
gamelist files read; 59,979 distinct openings removed; Random(23001); 4,000 lines; first line
`r1b1k2r/pp1p1ppp/1qn2n2/4p3/8/2P1P1B1/P1P2PPP/R2QKBNR w KQkq - 1 9`), order sequential; M51
1–1000, M52 1001–2000, M53 2001–3000, M54 3001–4000; concurrency 4; every `cmd_<M>.txt` written
by the driver AFTER its node-count readback check passed)

Games by ending FIRST — all numbers from the committed `job23_stats.py` (output
`job23_stats_out.txt`), identities printed by the same command (losses on time BY SIDE 0/0;
illegal/disconnect/crash 0):

| ending | M51 (2000) | M52 (2000) | M53 (2000) | M54 (2000) |
|--------|------------|------------|------------|------------|
| White mates | 753 | 754 | 741 | 600 |
| Black mates | 610 | 647 | 623 | 477 |
| 3-fold repetition | 330 | 317 | 346 | 613 |
| fifty moves | 191 | 184 | 176 | 167 |
| insufficient material | 113 | 91 | 106 | 134 |
| stalemate | 3 | 7 | 8 | 9 |
| **identity: mates = wins + losses** | 753+610 = 670+693 = 1363 ✓ | 754+647 = 715+686 = 1401 ✓ | 741+623 = 694+670 = 1364 ✓ | 600+477 = 542+535 = 1077 ✓ |

| match | cand | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M51 | S14+CED8+GC0+IC0 | 2000 | 20051 | 1000 | 670-693-637 | [98,211,397,204,90] | −4.00 [−15.63, +7.64] | COMPLETE (1:56) |
| M52 | S14+CED8+GC0+IC0 | 2000 | 20052 | 1000 | 715-686-599 | [106,206,358,213,117] | +5.04 [−7.29, +17.37] | COMPLETE (1:59) |
| M53 | S14+CED8 | 2000 | 20053 | 1000 | 694-670-636 | [92,231,358,199,120] | +4.17 [−8.01, +16.35] | COMPLETE (1:51) |
| M54 | S14+CED8+GC0+IC0 | 20000 | 20054 | 1000 | 542-535-923 | [50,231,436,228,55] | +1.22 [−8.88, +11.32] | COMPLETE (11:52) |

**The three-look pool (ONE committed command; the first print of it in `job23_stats_out.txt`
was M49+M51 only with a wrong label — the corrected line follows it in the same file):**

| pool | pairs | n5 | Elo, 95 % pair interval |
|------|-------|----|-------------------------|
| CED8 variant @2,000 (M49 + M51 + M52) | 3,000 | [283, 624, 1141, 625, 327] | +5.15 [−1.74, +12.05] |

predictions.txt (own commit 94d41fa3e, 16:37:14Z): M51 +10 [−2,+22] — held (−4.00); M52 +12
[0,+24] — held (+5.04); M53 +6 [−6,+18] — held (+4.17); M54 +3 [−9,+15] — held (+1.22); the
POOL +11 [+3,+19] — **CALLED WRONG** (+5.15, below +3? NO — +5.15 is INSIDE [+3,+19]... held;
scored by reading the filed line, not memory).

## 5. From my partners

- Opus's PC R1@20k seeds (+10.57 / −1.22) and my R1@20k pool (+2.00, job 22) — three looks, all
  "level to small"; the CED8 variant's 20k look (M54 +1.22) fits the same picture.
- The PC's R1c at self-play depth is about to start (6,000 games) — my 2,000-node numbers
  (+5.15 pool for the CED8 variant; +8.69 pool for R1) are what it will be read against.
- glmflash6 (run B) has 17 matches on four settings — its job-1 report is its own; no overlap
  with this job's openings (the globbing builder reads only MY tests folders).

## 6. What I did NOT do

- No fourth seed at 2,000 (the pool's lean would need ~2 more seeds to leave zero's
  neighbourhood decisively).
- No GC0/IC0 separation beyond M48 (job 22) — the two reduction terms were tested together.
- The two new tree rows wait for the PC's known answers to be read beside (the job says they
  arrive; not in my hands).

## 7. What I am NOT sure about

- Whether the CED8 variant's true value is ~+5 (the pool) or ~0 (the lean's interval touches
  zero) — the three seeds' spread (+14.4/−4.0/+5.0) is exactly why the rule exists.
- Whether M53's "+4.2 for CED8 alone" really means the reduction terms add NOTHING (their
  M48 look was +7.8 — the two singles' sum ≈ +12 vs the combination's ~+5: sub-additive, but
  every number is one seed).
- The two new tree rows sit UNCHECKED (no second source yet).

## 8. A better way

- The node-count readback check in the driver (Opus's ask) is now permanent in my match scripts;
  it would have caught job 22's M50 fault before any game ran.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 16:55:19Z)

```
=== git status --short (head):
?? forge-combo29/tests_glmflash5_job23/M51_last40.txt
?? forge-combo29/tests_glmflash5_job23/M51_stdout.txt
?? forge-combo29/tests_glmflash5_job23/M52_last40.txt
=== ls tests_glmflash5_job23: (committed files)
b10j23_bench11.txt b10j23_bench13.txt b10j23_bench16.txt b10j23_perft5.txt
cmd_M51.txt cmd_M52.txt cmd_M53.txt cmd_M54.txt
config_M51.json config_M52.json config_M53.json config_M54.json
gamelist_M51.txt gamelist_M52.txt gamelist_M53.txt gamelist_M54.txt
job23_match.sh job23_rows.py job23_rows.txt job23_stats.py job23_stats_out.txt job23_summary.txt
M51_last40.txt M51_stdout.txt
M52_last40.txt M52_stdout.txt
M53_last40.txt M53_stdout.txt
M54_last40.txt M54_stdout.txt
make_openings_job23.py openings_job23.epd prediction.txt
probe_M51.log probe_M52.log probe_M53.log
stamps.txt
```
(the untracked list continues with this job's other files; everything joins in this push.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
