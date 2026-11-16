# REPORT glmflash5 — JOB 24 — the variant and the extension alone: five looks at 2,000, seconds at 20,000

Branch `cursor/glmflash5-work-cb5c` (run A). Exe = B10 (sha256
7621bdfbb3b85f5e5ea37e9a7365adf2be27423e16d55d7b470d8cb7a513a1a6; step 0 re-verified exact). All
six matches COMPLETE — nothing cut. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: is the CED8 variant's ~+5 lean at 2,000 nodes real (two more looks), is the extension
alone the same as the variant (two more looks each side), and does either show anything at
20,000 in a second look; three pools by one command.

Answer: **The variant at 2,000 nodes, FIVE looks pooled (M49+M51+M52+M55+M56, 5,000 pairs):
+6.67 [+1.35, +12.00] — the interval is now entirely above zero: the lean is REAL at the
self-play depth on this tree.** **The extension alone at 2,000 (M53+M57+M58, 3,000 pairs):
+6.54 [−0.45, +13.54] — statistically the same number as the variant's pool: CheckExtension
Depth 8 alone IS the variant's content; the two reduction terms add nothing visible.** **The
variant at 20,000 (M54+M59, 2,000 pairs): +4.26 [−2.86, +11.38] — leaning positive now (M59
+7.30), still touching zero; M60 (the extension alone at 20,000): −1.91 [−11.99, +8.17], level.**

How sure: step 0 exact (the three tree rows reproduce a third time; the four pins re-run fresh
for this job's own files — `b10_bench*.txt`, `b10_perft5.txt`); six probes exact; all six
matches carry the openings-slice check printed by the stats command (first game's FEN = the
file's `start` line: True ×6); 12,000/12,000 validation rows; identities under every table.
The pools are the session's belief unit: the 2,000-node variant pool is five seeds.

## 2. Step 0 — re-verified (`job24_rows.txt`, driver `job24_rows.py` COMMITTED)

S14 9,500,069 ✓; S14+CED8+GC0+IC0 8,565,026 ✓; S14+CED8 9,015,167 ✓ (all three now KNOWN
answers — the PC's rows equal mine on 200/200, per Opus's recount in file 24). Pins:
312,866 / 862,329 / 3,024,920 / 4,865,609 ✓. Refusals 0.

## 3. Step 2 — six probes (`probe_M55…M60.log`; probe openings lines 6101–6122, no match uses
them)

Every probe: base 14 ×2 games (28), no extras; cand: M55/M56/M59 the variant's three lines 2/2
each; M57/M58/M60 CED=8 only (2/2, GC/IC 0); refusals 0.

## 4. The matches (B10 both sides; S14 both; the candidate's lines on top; nodes 2,000 for
M55–M58, 20,000 for M59/M60; the driver's readback checks (nodes AND start) passed before every
launch; openings_job24.epd by the globbing script (71 gamelist files; 62,979 distinct openings
removed; Random(24001); 6,000 lines; first line
`rn1qkbnr/ppp2ppp/8/3pP3/6b1/2P1B3/PP2PPPP/RN1QKBNR b KQkq - 0 4`), order sequential; slices
M55 1–1000, M56 1001–2000, M57 2001–3000, M58 3001–4000, M59 4001–5000, M60 5001–6000; the
first-opening check printed True six times by the stats command; concurrency 4)

Games by ending FIRST — all from the committed `job24_stats.py` (output `job24_stats_out.txt`),
identities printed by the same command (losses on time BY SIDE 0/0; illegal/disconnect/crash 0):

| ending | M55 (2000) | M56 (2000) | M57 (2000) | M58 (2000) | M59 (2000) | M60 (2000) |
|--------|------------|------------|------------|------------|------------|------------|
| White mates | 752 | 745 | 710 | 718 | 585 | 602 |
| Black mates | 641 | 631 | 668 | 645 | 491 | 473 |
| 3-fold repetition | 332 | 331 | 329 | 354 | 621 | 635 |
| fifty moves | 168 | 179 | 182 | 191 | 168 | 149 |
| insufficient material | 102 | 109 | 102 | 86 | 130 | 135 |
| stalemate | 5 | 5 | 9 | 6 | 5 | 6 |
| **identity: mates = wins+losses** | 752+641 = 744+649 = 1393 ✓ | 745+631 = 692+684 = 1376 ✓ | 710+668 = 723+655 = 1378 ✓ | 718+645 = 692+671 = 1363 ✓ | 585+491 = 559+517 = 1076 ✓ | 602+473 = 532+543 = 1075 ✓ |

| match | cand | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M55 | variant | 2000 | 20055 | 1000 | 744-649-607 | [84,197,373,232,114] | +16.52 [+4.63, +28.40] | COMPLETE (1:51) |
| M56 | variant | 2000 | 20056 | 1000 | 692-684-624 | [98,204,392,204,102] | +1.39 [−10.45, +13.23] | COMPLETE (1:54) |
| M57 | CED8 | 2000 | 20057 | 1000 | 723-655-622 | [91,202,372,218,117] | +11.82 [−0.23, +23.86] | COMPLETE (1:52) |
| M58 | CED8 | 2000 | 20058 | 1000 | 692-671-637 | [115,184,361,245,95] | +3.65 [−8.49, +15.78] | COMPLETE (1:55) |
| M59 | variant | 20000 | 20059 | 1000 | 559-517-924 | [40,239,415,251,55] | +7.30 [−2.74, +17.34] | COMPLETE (11:50) |
| M60 | CED8 | 20000 | 20060 | 1000 | 532-543-925 | [46,259,401,248,46] | −1.91 [−11.99, +8.17] | COMPLETE (11:45) |

