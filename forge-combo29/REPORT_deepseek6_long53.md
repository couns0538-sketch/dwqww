# REPORT — deepseek6, long 53 (carried hash on game positions, depth 12 and 14)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long53/`
Model: DeepSeek V4.1 Flash 1017

## 1. What was asked, the answer, how sure

**Asked:** long 48's carried-table comparison (positions searched in ONE process without `ucinewgame`, Hash 16,
against the fresh-process rows) on the **first 100 positions of G**, at **depth 12 and depth 14** — do carried
entries make the tree bigger on game positions too?

**Answer:** **at depth 12 yes (+2.95 %), at depth 14 the opposite (−3.38 %).** The carried table makes the G tree
**bigger** one depth and **smaller** the next, with 99 of 100 positions changing in both cases and only 34 (d12) /
23 (d14) best moves changing. Long 48's +1.50 % on O at depth 12 was the same effect, half the size; it is a
depth-12 statement, not a general one.

**How sure:** certain of the four sums and of the row-by-row comparisons (100 positions each, committed rows,
metas and logs; one command re-derives the table). The *why* is a suspicion and is marked as one.

## 2. Honesty numbers (raw in `pins/`)

Build: plain 6b98f217 release, `/tmp/ds6/build-release/forge`, sha256
`7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`, `id name Chess Engine Forge 6.4.24
candidate`.

| pin | required | measured | file |
|---|---|---|---|
| bench 11 | 312866 | **312866** | `pins/pins_bench11.txt` |
| bench 13 | 862329 | **862329** | `pins/pins_bench13.txt` |
| bench 16 | 3024920 | **3024920** | `pins/pins_bench16.txt` |
| go perft 5 | 4865609 | **4865609** | `pins/pins_perft5.txt` |

All four exact, re-run before the first counted run in this item.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed with `claim.sh`, its line first in stamps.txt | done | `stamps.txt` line 1 | exit 0, 20:43:43Z |
| prediction as its own commit | done | `PREDICTION.md` | 6 predictions with kill ranges |
| pins re-run | done | `pins/*` | four exact |
| `G100.epd` = first 100 of G, in file order | done | `G100.epd` | 100 lines |
| fresh d12 + carried d12 | done | `runs/G100_{fresh,carried}_d12.rows` | 100 rows each |
| fresh d14 + carried d14 | done | `runs/G100_{fresh,carried}_d14.rows` | 100 rows each |
| comparison | done | section 4 | sign flip |
| scorecard | done | `scorecard.txt` | 3 held, 3 killed |

**Why two harnesses.** `rows.py` starts a **fresh process per position** with `ucinewgame`; `carried.py` keeps
**one** process for all 100 and never sends `ucinewgame`, so the transposition table carries entries from position
to position. Only the difference between the two measures the carried effect. Both read every answer line and stop
on a refusal (`carried.py`'s meta records `mode=CARRIED (one process, NO ucinewgame)`).

## 4. The table

| depth | fresh (100 positions) | carried (one process) | ratio | nodes changed | best moves changed |
|---|---|---|---|---|---|
| 12 | 5,247,038 | 5,401,723 | **1.0295 (+2.95 %)** | 99/100 | 34/100 |
| 14 | 12,377,717 | 11,959,927 | **0.9662 (−3.38 %)** | 99/100 | 23/100 |

Rerun: `python3 sum_rows.py runs/G100_fresh_d12.rows runs/G100_carried_d12.rows` (from my long 25) and the same
for d14.

## 5. Findings, each with the command that shows it again

**F1. The carried-table effect changes sign between depth 12 and depth 14 on game positions.** +2.95 % at d12,
−3.38 % at d14, a 6.33-percentage-point swing. Reproduce: the two sums above.
This is the second sign flip I have measured today (long 51 found the same shape in a bundle's interaction), so
"does X grow or shrink with depth" has now twice had the answer "it reverses".

**F2. Long 48's O result was the same effect at half size.** O, 50 positions, depth 12: +1.50 %. G, 100 positions,
depth 12: +2.95 %. Game positions are twice as sensitive to a stale table as opening positions — which fits: G's
positions transpose into each other less than book positions do, so more carried entries are wrong for the new
position.

**F3. 99 of 100 positions change their node count at BOTH depths — the effect is uniform, not carried by a few
positions.** Only the *sign* of the aggregate differs by depth. So this is not one pathological position dragging
a sum; every position feels the carried table.

**F4. Best-move churn is low and falls with depth: 34/100 at d12, 23/100 at d14.** Long 48's O run changed 14/50
(28 %) at depth 12; G here is 34 % — the same order. Deeper searches converge, as in my long 25 (O) and long 51
(G).

**F5. A carried table is not free in either direction.** At d12 it costs 2.95 % more nodes; at d14 it "saves"
3.38 %. A harness that searches many positions in one process (a match, or a batch perft-like sweep) therefore has a
depth-dependent bias in its node counts, and a batch and a fresh-process run of the same positions are **not**
comparable at either depth.

## 6. What I read from my colleagues

- **long 48's report** (this session's own earlier item): the O depth-12 carried result of +1.50 % and the
  Hash sweep. That is the anchor this item extends to G at two depths.
- No colleague note was used as an instruction. The job line (file 14) is the only directive.

## 7. What I did NOT do

- **Did not run the full 353 of G** — the item says the first 100.
- **Did not run O at depth 14** for the carried comparison — the item says G.
- **Did not vary Hash** — Hash 16 throughout, as the item says; long 48 covers the sweep.
- **Did not run any match**: node counts only.
- No pull request, no branch but mine, no engine source (the harnesses are text scripts).

## 8. What I am NOT sure about

- **Why the sign flips.** A plausible reading: at depth 12 the carried entries are mostly stale-but-hit table
  entries that return wrong bounds and force re-searches (bigger tree); at depth 14 the searches are long enough
  that a pre-filled table saves more than it misleads (smaller tree). I have not instrumented hit rates, so that
  is a suspicion.
- Whether the flip happens between 13 and 14 or drifts — two depths only.
- Whether O at depth 14 also flips. Untested here; long 48 only measured O at depth 12.

## 9. A better way

Report a carried-process number **always with its depth and always against a fresh run of the same positions in
the same order** — this item's design did exactly that, and that design is what made the sign flip visible. A
harness that quotes a batch sum without saying which process model produced it cannot be compared with anything.

## 10. Times and the folder

times: see `stamps.txt` (first line is `claim.sh`'s output).
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
