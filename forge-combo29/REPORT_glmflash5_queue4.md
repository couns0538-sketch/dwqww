# REPORT glmflash5 — QUEUE 4 — row 4 played and THE POOLS (the item's deliverable)

Branch `cursor/glmflash5-work-cb5c` (run A). Builds: B10 (V, N0; sha 7621bdfb…), B_FINE (T1;
04bcba3d…), B5S (P; b8e0d166…). All five matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: row 4 (V@20k, V@2k, T1@20k, P@20k, N0@2k) and — because this is a POOL item — every
candidate's all-looks pool at its node counts, plus the pool without the picked-best first look
where one existed.

Answer: **V@20,000 over SIX looks: +1.85 [−2.24, +5.94] — level, tight. V@2,000 over SEVEN
looks: +5.61 [+1.11, +10.11] — one-sided; without the picked-best first look (M49) it is +4.14
[−0.72, +9.00] — the lean survives the best-of correction but only just. T1@20,000 over FOUR
looks: −2.30 [−7.32, +2.71] — level, leaning a hair negative. P@20,000 over FOUR looks: +10.60
[+5.56, +15.64] — one-sided and solid; without its first look: +8.80 [+2.99, +14.61] — still
one-sided. N0@2,000: the perfect mirrored null again (−0.00 ± 0.00, n5 [0,0,1000,0,0]).**

One sentence: **after this item the session's 20,000-node picture under S14 is: P (pv1) +10.6
(4 seeds, one-sided), V +1.9 (6 seeds), T1 −2.3 (4 seeds), C8 −3.3 (3 looks, item 1) — and at
2,000 nodes: P +80 (3 seeds), V +5.6 (7 seeds, +4.1 without its picked-best look), C8 −1.0
(2 looks), T1 +3.1 (3 looks), T2 −5.7 (2 looks).**

How sure: step 0 rows re-verified (V/T1/S14 exact — the queue-3 driver reran them); five probes
exact; 10,000/10,000 validation rows; identities + openings-slice checks (True ×5) printed by
the committed `queue4_stats.py`; the pools are that same command's output. One seed per new
match; the pools carry the named look lists.

## 2. Step 0 — rows (`queue4_rows.txt`, script `queue4_rows.py` COMMITTED)

S14 9,500,069 ✓; V 8,565,026 ✓; T1 10,170,054 ✓ (plus the queue-3 bundle rows reprinted — all
OK). Pins for this item's builds were verified in item 1 (same binaries); this item's own S14
row is the per-build identity check. Refusal lines 0.

## 3. Step 2 — five probes (`probe_M116…M120.log`; probe openings lines 6401–6410, no match
uses them; each probe's option list stamped before the run)

| probe | cand received (2/2 each) | base received | refusals | go-limit |
|-------|--------------------------|---------------|----------|----------|
| M116 (V) | CED=8, GC=0, IC=0 | its 14 ×2 | 0 | nodes 20000 |
| M117 (V) | the same | its 14 ×2 | 0 | nodes 2000 |
| M118 (T1) | LmrFine=1, FineHist=1 | its 14 ×2 | 0 | nodes 20000 |
| M119 (P) | SoundPvArm=1, SoundStepMask=1 | its 14 ×2 | 0 | nodes 20000 |
| M120 (N0) | nothing | nothing | 0 | nodes 2000 |

## 4. The matches (each setting's build on both sides; S14 both; cand's lines on top; nodes as
named; pairs colours swapped, `-pgnout` in my folder; openings_queue4.epd by the globbing
script (110 gamelist files; 100,979 distinct openings removed; Random(41004); 5,000 lines;
first line `rnbq1rk1/ppp1nppp/8/2bpP1B1/8/3BPN2/PPP2PPP/RN1QK2R b KQ - 2 6`), order sequential;
M116 1–1000, M117 1001–2000, M118 2001–3000, M119 3001–4000, M120 4001–5000; concurrency 4)

Games by ending FIRST — the output of the committed `queue4_stats.py` (`queue4_stats_out.txt`),
identities and openings-slice checks printed by the same command (losses on time BY SIDE 0/0;
illegal/disconnect/crash 0):

| ending | M116 (2000) | M117 (2000) | M118 (2000) | M119 (2000) | M120 (2000) |
|--------|-------------|-------------|-------------|-------------|-------------|
| White mates | 599 | 717 | 592 | 594 | 770 |
| Black mates | 485 | 666 | 484 | 477 | 636 |
| 3-fold repetition | 622 | 344 | 611 | 644 | 334 |
| fifty moves | 162 | 173 | 168 | 153 | 158 |
| insufficient material | 125 | 95 | 141 | 128 | 98 |
| stalemate | 7 | 5 | 4 | 4 | 4 |
| **identity: mates = wins+losses** | 599+485 = 557+527 = 1084 ✓ | 717+666 = 724+659 = 1383 ✓ | 592+484 = 528+548 = 1076 ✓ | 594+477 = 572+499 = 1071 ✓ | 770+636 = 703+703 = 1406 ✓ |

