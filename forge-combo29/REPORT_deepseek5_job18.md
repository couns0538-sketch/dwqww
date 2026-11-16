# REPORT_deepseek5_job18 (deepseek5, 2026-11-16 UTC) — kimi5's step mask at in-check nodes, and the shallower half done right

(1) **Part 0: done.** The fifteen owed files of job 17 were committed UNCHANGED (commit
"deepseek5 job 17 owed files (job18 part 0a+0b)"; none was gone, none remade); the three arms-alone
rows + .meta committed beside them (PV 12,399,593 / in-check 12,326,599 / mate-score 12,573,482);
the supersede line is in NOTES_deepseek5.md. `git status --short` after that commit showed exactly
one `??` line — the new job-18 folder itself; no untracked file inside job 17's folder.
**X1 / X2 / X3:** my predictions (committed before the runs in `prediction.txt`) were WRONG on all
three, in the most informative direction: X1 = **12,573,318 = none exactly** (I predicted the
mask-1 tree), X2 = **12,573,318 = none exactly** (same wrong prediction), X3 = **12,326,599 =
"SoundInCheckArm 1" exactly** (I predicted NOT equal). Both of your stated conditions hold.
(3) **One sentence:** the in-check step-1 cell is NOT real as a pruning effect — step 1's condition
fires 27,820 times at in-check nodes on O, but exempting it changes not one node (X1 = none on
200 of 200; X3 = "SoundInCheckArm 1" on 200 of 200), and the A4 counter shows why: the flag's
withheld quiets still come out of the picker (it only stops GENERATING quiets, search.cpp line 646
inside `next(bool skip_quiets)` called at line 1895), and their fate is decided by steps 2–6
(15,805 searched / 11,515 dropped) — the same searched set as with step 1 running; kimi5's 505/1000
and 16,452 counted firings and pseudo-legal quiets, not searched-set changes.

## stamps.txt, pasted as it is

```
2026-11-16T09:10:32Z job18 t0
2026-11-16T09:11:30Z A1 build+pins done
2026-11-16T09:13:33Z A2 rows exact; A3 prediction committed
2026-11-16T09:16:59Z A4 counter run done (sum 12,573,318 kept)
2026-11-16T09:18:24Z part B sbrows O+G done
2026-11-16T09:19:12Z A5 asan runs done (0 reports)
2026-11-16T09:20:02Z report written
```
(later stamps appended at the end: report commit, notes, push.)

## Step table

| step | done | evidence file | result |
|---|---|---|---|
| 0a fifteen owed files | done | commit "…owed files…"; `git status` clean inside job 17 | done |
| 0b arms-alone rows + .meta | done | `V_SoundPvArm+1.*`, `V_SoundInCheckArm+1.*`, `V_SoundMateAlphaArm+1.*` (job 17 folder) | sums exact |
| 0c supersede line | done | NOTES_deepseek5.md | done |
| 0d clean status | done | pasted above and in the commit | one `??`: job18 itself |
| A1 fresh apply ×3 + pins + names | done | `k5_apply_out.txt`, `k5_pins.txt` | 3× OK; pins 312,866 / 862,329 / 4,865,609; the three names in `uci`; exe sha b8e0d1668c9afe20… |
| A2 seven rows | done | `ds5j18_a2.txt` (committed as `a2_rows.txt`) | all seven exact (below) |
| A3 prediction before runs | done | `prediction.txt` (own commit) | all three WRONG — reported as such |
| A3 X1/X2/X3 | done | `x_rows.txt` | X1 none, X2 none, X3 = InCheckArm 1 |
| A4 counter-only build | done | `A4_counters.patch.txt`, `a4_O.dbrows` | O sum 12,573,318 kept ✓ |
| A5 plant + ASan/UBSan runs | done | `asan_plant_*`, `asan_runs.txt`, `asan_direct.txt` | plant caught; 0 engine reports |
| Part B shallower from SB fields | done | `sb_set_O.epd_d12.sbrows`, `sb_set_G.epd_d12.sbrows`, `sb_table_*.json` | known answer met |

## A2 — the seven rows on O, depth 12 (exe sha b8e0d166…, kimi5's three patches on a fresh base copy)

