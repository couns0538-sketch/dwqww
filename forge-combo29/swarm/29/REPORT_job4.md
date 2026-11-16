# job4 - CHECK of 19-F13 (seat 19), a C line for my FINDINGS

## what I checked
19-F13 claims: "on the PC-relevant families (depth 12 over 200 of the new R_1911 set) `MovePicker::pick_best` is
7.93 % — hotter than `MovePicker::next` at 5.71 % — and `TT probe_body` is 5.77 %, up from 2.09 % on bench 13."

I did not have their `R_1911.fens`, so I built my own 400-position deep-search set from the brief's own sources
(200 of O + the first 200 of G) and profiled `go depth 12` over all of them, then the same engine on `bench 13`,
with a harness I wrote from their command file (not a copy of their script).

## the answer
**REFUTES 19-F13's `pick_best` > `next` ordering claim on my position set — but only narrowly, and the honest
statement is "the two are equal within sampling error", not "next is hotter".**

| symbol | deep search (my 400) | bench 13 |
|---|---|---|
| `MovePicker::pick_best` | 6.48 % | 6.27 % |
| `MovePicker::next(bool)` | **6.53 %** | 5.79 % |
| `TT probe_body` | 4.86 % | 1.95 % |
| `see_ge` | 5.54 % | 5.46 % |
| `fill_pseudo_legal` | 2.83 % | 2.81 % |
| `Worker::search` | 12.39 % | 12.44 % |
| `qsearch` | 3.29 % | 3.35 % |
| `evaluate_position` | 16.05 % | 15.36 % |

## how sure: LOW on the ordering, HIGH on the "TT probe rises" half
- The `pick_best` / `next` gap on my deep set is **0.05 percentage points** (6.48 vs 6.53). With ~1,000-2,000
  task-clock samples and a per-symbol sampling error near ±1 point, that is **a tie**, and I will not claim my F7
  direction was right. I record this as a REFUTATION of the *specific ordering claim* only, with the caveat that
  "equal" is the accurate reading.
- The `probe_body` half of 19-F13 **is supported and is the more interesting part**: 4.86 % on a deep position set
  against 1.95 % on bench 13, a 2.5x rise, in the same direction and of the same character as their 5.77 % vs
  2.09 %. That is a real difference between bench and deep search, and it is outside the evaluation.

## a table: step | done-partly-not done | evidence file | result

| step | done? | evidence | result |
|---|---|---|---|
| build my own harness from 19-F13's command file | done | `check_19f13.py` | independent driver, no code copied |
| deep-search profile, 400 positions at depth 12 | done | `raw_check19f13.txt` | 400 searches completed, all 8 symbols sampled |
| bench 13 profile for the comparison | done | `raw_check19f13.txt` | 8 symbols sampled |
| assert no missing symbol can pass as 0 | done | `check_19f13.py` prints NOT FOUND + INCONCLUSIVE | fires (it did, on my first broken run) |
| judge 19-F13's pick_best > next claim | done | verdict line | **REFUTES (narrowly; equal within noise)** |
| judge 19-F13's probe_body rise | done | table above | **SUPPORTS** |

## the harness bug this job caught (worth recording)
My **first** run of this check produced `deep-search NOT FOUND` for every symbol, because the driver wrote all 400
`position/go` pairs and then waited — i.e. it closed the pipe behind running searches, which is exactly the
19-F12 fault. The guard I had just added turned that into `INCONCLUSIVE` instead of a table of fake zeros. After
fixing the driver to read stdout to `bestmove` after every `go`, the same script produced the table above.

## findings
| id | area | one sentence | file with the exact command that shows it again | type |
|---|---|---|---|---|
| 29-C1 | CONFIRMS the `probe_body` half of 19-F13 | `TT probe_body` is 4.86 % of a 400-position depth-12 search against 1.95 % on `bench 13` (2.5x), so the transposition table really is a bigger share of real search than `bench` suggests — PC-relevant, outside the evaluation. | `forge-combo29/swarm/29/job4/check_19f13.py` | CONFIRMS 19-F13 (partly) |
| 29-C2 | REFUTES the `pick_best` > `next` half of 19-F13 | On my own 400-position depth-12 set `MovePicker::pick_best` is 6.48 % and `MovePicker::next` 6.53 % — a 0.05-point gap inside sampling error, so "pick_best is hotter than next" is not reproduced; on `bench 13` I get the opposite order (6.27 vs 5.79), also inside noise. Honest reading: the two are equal, and neither my 29-F7 nor their 19-F13 ordering should be quoted as established. | `forge-combo29/swarm/29/job4/raw_check19f13.txt` | REFUTES 19-F13 (partly) |

## suspicions, not proven
- The `bench`-vs-deep difference for `probe_body` may be hash pressure: `bench` clears the 16 MB table before every
  one of its 8 positions (`src/uci.cpp:617`), so its searches start cold and short, while my run keeps one table warm
  across 400 searches at depth 12. I did not separate "cold table" from "deeper tree".
- `evaluate_position` at 16.05 % here is the BUILT-IN net figure and remains worthless on the PC (Rule 2).

## what I did NOT do
- I did not obtain seat 19's `R_1911.fens`, so this is a check on a *different* position set, not a reproduction on
  theirs. A different set can legitimately give a different ordering, which is why I am not claiming their numbers
  are wrong — only that their conclusion does not survive on mine.
- No hardware-event profiling (`perf_event_paranoid=2` blocks `cycles`), so all shares are task-clock samples with
  the error that makes a 0.05-point gap meaningless.
- I did not attempt a patch from either ordering claim, because neither ordering is established.

## what I am NOT sure about
- Whether `pick_best` would exceed `next` deeper than depth 12, or on positions with more pieces (my set is 200
  openings + 200 game positions, so middlegame-heavy but not endgame-heavy).
- Whether the 2.5x `probe_body` rise holds at a different `Hash` size; I used Hash 16 throughout, as the brief
  specifies for node-count work.

times: see stamps.txt
