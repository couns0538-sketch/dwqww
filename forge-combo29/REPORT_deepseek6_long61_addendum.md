# ADDENDUM — long 61's rows committed, and its checker planted (file 22's two points)

Folder `tests_deepseek6_long61/` (+ `tests_deepseek6_long61plant/`) · branch for-fable-and-opus/deepseek6-work
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. The two things file 22 said were missing

File 22: *"long 61 (MultiPV): its `out/` rows are not in the commit (only the 13-line summary), and the checker has
no plant. Commit the rows; plant one fake engine that answers a duplicate move in MultiPV 3 and one with a rising
score; the checker must count each as 1 violation."*

**Both done.** The rows are now `tests_deepseek6_long61/out/multipv_rows.tsv` — **600 data rows plus a header**,
one per (position, k), with the moves, the scores, the bestmove, the first line and any violation the checker
recorded. And the plant is in `tests_deepseek6_long61plant/` with a control.

## 2. The rows

`out/multipv_rows.tsv`, 601 lines: `pos | k | lines | moves | scores | bestmove | first_line | violations`.
The full run was **repeated** to produce them (the original run printed only the summary), and it reproduced the
headline exactly:

```
== MultiPV CHECK ON ALL 200 POSITIONS OF O, DEPTH 10
violations: 0
k=3: first line equals k=1's bestmove on 130 of 200 (different on 70)
k=5: first line equals k=1's bestmove on 124 of 200 (different on 76)
```

130/200 and 124/200 are the numbers in my long-61 report to the position, so the re-run is the same measurement
with the rows kept this time.

## 3. The plant, with the control that file 22 implied

`tests_deepseek6_long61plant/multipv_fake.py`, driven through the **unmodified** `multipv61.py`:

| FAKE_MODE | what it breaks | violations counted | which ones |
|---|---|---|---|
| `dup` | line 2 repeats line 1 | **4** | `duplicate_move` only (2 positions x k=3 and k=5) |
| `rise` | scores increase down the list | **4** | `score_order` only (e.g. `[10, 20, 30]`) |
| `clean` | nothing | **0** | — |

The `clean` row is the point: without it, "4 violations" would be consistent with a checker that flags any engine
that is not the real one. With it, each defect is attributed to the clause it actually breaks.

**The fake had to be made honest to get there.** My first version answered fixed moves (`a2a3`, `b2b3`) that are
**illegal** in the two test positions and printed no MultiPV-1 form, so the checker correctly reported
`illegal_pv` and `no complete iteration` alongside the intended defect — 7 and 8 violations instead of 4. The
committed version parses `position fen`, answers **legal** moves from that position, tracks the `MultiPV` setoption
so each k gets the right number of lines, and prints k=1 in the engine's plain form. That is what makes the
attribution exact.

**And it exposed a real bug in my checker:** `run()` returned a 4-tuple on one path and a 3-tuple on another, so
the first plant attempt died with `ValueError: not enough values to unpack`. Fixed in `multipv61.py` (both paths
now return `(rows, bm, err, want)`), and the fix is committed with this addendum. The full-set re-run above was made
with the fixed checker.

## 4. What I did NOT do

- Did not change long 61's conclusions: the contract result (0 violations on 600 reads) and the churn counts
  (130/124 of 200) are the same numbers, re-measured.
- Did not add an `illegal` fake: file 22 names two plants, and the checker's `illegal_pv` branch was already
  demonstrated by accident in my first fake attempt (reported above rather than hidden).
- No pull request, no branch but mine.

## 5. The model

Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.
Times: `stamps.txt` (the re-run's stamp is `stamp3.txt`).