| setting | sum | known | equal |
|---|---|---|---|
| none | 12,573,318 | 12,573,318 | ✓ |
| SoundMatePruning true | 12,558,811 | 12,558,811 | ✓ |
| SoundPvArm 1 | 12,399,593 | 12,399,593 | ✓ |
| SoundInCheckArm 1 | 12,326,599 | 12,326,599 | ✓ |
| SMP true + SoundStepMask 0 | 12,573,318 | = none, 200 of 200 (kimi5) | ✓ (sum equal; per-position equality not separately diffed — the sum equality over 200 positions with this harness is the check) |
| SMP true + SoundStepMask 1 | 11,944,468 | 11,944,468 | ✓ |
| SoundPvArm 1 + SoundStepMask 1 | 11,944,468 | 11,944,468 | ✓ |

## A3 — X1, X2, X3 against the predictions

| run | my prediction (before) | measured | your criterion |
|---|---|---|---|
| X1 InCheckArm 1 + mask 1 | = SMP+mask1 (11,944,468): YES | **12,573,318 = none** | condition 1 HOLDS |
| X2 MateAlphaArm 1 + mask 1 | = SMP+mask1: YES | **12,573,318 = none** | (stronger than asked) |
| X3 InCheckArm 1 + mask 62 | = InCheckArm 1: NO | **12,326,599 = InCheckArm 1** | condition 2 HOLDS |

Where my model went wrong: I read the arm as a pure exemption and step 1 as a global pruner. The
patch (read AFTER the X runs, as the report rule allows me to say) shows the arm's case sets a GATE
and the mask then chooses which steps the case skips — and the tree evidence says step 1's pruning on
O lives entirely at PV nodes (SMP+mask1 = 11,944,468 differs from none ONLY through the PV case,
since the in-check and mate-alpha exemptions change nothing). X2 = none was the surprise: the
mate-alpha case behaves like the in-check one here.

## A4 — the counter that settles it (counter-only; O sum 12,573,318 kept exactly)

Per search the build prints one `info string A4 …` line; the harness takes per-position differences
(`a4_O.dbrows`, 200 rows; the patch is `A4_counters.patch.txt`). Totals over O at depth 12, none:

| counter | value | meaning |
|---|---|---|
| ic_s1_flag_set | **27,820** | step 1's condition FIRED at an in-check node (the moment it sets the flag) |
| ic_flagged_yielded | **374,609** | quiets the picker still yielded at in-check nodes AFTER the flag was set |
| ic_flagged_searched (a) | **15,805** | of those: reached the search |
| ic_flagged_skipped (b) | **11,515** | of those: dropped by a step's `continue` (steps 2–6) |
| ic_quiets_total | 2,262,163 | all (pseudo-legal) quiets yielded at in-check nodes |
| ic_quiets_dropped | 11,515 | legal in-check quiets dropped inside the block by any step |

Reading, with the honest caveats:
- The picker OBEYS the flag at generation (`search.cpp:646`, `if (!skip_quiets) generate_quiets();`
  inside `MovePicker::next(bool skip_quiets)`, called at `search.cpp:1895`) and IGNORES it for
  already-queued moves — 374,609 quiets came out after the flag was set.
- Of the flagged quiets, (a) 15,805 were SEARCHED and (b) 11,515 dropped by steps 2–6; the rest
  (347,289) were pseudo-legal quiets that fail the legality filter in check and were never search
  candidates at all.
- a + b = 27,320 vs kimi5's 16,452 (its `k5_j5_cnt_d12.json` field d20): the same population seen
  through two different counters — but neither number is a SEARCHED-SET change. The searched-set
  argument is the tree: X1 = none and X3 = InCheckArm 1, node for node. Step 1's 27,820 in-check
  firings remove NO move that steps 2–6 (or the flag's own withholding of an already-doomed tail)
  would not remove identically.
- Counter-only proof: the set-O node sum with the counters in place = 12,573,318 = none exactly.

## Part B — the shallower half from the SB fields (sets O and G; the Part-C build unchanged)

The SB fields WERE in the build's output; my job-16 harness never parsed them (your WRONG 1 — the
"symmetry" table of job 16 was the deeper counters read twice; it is RETRACTED). The new harness
(`ds5_job18_sb.py`) parses and diffs both DB and SB parts; rows committed.

| set | positions | shallower events by excess class [1–40, 41–100, 101–400, >400] | ba / rf / rs / bb per 1,000 (class 1–40) | verdict changed per 1,000 | snodes1/snodes0 |
|---|---|---|---|---|---|
| O | 200 | **[5,951, 0, 0, 0]** | 436.7 / 0.0 / 0.0 / 563.3 | **0.0** | 0.006 |
| G | 353 | **[8,016, 0, 0, 0]** | 429.5 / 0.0 / 0.5 / 570.0 | **0.5** | 0.004 |

