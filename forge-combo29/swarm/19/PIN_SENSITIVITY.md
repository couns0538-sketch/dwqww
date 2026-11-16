# Which of the four pins can detect a move-ordering cost change?

seat 19 · area 9. A text-only answer, using an ablation I already had.

## 1. The short answer

**All four pins except perft 5 detect a move-ordering change — and strongly.** A picker change
(`std::sort` → `std::stable_sort`) that is *invisible in cost* but *visible in order* moves bench 11, 13 and
16 by 3–9 %, which is far outside any noise. perft 5 cannot detect it at all, because perft does not use the
picker.

**So the 19-F18 objection does NOT transfer to the ordering pins the way it transferred to the TT.** The
distinction matters and I want to state it precisely, because it is a correction to how my last message could
be read:

- For the **TT**, `bench`'s probes exercise the replacement path on **0.006 %** of calls. The workload almost
  never reaches the code, so a bench number cannot show a TT-cost change.
- For the **picker**, `bench` exercises the sort branch on **4.8 %** of calls (`job2` counters: 86,317 sorts
  in 1,806,615 pick_best calls) — not a large fraction, but the *node count* is a global function of the whole
  tree, so an ordering change propagates everywhere. The pin is sensitive to ordering even though the code
  path is a minority of calls.

The general rule this yields: **a bench pin is sensitive to anything that changes the TREE, and insensitive to
anything that only changes COST inside a rarely-taken path.** Ordering changes the tree. Hash-table
replacement cost does not.

## 2. The ablation, measured both ways

| build | bench 11 | bench 13 | bench 16 | perft 5 | R_1911 Hash 16 nodes |
|---|---|---|---|---|---|
| base 6b98f217 | 312,866 | 862,329 | 3,024,920 | 4,865,609 | 15,238,023 |
| `std::stable_sort` in `pick_best` | **292,627** | **939,494** | **2,925,608** | 4,865,609 | **16,102,887** |
| **does the pin see it?** | **yes, −6.5 %** | **yes, +8.9 %** | **yes, −3.3 %** | **no** | **yes, +5.7 %** |

R_1911 counters under the same ablation:

| counter | base | stable_sort | change |
|---|---|---|---|
| probes | 15,184,039 | 16,043,843 | +5.7 % |
| hit rate | 35.1 % | 35.3 % | — |
| full-table misses | 8,310,172 (54.7 %) | 8,811,039 (54.9 %) | tracks the node growth |
| `empty_none` | 0 | 0 | — |

So the R_1911 counter set also sees it, because every counter is a function of the tree the search walks.

## 3. What each pin can and cannot detect

| pin | detects a change in ordering? | detects a change in TT cost? | why |
|---|---|---|---|
| **bench 11** | **yes** (−6.5 % on the ablation) | no | 11 plies of search over 8 fixed positions; the tree is a function of ordering, but 11 plies is shallow enough that the table barely fills |
| **bench 13** | **yes** (+8.9 %) | **no** (0.006 % of probes reach the replacement scan) | deepest of the three; the table still never fills because each position is searched once |
| **bench 16** | **yes** (−3.3 %) | no | same reason as 13, with a larger tree and still no table pressure |
| **perft 5** | **no** | **no** | perft uses the move generator and `make_move` only — no picker, no table. It pins the generator, nothing else |

## 4. Practical consequences for validation

1. **A picker/ordering patch: any of bench 11, 13, 16 will show it.** They disagree in *direction* (11 and 16
   down, 13 up), so quoting one is not enough — quote all three, as the honesty check requires anyway.
2. **A TT patch: none of the four will show a cost change.** Use the recipe in `RECIPE_tt_validation.md`, and
   note that even there the counters prove the code is *reached*, not that it is *faster*.
3. **perft 5 is a generator pin only.** It cannot detect anything about ordering or the table. It is still
   worth keeping — it caught nothing so far, but it is the only pin that exercises `make_move` in isolation.
4. **A change that moves no bench pin has not been shown to change the tree.** That does not mean it is free;
   it means its cost lives somewhere the pins do not measure, and it needs a counter or a paired timing run.

## 5. Correction to how 19-F18 could be over-read

My last message said the same objection "applies to move ordering, where bench's fixed eight middlegame
positions are also unrepresentative". **That was too broad, and this ablation shows why.** bench's positions
are unrepresentative of the *distribution* of positions the PC will meet, which is a real limitation on
tuning decisions — but for a *cost* change, what matters is whether the code path is reached, and for
ordering the pin is sensitive because ordering changes the tree. I should have said "bench's positions are
unrepresentative for TT pressure and for tuning", not "for move ordering" without qualification.

## 6. What I did NOT do

- No test of a *cost-only* picker change (one that keeps order identical and only gets faster). That is the
  case where all four pins would stay flat and the ablation above says nothing. The honest statement is: this
  ablation bounds the *ordering* sensitivity, not the *cost* sensitivity, of the pins.
- I did not test whether bench 11/13/16 disagree in direction reproducibly across other ordering changes; I
  have one ablation.

## 7. Files

Pins: `job4/pins_stable_sort.txt`. Counters: `job4/stable_bench13.err`,
`job4/stable_R1911_h16.err`. Build recipe: `pickbest/edit_stable_sort.py` + `job4/instrument_tt.py`.
