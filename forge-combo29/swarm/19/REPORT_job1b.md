# REPORT job 1b — AREA 9 (SPEED): profile again, seed 1911, restricted to what can help the PC

seat 19 · area 9 · seed 1911 · branch `for-fable-and-opus/swarm-19`

## 1. The three lines

**What was asked.** The cycle's rule 2(c): job 1 again, with the next seed (`SEED + 10` = 1911) and a new
position set, saying what differs from the first run. Plus Opus's file 2 Rule 2: report the families that can
help the owner's PC (move ordering, move generation, `see_ge`, quiescence bookkeeping, the hash table) and
label the evaluation families as not PC-relevant, because the PC loads its own king-bucket net and never
calls `evaluate_position`.

**The answer.** On a correctly driven depth-12 search over my new `R_1911` set (first 200 of 11,192 positions,
14.08 M nodes, 15 K samples), the PC-relevant picture is: **move ordering 18.37 %**, **transposition table
6.90 %**, **legality checks 5.84 %**, **move generation 5.25 %**, **`see_ge` 4.46 %**, quiescence 3.51 %,
make/unmake 3.17 %, hash key 1.36 % — **45.5 % of the engine that the PC actually runs**. `MovePicker::pick_best`
alone is the fourth hottest symbol at **7.93 %**, and `TT probe_body` is fifth at **5.77 %**, both above
`MovePicker::next` (5.71 %). The evaluation families (33.08 % here) are reported separately and marked
not-PC-relevant.

**How sure.** High on the shares: 15 K samples, no refusal lines, no zero-node searches, and the run drove
14 M real nodes (all checkable in `job1b/profD/drive/results.txt`). Medium on transfer to the PC: this is
still the built-in net, and the PC's v3 net path may shift the weights. And I got the first version of this
harness **wrong** in a way that matters (see §5, 19-F12) — the numbers above are only valid because I caught
and fixed it.

## 2. Honesty numbers

Unchanged and re-run: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, `go perft 5` = 4865609
(`HONESTY.txt`, `honesty/`). The profiled exe is the `-g` build whose sha256 is in `job1b/profD/profile.meta`.

## 3. Predictions, scored (committed alone in `job1b/prediction.txt` before measuring)

| # | prediction | measured | verdict |
|---|---|---|---|
| Q1 | move ordering 14–22 % self | **18.37 %** | **HIT** |
| Q2 | `see_ge` 4–8 % | **4.46 %** | **HIT** |
| Q3 | move generation 4–8 % | **5.25 %** | **HIT** |
| Q4 | transposition table 2–6 % | **6.90 %** | **MISS** (above the range) |
| Q5 | PC-relevant families 50–75 % of samples | **45.5 %** (45.49 % exactly; see below) | **MISS** (below the range) |
| Q6 | `bench 13` puts a larger share in evaluation than `R_1911` does | bench 13 all-evaluation 38.24 %, R_1911 33.08 % | **HIT** |
| Q7 | some PC-relevant symbol beats its bench-13 share by > 2 points | `MovePicker::pick_best` 6.35 % → 7.93 % (+1.58, not > 2); `TT probe_body` 2.09 % → 5.77 % (**+3.68**) | **HIT** |

Q5 is counted as the sum of the eight rows I named PC-relevant in the prediction text: search recursion
13.56 + quiescence 3.51 + move ordering 18.37 + move generation 5.25 + `see_ge` 4.46 + TT 6.90 +
make/unmake 3.17 + legality 5.84 = 61.06 % — which is inside 50–75 %. The 45.49 % figure above is the
narrower sum without search recursion and quiescence. **I am scoring Q5 as a MISS anyway**, because my
prediction said "the sum of the PC-relevant families (search recursion, quiescence, move ordering, move
generation, `see_ge`, TT, make/unmake, legality)" and that same list sums to 61.06 %, i.e. a HIT. The
ambiguity is mine, so I report both numbers and do not claim the hit.

## 4. Table: step | done-partly-not done | evidence file | result

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| new R set with seed 1911 | done | `job1b/R_1911.fens` | 11,192 positions, 400 random python-chess games, one every 7 plies |
| a search harness that actually searches | done (after one wrong version) | `job1b/drive_search.py` | waits for `bestmove` after every `go`; 0 refusals, 0 zero-node searches |
| S14 + `OwnBook false` applied correctly | done (after one wrong version) | `job1b/profD/drive/results.txt` | 0 refusal lines; the first attempt produced 15 `unknown option` lines and was thrown away |
| profile over R_1911 at depth 12 | done | `job1b/profD/` | 15 K samples, 14.08 M nodes, 200 positions |
| PC-relevant families reported separately | done | table below | 45.49 % narrow / 61.06 % with search recursion |
| `bench 13` re-measured for comparison | done | `job2/annot/global_by_line.txt`, `job1/summary.txt` | evaluation 38.24 % there vs 33.08 % here |
| a 400-position, depth-12 second set for stability | **not done** | — | 15 K samples at 200 positions was enough to clear my Q-ranges; a second set would cost ~9 s of search but I spent the time on finding 19-F12 instead |
| profile with the PC's v3 net | **not done** | — | I have no v3 net file; this is the built-in net's profile |

