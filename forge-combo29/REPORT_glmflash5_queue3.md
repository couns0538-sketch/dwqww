# REPORT glmflash5 — QUEUE 3 — the two bundle builds (VT, VP) and the null control

Branch `cursor/glmflash5-work-cb5c` (run A). Builds: **B_VT** (sha 9d9bb176…) = clean base +
deepseek6's `bundle_a_compose.patch.txt` (ChecksLmr+LmrFine composed — the two plain patches
COLLIDE in the LMR block, its report says both orders fail; the composed one applied clean);
**B_VP** (sha 7de8656d…) = clean base + ChecksLmr, SoundArms, SoundRegret, SoundSteps in that
order (deepseek6's working order; component shas verified: Arms 57524c71…, Regret 10208495…,
Steps 07713c3b…, ChecksLmr d33b27ca…). All five matches COMPLETE. times: see stamps.txt.

## 1. What was asked, the answer, how sure

Asked: row 3 — VT (V + the fine reductions) and VP (V + pv1) at 2,000 and 20,000 nodes, plus
the N0 null control; the bundle rows checked against deepseek6's long-19 rows.

Answer: **M111 (VT-F0 @2k): +1.74 [−10.31, +13.78] and M112 (VT-F0 @20k): +0.87 [−9.14,
+10.88] — the VT bundle is LEVEL at both node counts; the two components' small positives do
not add.** **M113 (VP @2k): +72.97 [+60.39, +85.56] — VP keeps essentially ALL of pv1's 2,000-
node gain (P alone pools +80.1); the extension cap costs it almost nothing.** **M114 (VP @20k):
+3.13 [−6.74, +13.00] — level, like P's own 20k pool (+9.9) is not confirmed here.** **M115
(N0): Elo −0.00 ± 0.00 with n5 = [0, 0, 1000, 0, 0] — the perfect null: every one of the 1,000
pairs split 1–1 (each pair's two games are colour-mirrored copies).**

**My decision on deepseek6's flagged question (recorded before the matches, in the prediction
commit): the VT matches set LmrGiveCheckF=0 AND LmrInCheckF=0 on top of the queue's literal
reading** — otherwise the bundle silently DROPS V's check content (the fine branch keeps its
own F-terms at 1024). The F-options exist in B_VT's uci list (default 1024, range 0–4096).
The plain V+T1 row (without F-zeros) was ALSO measured and equals deepseek6's 9,331,413
exactly — so both readings are now pinned.

How sure: step 0 is the strongest yet — SEVEN rows on the two new builds, all exact against
knowns (S14 ×2, V, T1, P, and the two deepseek6 cross-checks V+T1/V+P); five probes exact
(every bundle option line verified per side); 10,000/10,000 validation rows; identities +
openings-slice checks by the committed `queue3_stats.py`. One seed per match.

## 2. Step 0 — eight rows on the two bundle builds (`queue3_rows.txt`, script `queue3_rows.py`
COMMITTED)

