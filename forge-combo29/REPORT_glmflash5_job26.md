# REPORT glmflash5 — JOB 26 — kimi5's LmrFine (finer late-move reductions): T1 and T2 by games

Branch `cursor/glmflash5-work-cb5c` (run A). B_FINE = a clean copy of 6b98f217 + kimi5's
`tests_kimi5_job11/LmrFine.patch.txt` (75 lines; sha256 verified BEFORE use:
f7bf3f4363220440dfdd3419805f14cd90a094ad1cc296bd00d9b9911d0406c0 — starts with the required
`f7bf3f43`); applied with `patch -p1` (dry-run then real, both rc=0, outputs committed); built
as B10 is. B_FINE sha256 04bcba3ddcc97501bdd524a686f785041f7b8ec22dd131be319f69bcabb05720. All
six matches COMPLETE — nothing cut. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: the first matches of the LmrFine patch — T1 (LmrFine 1 + LmrFineHistory 1, the fine
reductions with the history term) and T2 (T1 + LmrRoundF 0, round-down) against plain S14, at
2,000 and 20,000 nodes.

Answer: **T1 is LEVEL at both depths: at 2,000 the two seeds straddle (M67 −4.52 [−16.72,
+7.69]; M68 +5.04 [−6.81, +16.89]) and the pool is +0.26 [−8.25, +8.77]; at 20,000 the pool is
EXACTLY zero: −0.00 [−7.02, +7.02] (M70 −1.56, M71 +1.56).** **T2 LOSES at both depths: M69
(2k) −13.03 [−25.04, −1.03] — one-sided DOWN; M72 (20k) −6.95 [−17.43, +3.53] — level-to-
negative. The 25 % larger tree of round-down buys nothing and the depth give-back shows.**

One sentence: **the fine-reduction path with the history term neither wins nor loses at either
node count (four seeds, two pools at ±8 and ±7); turning its rounding to round-down costs about
13 at 2,000 nodes (one-sided) and leans negative at 20,000 — on this tree, kimi5's defaults
(LmrFine 0, round-to-nearest) stay the right choice.**

How sure: step 0 fully met (the four sums exact — the fine-path IDENTITY row reproduced the
anchor to the node, and T1/T2 equal kimi5's numbers exactly); six probes exact after I repaired
my probe function (the first T1 probe run sent only `LmrFine 1` — my T1 branch had dropped the
FineHistory token; found by reading the probe log's own setoption list, rerun, the void logs
overwritten); 12,000/12,000 validation rows; identities + openings-slice checks (True ×6)
printed by the committed `job26_stats.py`. Six single seeds; the pools are two-seed each.

## 2. Step 0 — patch, pins, four rows (`job26_rows.txt`, driver `job26_rows.py` COMMITTED)

| setting | first-3 nodes | known | sum over 200 | known |
|---------|---------------|-------|--------------|-------|
| S14 | 41311, 24872, 28574 | ours+kimi5 ✓ | 9,500,069 | ✓ |
| S14 + LmrFine 1 + LmrFineHistory 0 + LmrRoundF 0 | 41311, 24872, 28574 | THE IDENTITY ✓ | 9,500,069 | ✓ |
| T1 (LmrFine 1 + LmrFineHistory 1) | 42893, 29118, 29414 | kimi5's ✓ | 10,170,054 | ✓ |
| T2 (T1 + LmrRoundF 0) | 37149, 33270, 53476 | kimi5's ✓ | 11,915,365 | ✓ |

Pins, no option: 312,866 / 862,329 / 4,865,609 ✓; uci: LmrFine (0..1, default 0), LmrFineHistory
(0..1, default 0), LmrRoundF (0..1023, default 512) — all present, count 1 each. Refusal lines 0.

## 3. Step 2 — six probes (`probe_M67…M72.log`; probe openings lines 6101–6122, no match uses
them)

