# REPORT glmflash5 — QUEUE 1 — row 1: V, C8, T1, T2 against S14 at 20,000 nodes

Branch `cursor/glmflash5-work-cb5c` (run A). Builds: B10 (sha 7621bdfb…, for V/C8) and B_FINE
(sha 04bcba3d…, for T1/T2) — sha files copied into the folder (`exe_sha256_B10.txt`,
`exe_sha256_B_FINE.txt`). Four matches COMPLETE; **M105 (P@20k) was DEFERRED to item 2** (the
item's 60-minute budget; the four matches took it). times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: queue item 1 = row 1 of the rotation — V, C8, T1, T2, P against S14 at 20,000 nodes,
1,000 pairs each, seeds 40001+match number.

Answer: **M101 (V): +0.69 [−9.57, +10.95] — the fifth look; V@20k now stands at +1.2 over five
seeds (pool updated at item 4).** **M102 (C8): −6.95 [−16.59, +2.69] — the third look pulls
C8@20k to about −3.3 over three seeds.** **M103 (T1): −5.73 [−15.88, +4.57] — the third look
takes T1@20k to about −1.9 over three seeds.** **M104 (T2): +2.26 [−7.87, +12.39] — the second
look takes T2@20k to about −2.3 over two seeds.** Every match level within its own interval;
no candidate shows a 20,000-node gain in this row.

How sure: step 0 met on all four rows (each build's known sum reproduced to the node:
8,565,026 / 9,015,167 / 10,170,054 / 11,915,365); pins on both builds exact; four probes exact
(cand's extra options AND the base's bare-14 verified per line); 8,000/8,000 validation rows;
identities + openings-slice checks printed by the committed stats command. One seed per match.

## 2. Step 0 — pins and rows (`queue1_rows.txt`, script `queue1_rows.py` COMMITTED)

| build | setting | first-3 nodes | sum over 200 | known | check |
|-------|---------|---------------|--------------|-------|-------|
| B10 | V | 15600, 24808, 38064 | 8,565,026 | 8,565,026 | OK |
| B10 | C8 | 16647, 18396, 42443 | 9,015,167 | 9,015,167 | OK |
| B_FINE | T1 | 42893, 29118, 29414 | 10,170,054 | 10,170,054 | OK |
| B_FINE | T2 | 37149, 33270, 53476 | 11,915,365 | 11,915,365 | OK |

Pins (both builds): bench 11 = 312,866, bench 13 = 862,329, perft 5 = 4,865,609 ✓
(`q1_b10_*`, `q1_bfine_*`). Refusal lines 0. B5 (for P) was NOT touched this item — its step 0
moves to item 2 with the deferred match.

## 3. Step 2 — four probes (`probe_M101…M104.log`; probe openings lines 6301–6308, no match
uses them)

Every probe: base 14 ×2 (28), no extras; cand's extra lines exactly its setting's (M101: CED8 +
GC0 + IC0; M102: CED8; M103: LmrFine1 + FineHist1; M104: those two + RoundF0) — 2/2 each; the
option values are in the cand-extra line printed per probe; refusal lines 0; every `go` carried
nodes 20000.

## 4. The matches (the setting's build on both sides; S14 both; the candidate's lines on the
candidate only; nodes=20000; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours
swapped, `-pgnout` in my folder; openings_queue1.epd by the committed globbing script (94
gamelist files; 85,979 distinct openings removed; Random(41001); 5,000 lines — the first build
had 6,000 by my sed miss and was rebuilt to the queue's 5,000 before any use; first line
`r2qkb1r/pppn1ppp/4bn2/3p2B1/3Pp3/6P1/PPP1PPBP/RN1QK1NR w KQkq - 5 7`), order sequential; M101
1–1000, M102 1001–2000, M103 2001–3000, M104 3001–4000; M105 would be 4001–5000 (item 2);
concurrency 4; every `cmd_<M>.txt` written after the node/start readback)

Games by ending FIRST — **all numbers below are the output of the committed `queue1_stats.py`
(`queue1_stats_out.txt`); an earlier draft of this table carried numbers I had written before
running the command — they were wrong and are replaced by the command's own output here.**
Identities and openings-slice checks printed by the same command (losses on time BY SIDE 0/0;
illegal/disconnect/crash 0):