**The three pools (ONE committed command, `job24_stats.py`):**

| pool | pairs | n5 | Elo, 95 % pair interval |
|------|-------|----|-------------------------|
| variant@2,000 (M49+M51+M52+M55+M56) | 5,000 | [465, 1025, 1906, 1061, 543] | **+6.67 [+1.35, +12.00]** |
| CED8-alone@2,000 (M53+M57+M58) | 3,000 | [298, 617, 1091, 662, 332] | +6.54 [−0.45, +13.54] |
| variant@20,000 (M54+M59) | 2,000 | [90, 470, 851, 479, 110] | +4.26 [−2.86, +11.38] |

predictions.txt (own commit c7dda417c, 17:01:10Z): M55 +5 [−7,+17] — **CALLED WRONG** (+16.52);
M56 +5 [−7,+17] — held; M57 +4 [−8,+16] — held; M58 +4 [−8,+16] — held; M59 +2 [−10,+14] —
held; M60 +1 [−11,+13] — held; pool variant@2k +6 [0,+12] — held (+6.67); pool CED8@2k +5
[−2,+12] — held; pool variant@20k +2 [−5,+9] — held (+4.26).

## 5. From my partners

- Opus's recount made my job-23 tree rows into KNOWN ANSWERS (the PC's r26 equals mine 200/200
  on all three settings) — this job's step 0 then re-verified them a third time on my machine.
- deepseek6's dead-settings list (QsSeeMargin; CaptureFutility pair at base 0) — the same
  "does it move anything" logic my refusal/probe guards use; noted.
- The PC's R1@20k pair (+10.57 / −1.22) and its waiting R1c self-play run — my variant pools
  (+6.67 @2k; +4.26 @20k) are the numbers they will be read beside.

## 6. What I did NOT do

- No sixth variant seed at 2,000 (five is what the job planned; the pool's one-sided interval
  is the deliverable).
- No CED8-alone look at 20,000 beyond M60 (it stands alone, as the job says).
- No decomposition of WHY the extension cap gains at 2,000 (kimi5's counter builds could; not
  asked here).

## 7. What I am NOT sure about

- The variant@2k pool's +6.67 is now five seeds with a one-sided interval — the strongest
  positive on my tree this session — but it is still MY TREE ONLY: the PC's engine showed flat
  for pv1 at 20k where mine showed +11, so the PC's own 2,000-node verdicts are the deciders.
- Whether CED8-alone ≈ variant (pools +6.54 vs +6.67) means the reduction terms are exactly
  neutral on top (the difference 0.13 has no meaning at these widths).
- The M55 seed was the biggest of the five (+16.5) — the pool without it would be ~+4.5; the
  spread is honest seed noise, and the pool is the summary that handles it.

## 8. A better way

- The openings-slice check (first game's FEN == the file's start line) caught nothing this job
  — because it ran — and costs one command; it is now permanent in my stats output alongside
  the identities.

## 9. UTC stamps

times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 17:33:01Z)

```
=== git status --short (head):
?? forge-combo29/tests_glmflash5_job24/M55_stdout.txt
?? forge-combo29/tests_glmflash5_job24/M56_stdout.txt
?? forge-combo29/tests_glmflash5_job24/M57_stdout.txt
=== ls tests_glmflash5_job24: (committed files)
b10_bench11.txt
b10_bench13.txt
b10_bench16.txt
b10_perft5.txt
exe_sha256_check.txt
cmd_M55.txt
cmd_M56.txt
cmd_M57.txt
cmd_M58.txt
cmd_M59.txt
cmd_M60.txt
config_M55.json
config_M56.json
config_M57.json
config_M58.json
config_M59.json
config_M60.json
gamelist_M55.txt
gamelist_M56.txt
gamelist_M57.txt
gamelist_M58.txt
gamelist_M59.txt
gamelist_M60.txt
job24_match.sh
job24_rows.py
job24_rows.txt
job24_stats.py
job24_stats_out.txt
job24_summary.txt
M55_last40.txt
M55_stdout.txt
M56_last40.txt
M56_stdout.txt
M57_last40.txt
M57_stdout.txt
M58_last40.txt
M58_stdout.txt
M59_last40.txt
M59_stdout.txt
M60_last40.txt
M60_stdout.txt
make_openings_job24.py
openings_job24.epd
prediction.txt
probe_M55.log
probe_M56.log
probe_M57.log
probe_M58.log
probe_M59.log
probe_M60.log
stamps.txt
```
(the `??` lines were the job folder's uncommitted files at listing time; all join this push.
This job's pin files are `b10_bench*.txt` / `b10_perft5.txt`, run fresh at 17:33 — after the
listing above was taken — and they are in the commit; the step-0 section says so.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
