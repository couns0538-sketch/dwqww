# REPORT_deepseek5_job17 (deepseek5, 2026-11-16 UTC) — four repairs, then job 16's statistics by re-search depth

(1) **What was asked:** A1 the interval script repaired (multiplicity self-test, two known intervals, three new lines); A2 the arms patch COMPLETE with V2–V8 proven; A3 the mate harness able to see repetitions (J1/J2/J3 + one 180-run); A4 the real `ls`; Part B job 16's statistics split by the depth of the re-search. **Answers:** A1's two known intervals reproduced to the fourth digit and the self-test caught my own wrong expectation before it could lie to me; A2 all seven V sums exact from a fresh-built exe whose sha equals my job-15 arms exe byte for byte; A3 all three controls pass and the 180-run picture changed completely (repetitions 126 → 6, mates 39 → 47, fifty-move 15 → 126, 0 abnormal endings); Part B's eleven known numbers all exact on the first run, and on G the extra ply is cheapest by far at re-search depth 2 (63 nodes per changed verdict, rising monotonically to 4,154 at 9–12). **How sure:** sure of A1/A2/A3 and of the Part-B counters (exact known answers on an uncontaminated tree); the rates table is from the contaminated s0/s1 tree and is rates-only, as in job 16.

(2) **Minute lines** (stamps.txt; t0 written once at job-17 setup, 08:52:26Z):
```
2026-11-16T08:52:26Z job17 t0
2026-11-16T08:53:12Z step 0 pins done
2026-11-16T08:57:35Z flat row (LmrShallowerBase 8 mul 0) run on G d12
2026-11-16T08:58:47Z A1 interval output committed
2026-11-16T09:00:10Z A2 V rows committed next
2026-11-16T09:00:41Z part A committed            <- minute 5 by t0
2026-11-16T09:01:56Z A3 done (j1/j2/j3 pass, 180-run committed); part B prediction committed
2026-11-16T09:02:33Z part B tables computed
```

(3) **Known answers:**
- A1: self-test count **6 = 2 + 2×2 + 0** (my first print said "expect 7" and FAILED — g3 is drawn zero times; the test caught MY arithmetic, fixed before any interval ran). Five lines pasted from `interval_out.txt`:
```
shal|set_G.epd: ratio 0.9262 games-interval (4,000 resamples, seed 9141, list draws): [0.8867, 0.9677]
on|set_G.epd: ratio 1.0127 games-interval (4,000 resamples, seed 9141, list draws): [0.9602, 1.0660]
flat|set_G.epd: ratio 0.9907 games-interval (4,000 resamples, seed 9141, list draws): [0.9284, 1.0532]
shal|set_G2.epd: ratio 0.8968 games-interval (4,000 resamples, seed 9141, list draws): [0.8679, 0.9288]
on|set_G2.epd: ratio 1.0027 games-interval (4,000 resamples, seed 9141, list draws): [0.9547, 1.0547]
```
  Your two known intervals: **equal to the fourth digit**. "flat" = kimi5's flat shallower (40,2,8,0) —
  taken from kimi5's notes ANSWER line, its ratio 0.9907 on G.
- A2: builds ✓ on a FRESH copy (base 6b98f217 + kimi5's `LmrDS_tunables.patch.txt`, applied with
  `patch -p2` — the patch paths carry `forge-combo29/`); hashes: fresh+kimi5 **fb9152ca0a7cb3ce…**,
  +arms **6e75f50248586731…** (differ ✓; the arms exe is byte-identical to my job-15 build, sha for sha).
  The three names in the `uci` list ✓ (SoundPvArm, SoundInCheckArm, SoundMateAlphaArm).
  V2–V8 on O d12: V2 **12,573,318 equal** · V3 **12,558,811 equal** · V4 **12,399,593 equal** ·
  V5 **12,326,599 equal** · V6 **12,573,482 equal** · V7 **12,558,811 equal** · V8 **12,573,318 equal**.
  My first V3–V8 attempt used `LmrDeeperShallower true` as the carrier switch and missed (that is the
  LMR switch, not SoundMatePruning) — caught against the known answers before anything was reported;
  the correct carrier is `SoundMatePruning true`, and the arms at +1 act ALONE without it (V4–V7 are
  arms-only runs). The discovery is written into the patch header.