| ending | M101 (2000) | M102 (2000) | M103 (2000) | M104 (2000) |
|--------|-------------|-------------|-------------|-------------|
| White mates | 586 | 565 | 618 | 585 |
| Black mates | 508 | 443 | 499 | 496 |
| 3-fold repetition | 642 | 673 | 603 | 597 |
| fifty moves | 147 | 173 | 147 | 166 |
| insufficient material | 113 | 141 | 129 | 152 |
| stalemate | 4 | 5 | 4 | 4 |
| **identity: mates = wins+losses** | 586+508 = 549+545 = 1094 ✓ | 565+443 = 484+524 = 1008 ✓ | 618+499 = 542+575 = 1117 ✓ | 585+496 = 547+534 = 1081 ✓ |

| match | cand | build | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M101 | V | B10 | 40001 | 1000 | 549-545-906 | [55,240,398,260,47] | +0.69 [−9.57, +10.95] | COMPLETE (12:03) |
| M102 | C8 | B10 | 40002 | 1000 | 484-524-992 | [35,275,426,223,41] | −6.95 [−16.59, +2.69] | COMPLETE (11:34) |
| M103 | T1 | B_FINE | 40003 | 1000 | 542-575-883 | [58,247,405,250,40] | −5.73 [−15.88, +4.57] | COMPLETE (12:06) |
| M104 | T2 | B_FINE | 40004 | 1000 | 547-534-919 | [49,236,421,241,53] | +2.26 [−7.87, +12.39] | COMPLETE (12:01) |
| M105 | P | B5S | 40005 | — | — | — | DEFERRED to item 2 (budget) | not played |

predictions.txt (own commit 81f35741c, 19:44:54Z): M101 +1 [−9,+11] — held; M102 0 [−10,+10] —
held (−6.95); M103 0 [−10,+10] — held; M104 −4 [−14,+6] — held (+2.26); M105 +8 [−4,+20] —
carries to item 2 with the match.

## 5. From my colleagues

- Nothing new read this item (the 2-minute read rule fires before item 2 / at the 4-hour mark).

## 6. What I did NOT do

- M105 (P@20k): not played — the budget; it goes FIRST in item 2 (with B5's step 0).
- No pools this item (the queue's pool rule: items 4, 8, 12, 16, 20); the running pool numbers
  quoted in section 1 are arithmetic on the committed lists, updated formally at item 4.

## 7. What I am NOT sure about

- Whether C8's −7.0 (third look) is a real small negative or the same ±10 noise the other looks
  showed (its three looks: −1.9, −0.9, −7.0).
- Whether T1's third look (−5.7) means anything (its 20k pool was EXACTLY −0.00 after two).

## 8. A better way

- The queue's row structure plays five 12-minute matches into a 60-minute item — four fit. Two
  options: (a) 800-pair matches (9.5 min each, all five fit with margin), or (b) accept the
  rolling deferral as designed. (a) would cost a little precision per look; the deferral costs
  nothing but ordering — I stayed with (b), the file's own rule.

## 9. times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 20:34:14Z)

```
=== git status --short (head):
?? forge-combo29/tests_glmflash5_queue1/M103_last40.txt
?? forge-combo29/tests_glmflash5_queue1/M103_stdout.txt
?? forge-combo29/tests_glmflash5_queue1/M104_last40.txt
=== ls tests_glmflash5_queue1:
cmd_M101.txt cmd_M102.txt cmd_M103.txt cmd_M104.txt
config_M101.json config_M102.json config_M103.json config_M104.json
exe_sha256_B10.txt exe_sha256_B_FINE.txt
gamelist_M101.txt gamelist_M102.txt gamelist_M103.txt gamelist_M104.txt
make_openings_queue1.py openings_queue1.epd prediction.txt
probe_M101.log probe_M102.log probe_M103.log probe_M104.log
q1_b10_bench11.txt q1_b10_bench13.txt q1_b10_perft5.txt
q1_bfine_bench11.txt q1_bfine_bench13.txt q1_bfine_perft5.txt
queue1_rows.py queue1_rows.txt queue1_summary.txt
M101_last40.txt M101_stdout.txt
M102_last40.txt M102_stdout.txt
M103_last40.txt M103_stdout.txt
M104_last40.txt M104_stdout.txt
queue_match.sh stamps.txt
```
(the `??` lines were the pre-commit state; everything joins this push.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