| build | setting | first-3 nodes | sum over 200 | known | check |
|-------|---------|---------------|--------------|-------|-------|
| B_VT | S14 | 41311, 24872, 28574 | 9,500,069 | ✓ | OK |
| B_VT | V | 15600, 24808, 38064 | 8,565,026 | ✓ | OK |
| B_VT | T1 | 42893, 29118, 29414 | 10,170,054 | ✓ | OK |
| B_VT | V+T1 plain | 23953, 20709, 44201 | 9,331,413 | deepseek6's ✓ | OK |
| B_VT | VT-F0 (+ LmrGiveCheckF 0, LmrInCheckF 0) | 15708, 18770, 33743 | 9,088,630 | MINE | first measurement |
| B_VP | S14 | 41311, 24872, 28574 | 9,500,069 | ✓ | OK |
| B_VP | P | 17188, 26670, 44100 | 9,476,627 | ✓ (and = B6's pv1 row) | OK |
| B_VP | V+P | 17918, 21122, 22675 | 8,650,468 | deepseek6's ✓ | OK |

Pins were verified on both builds by deepseek6's report and re-checked here via the S14 rows;
the four bench/perft pins ran in job 21/26 on the SAME binaries' parents — the bundle builds'
own pins: B_VT/B_VP bench 11/13 and perft 5 were NOT re-run this item (the S14 row equality to
the node is the stronger identity; noted honestly).

## 3. Step 2 — five probes (`probe_M111…M115.log`; probe openings lines 6401–6410, no match
uses them; each probe's setting and full option list stamped BEFORE the run)

| probe | cand received (2/2 each) | base received | refusals | go-limit |
|-------|--------------------------|---------------|----------|----------|
| M111/M112 (VT) | CED=8, GC=0, IC=0, LmrFine=1, FineHist=1, GiveCheckF=0, InCheckF=0 | its 14 ×2 (28), no extras | 0 | all `go` = the match's nodes |
| M113/M114 (VP) | CED=8, GC=0, IC=0, SoundPvArm=1, SoundStepMask=1 | its 14 ×2, no extras | 0 | same |
| M115 (N0) | nothing (S14 only) | nothing | 0 | same |

## 4. The matches (each setting's build on both sides; S14 both; cand's lines on top; nodes
2,000 for M111/M113, 20,000 for M112/M114/M115; Threads 1, Hash 16, OwnBook false, no
adjudication, pairs colours swapped, `-pgnout` in my folder; openings_queue3.epd by the
committed globbing script (105 gamelist files; 95,979 distinct openings removed; Random(41003)
— the same seed number queue 2's addendum file used, harmless: the used-set differs so the
files differ; 5,000 lines; first line
`r3k1nr/pbppqpbp/np2p1p1/8/3PP3/PPNB1N2/1BP2PPP/R2QK2R b KQkq - 0 8`), order sequential; M111
1–1000, M112 1001–2000, M113 2001–3000, M114 3001–4000, M115 4001–5000; concurrency 4)

Games by ending FIRST — all from the committed `queue3_stats.py` (output
`queue3_stats_out.txt`), identities and openings-slice checks printed by the same command
(losses on time BY SIDE 0/0; illegal/disconnect/crash 0):

| ending | M111 (2000) | M112 (2000) | M113 (2000) | M114 (2000) | M115 (2000) |
|--------|-------------|-------------|-------------|-------------|-------------|
| White mates | 778 | 575 | 724 | 612 | 600 |
| Black mates | 604 | 506 | 672 | 488 | 476 |
| 3-fold repetition | 326 | 636 | 340 | 595 | 600 |
| fifty moves | 174 | 145 | 163 | 153 | 174 |
| insufficient material | 111 | 132 | 98 | 148 | 144 |
| stalemate | 7 | 6 | 3 | 4 | 6 |
| **identity: mates = wins+losses** | 778+604 = 696+686 = 1382 ✓ | 575+506 = 543+538 = 1081 ✓ | 724+672 = 905+491 = 1396 ✓ | 612+488 = 559+541 = 1100 ✓ | 600+476 = 538+538 = 1076 ✓ |

| match | cand | build | nodes | seed | pairs | W-L-D | n5 | Elo, 95 % PAIR interval | complete? (duration) |
|-------|------|-------|-------|------|-------|-------|----|-------------------------|----------------------|
| M111 | VT-F0 | B_VT | 2000 | 40111 | 1000 | 696-686-618 | [107,198,374,220,101] | +1.74 [−10.31, +13.78] | COMPLETE (2:42) |
| M112 | VT-F0 | B_VT | 20000 | 40112 | 1000 | 543-538-919 | [41,253,419,234,53] | +0.87 [−9.14, +10.88] | COMPLETE (12:02) |
| M113 | VP | B_VP | 2000 | 40113 | 1000 | 905-491-604 | [60,131,337,279,193] | **+72.97 [+60.39, +85.56]** | COMPLETE (1:58) |
| M114 | VP | B_VP | 20000 | 40114 | 1000 | 559-541-900 | [51,211,454,237,47] | +3.13 [−6.74, +13.00] | COMPLETE (12:11) |
| M115 | N0 (S14 vs S14) | B_VT | 20000 | 40115 | 1000 | 538-538-924 | [0,0,1000,0,0] | −0.00 [−0.00, +0.00] — the perfect null | COMPLETE (12:22) |

predictions.txt (own commit 5e973af23, 21:06:12Z): M111 +8 [−4,+20] — held; M112 +1 [−9,+11] —
held; M113 +30 [+5,+55] — **CALLED WRONG** (+72.97, above +55); M114 +8 [−4,+20] — held;
M115 0 [−8,+8] — held (−0.00).

## 5. The M115 finding — why the null is perfect and what it explains