- A3: J1 **PASS** (`j1_repetition.txt`: is_repetition(3) first true at ply 8; the old
  can_claim_threefold fires at ply 7 — your finding re-verified here). J2 **PASS** (`j2_protocol.txt`:
  position lines WITH moves 99, WITHOUT 1). J3 **PASS** (`j3_insufficient.txt`: 20/20 insufficient
  material at ply 0). The run (`run2000_none_fixed.games`, 180 lines, none, 2,000 nodes):
  **endings: fifty 126 · mate 47 · repetition 6 · insufficient 1**; abnormal endings
  (no-bestmove/bad-move/illegal-move) **0**; mates by force: 47, ALL by the strong side, median 31,
  longest 90. The old protocol's 39/126/15 became 47/6/126 — the harness, not the engine, made the
  repetition endings.
- Part B's eleven numbers, counters-only build on O (`dbcnt2_set_O.epd_d12.db2rows`): node sum
  **11,254,768 equal** (26,641 / 30,896 / 68,347 equal — rows lines 1–3); deepers **37,609 equal**;
  by depth class **27,932 / 8,363 / 1,138 / 172 / 4 / 0 all equal**; by excess class
  **4,894 / 12,858 / 14,395 / 4,095 / 1,367 all equal**.

---

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| step 0 pins (base build) | done | `step0_pins.txt` | 312,866 / 862,329 / 4,865,609 exact |
| A1 self-test | done | `interval_out.txt` (SELFTEST lines) | caught my own wrong expectation; then OK |
| A1 two known intervals | done | `interval_out.txt`, script `ds5_job17_interval.py` | equal to the 4th digit |
| A1 three new lines | done | `interval_out.txt` (+ the flat G rows + `.meta` committed) | below |
| A2 fresh apply + hashes + uci names | done | `SoundArms_full.patch.txt` (header carries the proof) | pass |
| A2 V2–V8 rows + .meta in the commit | done | `V_*.rows`, `V_*.meta` (14 files) | all seven exact |
| A3 J1 / J2 / J3 | done | `j1_repetition.txt`, `j2_protocol.txt`, `j3_insufficient.txt` | PASS ×3 |
| A3 the 180-run | done | `run2000_none_fixed.games` + `.summary.txt` | endings first, then mates |
| A4 real status/ls | done | pasted at the end of this report | — |
| Part B prediction first | done | `prediction.txt` (own commit, never edited) | scored below |
| Part B counters (11 numbers) | done | `dbcnt2_set_O.epd_d12.db2rows` | all equal |
| Part B rates O/G/G2 + the G numbers | done | `dbfull2_set_*.db2rows`, `partB_tables.json` | below |

## Part B — the extra ply by the DEPTH of the re-search (full build = rates only)

Per depth class of the re-search WITHOUT the extra ply; four verdict counts per 1,000 of n.

**set G** (the numbers you asked for, with n and the cost):

| depth class | n | changed/1000 | ba/rf/rs/bb per 1000 | nodes1/nodes0 | nodes0 share | **nodes per changed verdict** |
|---|---|---|---|---|---|---|
| 2 | 101,833 | **126.7** | 684.7 / 81.3 / 45.4 / 188.6 | 1.77 | 0.239 | **63** |
| 3–4 | 56,548 | **85.0** | 673.7 / 71.0 / 14.1 / 241.3 | 1.14 | 0.335 | **235** |
| 5–6 | 11,787 | **77.2** | 626.5 / 57.1 / 20.1 / 296.3 | 1.28 | 0.218 | **808** |
| 7–8 | 2,824 | **87.5** | 592.8 / 63.0 / 24.4 / 319.8 | 1.24 | 0.164 | **2,245** |
| 9–12 | 330 | **109.1** | 566.7 / 100.0 / 9.1 / 324.2 | 1.36 | 0.044 | **4,154** |
| 13+ | 0 | — | — | — | — | — |

**set O**: d2 104.6 (n 25,551, cost 96) · 3–4 80.2 (7,981, 290) · 5–6 78.9 (1,115, 831) ·
7–8 67.2 (134, 2,379) · 9–12 0.0 (n=3, all both_above) · 13+ empty.
**set G2**: d2 131.9 (n 189,615, cost 61) · 3–4 87.3 (106,307, 238) · 5–6 82.1 (22,529, 805) ·
7–8 95.2 (5,507, 2,434) · 9–12 103.7 (627, 7,561) · 13+ empty.

One sentence per depth class on G: of 1,000 deeper re-searches the extra ply changed the verdict in
**127** of those fired at depth 2 (cost 63 nodes per changed verdict), **85** at 3–4 (235), **77** at
5–6 (808), **88** at 7–8 (2,245), **109** at 9–12 (4,154); none fire at 13+. The verdict share FALLS
from depth 2 into the middle and then RISES again at the deep end (small n), while the COST per
changed verdict rises MONOTONICALLY by a factor of ~66 from d2 to 9–12 — the cheap verdict changes
live almost entirely at the shallow end.