| probe | cand received | base received | refusals | go-limit |
|-------|---------------|---------------|----------|----------|
| M67/M68/M70/M71 (T1) | LmrFine=1 AND LmrFineHistory=1, 2/2 each (after the redo) | its 14 lines ×2 (28), no Lmr* extras | 0 | all `go` carry the match's nodes |
| M69/M72 (T2) | LmrFine=1, LmrFineHistory=1, LmrRoundF=0, 2/2 each | its 14 ×2, no extras | 0 | same |

The redo is stamped (the void first attempt's logs were overwritten by the rerun; the fault and
its fix are in stamps.txt and the notes).

## 4. The matches (B_FINE both sides; S14 both; the candidate's T-lines on top; nodes 2,000 for
M67–M69, 20,000 for M70–M72; Threads 1, Hash 16, OwnBook false, no adjudication, pairs colours
swapped, `-pgnout` in my folder; openings_job26.epd by the committed GLOBBING script (83
gamelist files read; 74,979 distinct openings removed; Random(26001); 6,000 lines; first line
`rnb1kbnr/p3q1pp/2pp1p2/1p2p3/P3P3/1B1P1Q1N/1PP2PPP/RNB1K2R b KQkq - 0 7`), order sequential;
M67 1–1000, M68 1001–2000, M69 2001–3000, M70 3001–4000, M71 4001–5000, M72 5001–6000;
concurrency 4; every `cmd_<M>.txt` written by the driver after its readback check)

Games by ending FIRST — all from the committed `job26_stats.py` (output `job26_stats_out.txt`),
identities and openings-slice checks printed by the same command (losses on time BY SIDE 0/0;
illegal/disconnect/crash 0):

| ending | M67 (2000) | M68 (2000) | M69 (2000) | M70 (2000) | M71 (2000) | M72 (2000) |
|--------|------------|------------|------------|------------|------------|------------|
| White mates | 737 | 737 | 728 | 580 | 594 | 623 |
| Black mates | 663 | 662 | 649 | 485 | 497 | 487 |
| 3-fold repetition | 333 | 326 | 304 | 621 | 578 | 599 |
| fifty moves | 177 | 167 | 196 | 149 | 174 | 152 |
| insufficient material | 85 | 97 | 115 | 158 | 151 | 132 |
| stalemate | 5 | 11 | 8 | 7 | 6 | 7 |
| **identity: mates = wins+losses** | 737+663 = 687+713 = 1400 ✓ | 737+662 = 714+685 = 1399 ✓ | 728+649 = 651+726 = 1377 ✓ | 580+485 = 528+537 = 1065 ✓ | 594+497 = 550+541 = 1091 ✓ | 623+487 = 535+575 = 1110 ✓ |

| match | cand | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|------|-------|-------|----|-------------------------|----------------------|
| M67 | S14+T1 | 2000 | 20067 | 1000 | 687-713-600 | [111,214,373,194,108] | −4.52 [−16.72, +7.69] | COMPLETE (2:02) |
| M68 | S14+T1 | 2000 | 20068 | 1000 | 714-685-601 | [92,211,377,216,104] | +5.04 [−6.81, +16.89] | COMPLETE (2:04) |
| M69 | S14+T2 | 2000 | 20069 | 1000 | 651-726-623 | [119,213,382,196,90] | **−13.03 [−25.04, −1.03]** | COMPLETE (2:04) |
| M70 | S14+T1 | 20000 | 20070 | 1000 | 528-537-935 | [46,252,404,261,37] | −1.56 [−11.47, +8.34] | COMPLETE (12:13) |
| M71 | S14+T1 | 20000 | 20071 | 1000 | 550-541-909 | [45,241,420,248,46] | +1.56 [−8.39, +11.51] | COMPLETE (11:53) |
| M72 | S14+T2 | 20000 | 20072 | 1000 | 535-575-890 | [60,260,394,232,54] | −6.95 [−17.43, +3.53] | COMPLETE (11:41) |

**The two pools (ONE committed command):**