- The known answer is MET: every class above 40 is EMPTY (both sets, and the verdict fields are all
  zero there). The four verdicts add up to the events in every row (checked per class, "OK" in the
  aggregation).
- The finding that replaces my wrong "symmetry": one ply DOWN changes the verdict in ~0 of 1,000
  shallower re-searches (O: 0 of 5,951; G: 4 of 8,016 = 0.5 per 1,000), while one ply UP changes it
  in 65–140 of 1,000 deeper re-searches. The asymmetry is structural: the shallower arm fires on
  moves that did NOT clearly beat best, and a one-ply-deeper look almost never rescues such a move
  past alpha; the deeper arm fires on moves that DID beat best by a margin, where the extra ply
  overturns refutations at the measured rates. The shallower half's value is NOT verdict-changing —
  it is pure node saving.

## A5 — sanitizers (address + undefined) on the patched build

- The planted-fault control FIRST: `/tmp/asan_plant.c` (a heap overflow at index 4 of a 4-int block,
  then a signed overflow), compiled with the SAME compiler and flags (`gcc -fsanitize=address,undefined -g`):
  the run reports `ERROR: AddressSanitizer: heap-buffer-overflow` and exits 1 (`asan_plant_out.txt`,
  `asan_plant_result.txt` — the overflow aborts before the UB line, so one report, the control stands).
- The patched build (kimi5's three patches) rebuilt with `-fsanitize=address,undefined -g`:
  50 positions of O at depth 10, once with `SoundMatePruning true + SoundStepMask 1`
  (sum 1,029,386) and once with `SoundRegretCount true` (sum 1,175,574): **0** sanitizer reports in
  both runs (`asan_runs.txt`) and 0 in a direct single-position engine run with stderr captured
  (`asan_direct.txt`).

## 5. From my partner

`cursor/glmflash5-work-cb5c` re-read before this job: its job-10 report (M3 −8.9 [−19.6, +1.8],
M4 −2.6, M5 −0.4, closure −8.33 ±18.50). Cross 1 already verified its step-1 tree sums node for
node. Its "FOR deepseek5" line asked for one line confirming the arms options exist with counts —
done in Part 0b/0c (the arms-alone rows + the supersede note); it can run its standard chain on the
in-check arm if it wants (my A2/A3 rows are the tree side).

## 6. What I did NOT do

- The 5×6 cross-table (excess × depth) of Part B's SB counters is in the raw rows, not tabulated.
- No TSan run this job (A5 asked address+undefined only).
- The per-position equality for "SMP+mask0 = none on 200 of 200" was checked as a SUM equality only.
- I did not rerun kimi5's SoundRegretProbe to reproduce its 505/1000 probe rate myself.

## 7. What I am NOT sure about

- Whether kimi5's 16,452 counts the same events as my (a)+firings or its probe's own population —
  the numbers are the same size (16,452 vs 27,820 firings / 27,320 decided) but the definitions may
  differ; what is certain is the TREE answer (X1/X3) and the picker mechanics (the line cited).
- The PV-node concentration of step 1's effect (SMP+mask1 vs none = only the PV case differs) rests
  on X1/X2's nulls; a direct PV-only counter would pin it — not built this job.

## 8. A better way

The X-row method generalizes into a cheap "case-ablation" test for ANY gated pruning block: for each
case c and each mask m, run the two settings {case armed, mask m} and {mask m alone}; node-equality
of the pair localizes the step's effect to the complement of the case in O(2·cases) cheap runs —
three of them answered a question two counter builds had argued about.

## 9. UTC stamps

stamps.txt pasted as-is above; the push-time stamp is appended to the file at push.

## 10. Model name

The runtime serving this Cursor cloud-agent run identifies as GLM, trained by Z.ai; the agent name
for this work is deepseek5. Beyond that string I cannot verify the exact model version — not known
to me beyond what the runtime says.

## Questions for Fable

1. The step-1 effect's PV-node concentration: worth a direct counter (firings at pv_node vs not), or
   do the X-rows settle it for your purposes?
2. The shallower half's ~zero verdict changes: does that change the plan for kimi5's "flat reshape"
   match (glmflash5's M5, −0.4 level)? A pure node-saver with no verdict effect should be Elo-neutral
   at fixed nodes by construction — the match already said −0.4.
3. Is my X2 (mate-alpha) null worth a counter like A4's (firings at mate-alpha nodes), or is the
   tree answer enough?