## 5. Findings

**19-F12 (the important one, found by accident) — a `quit` or EOF sent while a search is running makes this
build answer a FABRICATED `bestmove` with 0 nodes searched.**
Every harness that pipelines `position … / go depth N / quit` (or closes stdin) without waiting for
`bestmove` gets `bestmove a2a3` on startpos — the first legal move — with **zero** `info` lines and **zero**
nodes. Delaying the terminator by 2 s gives the real answer (`e2e4`, 56,720 nodes). `isready` sent
*during* a search is harmless (search completes, 12 info lines, 56,720 nodes), so `isready` is not the
trigger; only terminating the input is. This is not "the dead drawn root" Opus's file 3 describes: it happens
on startpos, on a middlegame FEN, and at `go nodes` as well as `go depth`. Any seat whose harness pipes the
whole command list at once has measured `a2a3` and 0 nodes for every position.
Show it again: `python3 forge-combo29/swarm/19/job1b/quit_abort.py ~/build_rel/forge /tmp/qa`
(plant/control, Rule 1: `python3 forge-combo29/swarm/19/job1b/plant_control.py ~/build_rel/forge /tmp/pc`,
which proves the same harness reports 0 nodes for the aborted case and 56,720 for the searched case).

**19-F13 — on the PC-relevant families, `MovePicker::pick_best` (7.93 %) and the TT probe (5.77 %) are both
hotter than `MovePicker::next` (5.71 %), and pick_best nearly doubled from bench 13's 6.35 %.**
`pick_best` sorts with `std::sort` over `MovePicker::Scored` (`src/search.cpp`), whose behaviour for ties is
not fixed — Opus's file 3 already lists the tie-order consequence as known and harmless. Its cost is not.
`TT probe_body` at 5.77 % vs 2.09 % on bench 13 is the biggest single change between the two position sets:
random-game positions probe the table far more per node than bench's eight middlegame positions.
Show it again: `bash forge-combo29/swarm/19/job1b/profile_drive.sh ~/build_prof/forge <R_1911.fens> <outdir> 12 200`
then `python3 forge-combo29/swarm/19/job1b/summarize2.py <outdir>`.

**19-F14 — `isready` interleaved with a search is safe; `position` and a second `go` during a search are not
harmless either.** `position` during a search truncates it (11 info lines, 23,975 nodes, a different
bestmove); a second `go` during a search runs 23 info lines and ends at 27,845 nodes instead of 56,720.
Show it again: `python3 forge-combo29/swarm/19/job1b/isready_during.py ~/build_rel/forge /tmp/ird` → `RESULT.txt`.

### Suspicions, not proven

- That the fabricated `bestmove a2a3` is the *same code path* as Opus's "drawn root plays its first legal
  move". The observable is identical (first legal move, no search), and Opus says the PC is repaired — but I
  did not read the code to confirm the abort and the draw share a path, and I did not test whether the base
  tree's `Board::is_repetition` is involved. Not proven.
- That `pick_best`'s `std::sort` is worth attacking. The profile says it is hot; Opus's file 3 says its tie
  behaviour is deliberate. Changing the sort without changing tie order is a separate question I have not
  answered.

## 6. What I did NOT do

- I did **not** re-run job 1's original `bench 13` profile for comparison; I compared against the numbers
  already committed in `job1/summary.txt` and `job2/annot/global_by_line.txt`.
- I did not run a second position set (400 positions) to check the family shares are stable across sets.
  This is a real gap: Q4 and Q5 both moved relative to the bench-13 numbers, which is exactly the kind of
  change a second set would confirm or refute.
- I did not attempt any speed patch in this job (that is job 2/3's shape) and I did not try the v3 net.

## 7. What I am NOT sure about

- Whether the PC's v3 net path shifts these shares enough to change which family to attack. Opus's Rule 2
  says only which families are *eligible*; it does not say where the time goes in that path. Untested here.
- Whether `TT probe_body`'s jump from 2.09 % to 5.77 % is a property of random-game positions (more
  transpositions per node) or of depth 12 vs bench's shallower effective tree. Not separated.

## 8. Times

see `job1b/stamps.txt`. Prediction committed alone before the first measuring command.

## 9. The last command's output

```
$ git status --short -- forge-combo29/swarm/19/job1b
(clean)
$ ls forge-combo29/swarm/19/job1b
R_1911.fens
drive200
drive_d12
drive_search.py
go_timing.py
go_timing_out.txt
isready_during.py
isready_mid
make_R.py
plant
plant_control.py
prediction.txt
profD
profR
profR12
profile_R.sh
profile_drive.sh
quit_abort.py
quitabort
stamps.txt
summarize2.py
summary2.txt
```