| pool | pairs | n5 | Elo, 95 % pair interval |
|------|-------|----|-------------------------|
| T1@2,000 (M67+M68) | 2,000 | [203, 425, 750, 410, 212] | +0.26 [−8.25, +8.77] |
| T1@20,000 (M70+M71) | 2,000 | [91, 493, 824, 509, 83] | −0.00 [−7.02, +7.02] |

predictions.txt (own commit 0853905eb, 18:20:29Z): M67 −3 [−15,+9] — held; M68 −3 [−15,+9] —
held (+5.04 inside); M69 −12 [−24,0] — held (−13.03); M70 −1 [−11,+9] — held; M71 −1 [−11,+9]
— held; M72 −6 [−18,+6] — held (−6.95); pool T1@2k −3 [−11,+5] — held (+0.26); pool T1@20k −1
[−8,+6] — held (−0.00). All eight filed ranges held (scored by re-reading the file).

## 5. From my colleagues

- Nothing new was read this job beyond file 26's own summary (deepseek6's G-at-depth-14 identity
  work stands; kimi5's patch now has its first games).
- The probe-fault lesson is mine: a probe log's setoption list must be READ, not assumed — the
  missing FineHistory line was visible in one grep and the rerun cost one minute.

## 6. What I did NOT do

- No LmrRoundF values between 0 and 512 (the two extremes only, as the job defined T2).
- No LmrFineHistory-alone setting (the job's rows pair it with LmrFine 1).
- No second seeds beyond the two per setting the job planned.

## 7. What I am NOT sure about

- Whether T1's true value is exactly 0 (both pools straddle; the 20,000 pool's midpoint is 0.00
  to two decimals — as clean a null as this session has produced).
- Whether T2's 2,000-node −13.0 is the round-down cost or partly the 25 % tree's depth give-back
  measured at the wrong budget (a T2-at-equal-nodes-to-S14 match would need a node ladder, not
  asked).
- The M67 probe fault means job 26's probe evidence for T1 exists only from the redo (the void
  logs are gone — overwritten; the fault is documented, not hidden).

## 8. A better way

- The probe function should ECHO the options it is about to send into the stamp line (my redo
  now does: `T=$T extra=[...]` is stamped) — the mismatch becomes visible in the stamp itself,
  not only in a later grep.

## 9. times: see stamps.txt.

## 10. Real output of `git status --short` and `ls` of the folder (verbatim, 19:04:14Z)

```
=== git status --short (head):
 M forge-combo29/tests_glmflash5_job26/stamps.txt
?? forge-combo29/tests_glmflash5_job26/M67_last40.txt
?? forge-combo29/tests_glmflash5_job26/M67_stdout.txt
=== ls tests_glmflash5_job26: (52 files)
bfine_bench11.txt bfine_bench13.txt bfine_perft5.txt
cmd_M67.txt cmd_M68.txt cmd_M69.txt cmd_M70.txt cmd_M71.txt cmd_M72.txt
config_M67.json config_M68.json config_M69.json config_M70.json config_M71.json config_M72.json
gamelist_M67.txt gamelist_M68.txt gamelist_M69.txt gamelist_M70.txt gamelist_M71.txt gamelist_M72.txt
job26_match.sh job26_rows.py job26_rows.txt job26_stats.py job26_stats_out.txt job26_summary.txt
LmrFine.patch.txt
M67_last40.txt M67_stdout.txt
M68_last40.txt M68_stdout.txt
M69_last40.txt M69_stdout.txt
M70_last40.txt M70_stdout.txt
M71_last40.txt M71_stdout.txt
M72_last40.txt M72_stdout.txt
make_openings_job26.py openings_job26.epd prediction.txt
probe_M67.log probe_M68.log probe_M69.log probe_M70.log probe_M71.log probe_M72.log
stamps.txt
```
(the `M`/`??` lines were the pre-commit state; everything joins this push.)

## 11. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