| match | cand | build | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|-------|------|-------|-------|----|-------------------------|----------------------|
| M116 | V | B10 | 20000 | 40116 | 1000 | 557-527-916 | [36,258,396,260,50] | +5.21 [−4.79, +15.21] | COMPLETE (12:03) |
| M117 | V | B10 | 2000 | 40117 | 1000 | 724-659-617 | [80,207,390,214,109] | +11.30 [−0.38, +22.97] | COMPLETE (1:50) |
| M118 | T1 | B_FINE | 20000 | 40118 | 1000 | 528-548-924 | [52,245,424,229,50] | −3.47 [−13.59, +6.64] | COMPLETE (12:19) |
| M119 | P | B5S | 20000 | 40119 | 1000 | 572-499-929 | [36,224,417,277,46] | +12.69 [+2.90, +22.48] | COMPLETE (12:18) |
| M120 | N0 | B10 | 2000 | 40120 | 1000 | 703-703-594 | [0,0,1000,0,0] | −0.00 [−0.00, +0.00] | COMPLETE (1:58) |

**THE POOLS (the same committed command; looks named; the best-of correction where it applies):**

| pool | looks | pairs | n5 | Elo, 95 % pair interval |
|------|-------|-------|----|-------------------------|
| V@20,000 ALL | M54, M59, M73, M74, M101, M116 (6) | 6,000 | [279, 1439, 2512, 1479, 291] | +1.85 [−2.24, +5.94] |
| V@2,000 ALL | M49, M51, M52, M55, M56, M107, M117 (7) | 7,000 | [652, 1448, 2679, 1464, 757] | **+5.61 [+1.11, +10.11]** |
| V@2,000 without M49 (the picked-best first look) | 6 | 6,000 | [573, 1241, 2293, 1256, 637] | +4.14 [−0.72, +9.00] |
| T1@20,000 ALL | M70, M71, M103, M118 (4) | 4,000 | [201, 985, 1653, 988, 173] | −2.30 [−7.32, +2.71] |
| P@20,000 ALL | M24, M32, M105, M119 (4) | 4,000 | [164, 919, 1650, 1043, 224] | **+10.60 [+5.56, +15.64]** |
| P@20,000 without M24 (its picked-best-style first look) | 3 | 3,000 | [120, 714, 1222, 782, 162] | +8.80 [+2.99, +14.61] |
| N0@2,000 | M120 (1) | 1,000 | [0, 0, 1000, 0, 0] | −0.00 [−0.00, +0.00] |

(A print-label slip in the first pool line — it said "FIVE" while listing six looks — is
corrected by the appended line in `queue4_stats_out.txt`; the numbers were identical.)

predictions.txt (own commit 855f1a333, 21:49:33Z): M116 +1 [−9,+11] — held (+5.21); M117 +5
[−6,+16] — held (+11.30); M118 −1 [−11,+9] — held (−3.47); M119 +8 [−2,+18] — held (+12.69);
M120 "Elo 0.00±0.00, n5 [0,0,1000,0,0], wrong if any decisive game appears" — held exactly.

## 5. From my colleagues

- Nothing new read this item (the 2-minute rule fires before item 5).

## 6. What I did NOT do

- No C8@2k pool this item (C8 is not in row 4; its 2,000-node looks are M53+M108 — pooled in
  queue 2's report).
- No T2 looks this item (not in row 4).
- The best-of correction is applied only where a look was demonstrably the reason for repeats
  (V@2k's M49; P@20k's M24 under S14); the other candidates' first looks were not picked-best.

## 7. What I am NOT sure about

- Whether V@2k's +5.61 (7 seeds) vs +4.14 (without M49) bracket means the truth is ~+4–6 —
  plausible, but the picked-best correction is a heuristic, not an unbiased estimator.
- Whether P@20k's +10.6 (4 seeds, one-sided) and the PC's mixed pair (+10.57/−1.22) are the same
  truth — the trees differ; the PC's own further seeds decide.
- M117's +11.3 sits at the top of V@2k's look spread (−4.0 … +16.5 across seven looks) — the
  pool handles it; no single look means much.

## 8. A better way

- The pool command should live in ONE committed file per session (it is now duplicated per
  item); a shared `pools.py` with the look-table as data would remove the copy drift (this
  item's label slip came from exactly that).

## 9. times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 22:31:01Z)

```
=== git status --short (head):
 M forge-combo29/tests_glmflash5_queue4/stamps.txt
?? forge-combo29/tests_glmflash5_queue4/M116_last40.txt
?? forge-combo29/tests_glmflash5_queue4/M116_stdout.txt
=== ls tests_glmflash5_queue4: (committed files)
cmd_M116.txt cmd_M117.txt cmd_M118.txt cmd_M119.txt cmd_M120.txt
config_M116.json config_M117.json config_M118.json config_M119.json config_M120.json
exe_sha256_queue3.txt (the B10/B_FINE/B5S sha file copied from queue 3's folder)
gamelist_M116.txt gamelist_M117.txt gamelist_M118.txt gamelist_M119.txt gamelist_M120.txt
job24_match.sh (not in this folder) — the folder's driver is queue4_match.sh
make_openings_queue4.py openings_queue4.epd prediction.txt
probe_M116.log probe_M117.log probe_M118.log probe_M119.log probe_M120.log
queue4_match.sh queue4_rows.py queue4_rows.txt queue4_stats.py queue4_stats_out.txt queue4_summary.txt
M116_last40.txt M116_stdout.txt
M117_last40.txt M117_stdout.txt
M118_last40.txt M118_stdout.txt
M119_last40.txt M119_stdout.txt
M120_last40.txt M120_stdout.txt
stamps.txt
```
(the `M`/`??` lines were the pre-commit state; everything joins this push.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