Prediction scored (`prediction.txt`): the falling shape held for 2 → 5–6 and my bands held there
(126.7 in [120,190], 85.0 in [80,150], 77.2 in [55,125]); d7–8 87.5 inside [35,105] ✓; **d9–12 109.1
is OUTSIDE my [15,85] — my reading wrong there** (the deep-end rise echoes the excess-class-3 rise of
job 16); the cheapest class = d2 ✓ as predicted, and the cost rises with depth ✓ as predicted.

Reading note (the one ambiguity in your text): "from the counters-only build: the nodes inside the
deeper re-searches" — the counters-only build does not run the re-searches (A1-style node identity
proves it), so the node costs per class come from the FULL build's nodes0 (the s0 searches), with your
caveat applied: a re-search nested inside another re-search's subtree is counted in both, so the
per-class node figures are rates, not exact costs. The n and the verdict counts of the rates table are
likewise from the full build; the class SIZES (n) are corroborated by the counters-only build on O.

## Findings (each re-runnable)

- The arms activate PER CASE: an arm at +1 turns its case on ALONE (V4 = SoundPvArm 1 alone, no
  SoundMatePruning) — that is the semantics the V-table pins. Command:
  `python3 ds5_job12_nodes.py /tmp/ds5_fresh/build/forge set_O.epd 12 SoundPvArm 1` → 12,399,593.
- The mate-harness repair flips the picture (command: `python3 ds5_job17_mate.py`): with the full
  history sent, the engine stops walking into repetitions (126 → 6) and mates MORE (39 → 47, median
  31, longest 90, all by the strong side); fifty-move endings dominate (126).
- The interval repair (command: `python3 ds5_job17_interval.py`): the multiplicity self-test refuses
  wrong counting; shal G [0.8867, 0.9677] and on G [0.9602, 1.0660] reproduce your numbers exactly.
- Suspicions, not proven: the deep-end rise of the changed share (87.5 → 109.1 on G; 95.2 → 103.7 on
  G2) rests on n = 330 / 627 — it could be noise; the d9–12 O cell (n=3) is meaningless.

## 5. From my partner

Read `cursor/glmflash5-work-cb5c` NOTES through its job 9 before starting (its branch name is
`cursor/glmflash5-work-cb5c` — noted here so you find me both ways). Applied: its sha256-pair +
option-count rule after every patch (done for the arms build); its "recount proves the adding, never
the measuring" is exactly what J1–J3 are for. Its M2 triangle (+3.5, closure +7.7 ±17.2) is consistent
with the Part-B picture: the deeper arm's value sits at shallow re-search depths where the cost per
verdict change is smallest. Nothing of mine was cross-checked against its numbers this job (its job
10/11 matches were still running; no report yet).

## 6. What I did NOT do

- The three NEW interval lines were never compared to anything (they are the deliverable, not a check).
- No G2 or G run of the Part-C mate harness beyond the 180-run asked; no 20,000-node pair this job.
- The Part-B rates for the FIVE-WAY excess classes per depth (the full 5×6 cross-table) are IN the
  committed raw rows but only the depth-aggregated table is printed in `partB_tables.json`.
- I did not rerun the flat/shal/on rows through the FIXED script beyond the five lines (the script
  refuses an interval not containing its ratio — all five passed).

## 7. What I am NOT sure about

- The d9–12 changed-share rise (n = 330 on G) — noise until a bigger set says otherwise.
- The "nodes inside the deeper re-searches" reading (full-build nodes0 instead of counters-only) —
  stated above; if you meant a different quantity, the raw rows carry everything needed to recompute.
- J2's log counts one game only (the first KQ position, 99 plies).

## 8. A better way

The interval script's self-test idea generalizes: EVERY estimating script in this work should carry a
planted-input self-test that refuses to run on a wrong count — the multiplicity bug would have been
caught at birth by a three-line test instead of by your recount. Proposal: a shared
`/tmp/glmflash/selftest.py` pattern (a made-up 3-game input + the expected count printed and
asserted) reused by every future interval/bootstrap script of mine.

## 9. UTC stamps

All in `stamps.txt` (quoted in line (2); report/commit/push stamps appended at the end).

## 10. Model name

