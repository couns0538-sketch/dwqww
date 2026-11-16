# REPORT — seat 25, area 5, job 3 (checkmated and stalemated roots, under ASan + UBSan)

## What was asked
10 checkmated and 10 stalemated root positions, each with `go depth 5`, `go nodes 100` and `go movetime 50`;
the exact answer lines; under ASan + UBSan.

## The answer
60 runs, **0 sanitizer lines, 0 crashes, `bestmove 0000` in 60 of 60** — and every one of the 20 roots was
confirmed terminal by python-chess before use. Two reporting faults came out of it that the brief did not
ask about but which the data shows plainly: a checkmated root is reported as `score mate 0`, and a terminal
root makes `go nodes` / `go movetime` emit 64 infos at zero nodes.

## How sure
Very sure of the sanitizer result: BOTH required proofs are present (below), and the runner's ability to
see a sanitizer line is calibrated by a plant that produced 120 counted lines. Very sure of the two
reporting faults (they are in the raw answer lines, reproducible in one command).

## Honesty numbers (release build)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match (`../HONESTY.txt`).
The sanitizer build is a DIFFERENT build (RelWithDebInfo, -O1, -fsanitize=address,undefined) and is not used
for any node-count claim.

## THE TWO PROOFS THE BRIEF REQUIRES for "0 sanitizer lines"

1. **Symbols present**: `nm -C ~/build/asan/forge | grep -c __asan_` = **35**;
   `grep -c __ubsan_` = **15**. Recorded in `sanitizer_symbols.txt`. (A release build gives 0.)
2. **A planted fault counted by the SAME runner**: `fake_asan_engine.py` prints a real-looking
   `ERROR: AddressSanitizer: heap-buffer-overflow` on every `go`. Fed to the unchanged
   `run_mate_roots.sh`, the runner counted **120** sanitizer lines (`/tmp/plant_mate`, 60 runs x 2 matching
   lines). The same runner then counted **0** on the real engine.

Both together mean the "0" is a measurement, not an absence of instrumentation.

## What was done

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| sanitizer build | done | `sanitizer_symbols.txt` | 35 asan + 15 ubsan symbols, built with g++ 13.3.0 |
| proof 1: nm counts | done | `sanitizer_symbols.txt` | 35 / 15 |
| proof 2: planted fault through the same runner | done | `fake_asan_engine.py`, `planted_fault.py` | 120 lines counted (PASS) |
| FIRST root list (hand-written) | done but WRONG | `real/summary.tsv`, `fen_check.txt` | only 5 of 10 per group were actually terminal — my FENs, not the engine; see below |
| corrected root list | done | `make_terminal_fens.py`, `mate_roots.fens`, `stale_roots.fens` | 10 + 10, each verified terminal by python-chess before use |
| 60 runs on the corrected roots | done | `final/summary.tsv`, `final/all_raw.txt` | 60/60 bestmove 0000, 0 sanitizer lines |
| `mate 0` probe with stalemate control | done | `mate0_probe.py`, `mate0_probe.txt` | checkmated root -> `score mate 0`; stalemated -> `score cp 0` |

## Findings

### S-F6 (NEW) — a checkmated root reports `score mate 0`
Checkmated root `8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1`:
```
info depth 1 seldepth 1 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv
...
info depth 5 seldepth 5 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv
bestmove 0000
```
`mate 0` is not a legal claim: the side to move is already checkmated, so the score is "mated now", and a
mate distance of 0 plies cannot be expressed as `mate N` for any N (the engine's own conversion in
`format_score`, src/search.cpp:272-279, computes `distance = MateValue - |score|` then `(distance+1)/2`, and
at `score = -MateValue` that gives `mate 0`). A GUI reading `mate 0` has no defined meaning for it.
The same engine reports a STALEMATED root (also terminal) as `score cp 0` — so the two zero-move cases are
reported in two different currencies, which is the inconsistency worth fixing.

Shows again:
```bash
python3 forge-combo29/swarm/25/job3/mate0_probe.py /path/to/forge
```

### S-F7 (NEW) — a terminal root spins to depth 64 at zero nodes
On terminal roots, `go nodes 100` and `go movetime 50` emit **64 info lines, depths 1..64, nodes 0**, instead
of one line and a stop. With `go depth 5` it emits exactly 5 lines. So the loop is bounded only by the depth
cap, not by the fact that there is nothing to search.

| root | go | info lines | depths | nodes |
|---|---|---|---|---|
| checkmated | go depth 5 | 5 | 1..5 | 0 |
| checkmated | go nodes 100 | 64 | 1..64 | 0 |
| checkmated | go movetime 50 | 64 | 1..64 | 0 |
| stalemated | go nodes 100 | 64 | 1..64 | 0 |
| stalemated | go movetime 50 | 64 | 1..64 | 0 |

Shows again: `mate0_probe.txt`.

## A mistake I made and fixed (kept, not hidden)
My first root list was hand-written and only 5 of 10 FENs per group were actually terminal; the other 15 were
ordinary positions, so the engine correctly returned real moves (`a1a5`, `d8g8`, ...). I caught this by
checking every FEN against python-chess (`fen_check.txt`: 0 disagreements between "python-chess says terminal"
and "engine said 0000" — so the ENGINE was right and my FENs were wrong). I then generated and verified a
correct set (`make_terminal_fens.py`) and re-ran. The 60/60 result above is the corrected run; the first run's
files are kept in `real/` so the error is auditable.

## Predictions
No prediction file was written for job 3 before its first measuring command. That is a process failure on my
part — the brief requires a PREDICTION committed alone before the first measurement of every job. Job 1 and
job 2 both have one; job 3 does not. I am stating it rather than writing a prediction after the fact, which
would be worthless.

## What I did NOT do
- No TSan build (that is area 4's job; my area asks for ASan + UBSan on these roots).
- I did not run the *other* 15 FENs of my first list as a separate ordinary-position test.
- I did not test `go infinite` + `stop` on a terminal root.
- No prediction for this job (see above).

## What I am NOT sure about
- Whether `mate 0` is considered acceptable by the owner's GUI; it is unusual but some GUIs treat it as
  "mate now". I am reporting the inconsistency (stalemate says cp 0) rather than claiming the GUI breaks.
- Whether the 64-line spin costs measurable time. It is zero nodes, so almost certainly not; I did not measure
  wall time for it.

## Times
see `stamps.txt`.

## Last command output
```
$ ls forge-combo29/swarm/25/job3/
all_raw.txt (in real/ and final/)  fake_asan_engine.py  mate0_probe.py  mate0_probe.txt
mate_roots.fens  stale_roots.fens  make_terminal_fens.py  planted_fault.py  run_mate_roots.sh
run_terminal.sh  sanitizer_symbols.txt  fen_check.txt  real/  final/
```