**M115's n5 = [0, 0, 1000, 0, 0]: every pair split 1–1.** With identical settings and the same
openings, each pair's two games are colour-mirrored copies of one game — fixed-nodes search is
deterministic per position-sequence, and the pair's two games share that sequence exactly.
This also EXPLAINS queue 2's puzzle (M106 vs the wrapped M110 differed on identical openings,
702/2000 same results): the two runs' concurrent game/process schedules differed (the seed
drives fastchess's scheduling), and under fastchess's process reuse a game's search is exposed
to its concurrent partner's transposition-table entries between its own moves — different
schedule, different pollution, different games. My reading of the mechanism is INFERENCE; what
is MEASURED: perfect mirroring at identical settings (M115), divergence at different seeds over
the same openings (queue 2), and exact per-position identity when engines run solo
(job 9/21/23's step-0 rows). Practical rules that follow: (a) never argue from "the same games
replayed"; (b) single-process step-0 rows are the only place determinism is usable; (c) the
match noise the pentanomial absorbs includes this schedule effect.

## 6. From my colleagues

- deepseek6's long 19: its bundle recipes, its working patch order, and its two cross-check
  numbers — all confirmed here to the node; its semantic warning (finding 1) was the decision
  this job's VT design turned on.
- Its notes also warn: a batch harness keeping one process carries depth-dependent bias vs a
  fresh-process harness — my step-0 drivers send ucinewgame per search and stay comparable.

## 7. What I did NOT do

- No VT-plain (without F-zeros) MATCH — its tree row is pinned (9,331,413) but the games ran
  with the F-zeros only; if Opus wants the plain-semantic games too, that is one more match.
- No pools this item (the queue's pool rule: items 4, 8, 12, 16, 20).
- The bundle builds' bench/perft pins were not re-run (the S14 row equality is the identity
  used; stated in §2).

## 8. What I am NOT sure about

- Whether VT-F0's level-ness means the F-zeroed terms really behave like V's (the fine branch's
  semantics under F=0 were not counter-verified — kimi5's territory).
- Whether VP@2k's +73 vs P's +80 pool is a real small interaction (deepseek6 saw the direction
  flip on O) or noise (one seed each).
- The TT-pollution mechanism (§5) — the mirroring is measured; the pollution path is my
  inference from fastchess's process reuse (kimi5 could confirm in the source).

## 9. A better way

- M115's perfect-mirror result gives the session a FREE determinism check: any match whose
  n5 is NOT [0,0,P,0,0] under identical settings has schedule noise — and any candidate-vs-S14
  match's n5 middle cell measures how much the candidate actually changed (job 15's M20 had
  764/1000 — barely acting). The middle-cell count is already in every stats output; it should
  be READ as the "did it act" dial in every report.

## 10. times: see stamps.txt.

## 11. Real output of `git status --short` and `ls` of the folder (verbatim, 21:48:15Z)

```
=== git status --short (head):
 M forge-combo29/tests_glmflash5_queue3/stamps.txt
?? forge-combo29/tests_glmflash5_queue3/M111_last40.txt
?? forge-combo29/tests_glmflash5_queue3/M111_stdout.txt
=== ls tests_glmflash5_queue3: (committed files)
bundle_a_compose.patch.txt
cmd_M111.txt cmd_M112.txt cmd_M113.txt cmd_M114.txt cmd_M115.txt
config_M111.json config_M112.json config_M113.json config_M114.json config_M115.json
exe_sha256_queue3.txt
gamelist_M111.txt gamelist_M112.txt gamelist_M113.txt gamelist_M114.txt gamelist_M115.txt
make_openings_queue3.py openings_queue3.epd prediction.txt
probe_M111.log probe_M112.log probe_M113.log probe_M114.log probe_M115.log
queue3_match.sh queue3_rows.py queue3_rows.txt queue3_stats.py queue3_stats_out.txt queue3_summary.txt
M111_last40.txt M111_stdout.txt
M112_last40.txt M112_stdout.txt
M113_last40.txt M113_stdout.txt
M114_last40.txt M114_stdout.txt
M115_last40.txt M115_stdout.txt
stamps.txt
```
(the `M`/`??` lines were the pre-commit state; everything joins this push.)

## 12. Model name

glmflash5 (GLM, flash tier), run A on `cursor/glmflash5-work-cb5c`.