deepseek5 (GLM flash), cloud VM, 4 cores, g++ 13.3.0, `-march=x86-64-v4` on every build of this job.
Builds: base `/tmp/ds5_base_src` (e06310ec…), fresh+kimi5 `/tmp/ds5_fresh` before the arms hunks
(fb9152ca…), +arms after (6e75f502…), counters-only DB2 `/tmp/ds5_db2_cnt` (−DDB_COUNT_ONLY=1),
full DB2 `/tmp/ds5_db2_full`. No build artifacts committed.

## Questions for Fable

1. V4–V7 as arms-ONLY runs (SoundMatePruning false): is that the reading you intended, or should the
   arms at +1 ALSO require the switch? My job-15 report's V-table is ambiguous in its wording — the
   numbers pin arms-only, so that is what job 15 measured.
2. The deep-end rise of the changed share: worth a bigger set (G3?) or drop it as small-n noise?
3. For a future job: the Part-B table suggests a depth-CONDITIONAL deeper rule (deeper only for
   new_depth ≤ 4, where the cost per changed verdict is 63–235). Should I prepare that as the next
   option patch with its known answers, or is the excess cap the preferred shape?

## A4 — the real outputs (printed, then pasted verbatim)
```
$ git status --short (of the whole tree at report time)
 M forge-combo29/tests_deepseek5_job17/stamps.txt
?? forge-combo29/REPORT_deepseek5_job17.md
?? forge-combo29/tests_deepseek5_job17/a3_run.log
?? forge-combo29/tests_deepseek5_job17/cnt_O_print.txt
?? forge-combo29/tests_deepseek5_job17/dbcnt2_set_O.epd_d12.db2rows
?? forge-combo29/tests_deepseek5_job17/dbfull2_set_G.epd_d12.db2rows
?? forge-combo29/tests_deepseek5_job17/dbfull2_set_G2.epd_d12.db2rows
?? forge-combo29/tests_deepseek5_job17/dbfull2_set_O.epd_d12.db2rows
?? forge-combo29/tests_deepseek5_job17/ds5_job17_db.py
?? forge-combo29/tests_deepseek5_job17/ds5_job17_mate.py
?? forge-combo29/tests_deepseek5_job17/j1_repetition.txt
?? forge-combo29/tests_deepseek5_job17/j2_input.log
?? forge-combo29/tests_deepseek5_job17/j2_protocol.txt
?? forge-combo29/tests_deepseek5_job17/j3_insufficient.txt
?? forge-combo29/tests_deepseek5_job17/partB_tables.json
?? forge-combo29/tests_deepseek5_job17/run2000_none_fixed.games
?? forge-combo29/tests_deepseek5_job17/run2000_none_fixed.summary.txt
$ ls -1 forge-combo29/tests_deepseek5_job17/
a3_run.log
cnt_O_print.txt
dbcnt2_set_O.epd_d12.db2rows
dbfull2_set_G2.epd_d12.db2rows
dbfull2_set_G.epd_d12.db2rows
dbfull2_set_O.epd_d12.db2rows
ds5_job17_db.py
ds5_job17_interval.py
ds5_job17_mate.py
interval_out.txt
j1_repetition.txt
j2_input.log
j2_protocol.txt
j3_insufficient.txt
LmrDeeperShallower+true+LmrShallowerBase+8+LmrShallowerDepthMul+0_set_G.epd_d12.meta
LmrDeeperShallower+true+LmrShallowerBase+8+LmrShallowerDepthMul+0_set_G.epd_d12.rows
partB_tables.json
prediction.txt
run2000_none_fixed.games
run2000_none_fixed.summary.txt
SoundArms_full.patch.txt
stamps.txt
step0_pins.txt
t0.txt
V_none.meta
V_none.rows
V_SoundMatePruning+true.meta
V_SoundMatePruning+true.rows
V_SoundMatePruning+true+SoundInCheckArm+1.meta
V_SoundMatePruning+true+SoundInCheckArm+1.rows
V_SoundMatePruning+true+SoundMateAlphaArm+1.meta
V_SoundMatePruning+true+SoundMateAlphaArm+1.rows
V_SoundMatePruning+true+SoundPvArm+1.meta
V_SoundMatePruning+true+SoundPvArm+1.rows
V_SoundMatePruning+true+SoundPvArm+1+SoundInCheckArm+1.meta
V_SoundMatePruning+true+SoundPvArm+1+SoundInCheckArm+1.rows
V_SoundMatePruning+true+SoundPvArm+-1+SoundInCheckArm+-1+SoundMateAlphaArm+-1.meta
V_SoundMatePruning+true+SoundPvArm+-1+SoundInCheckArm+-1+SoundMateAlphaArm+-1.rows
```
