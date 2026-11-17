# STATUS — option-pair interactions (`swarm/optpairs`)

**State: complete.** Nine pairs attempted, seven measured, two cited from the existing audit.
Two findings that are not about pairs came out of the work and are in `FINDINGS.md` §8.

## Build and pins

| item | value |
|---|---|
| commit | `6b98f217` (audit base) |
| compiler | `/usr/bin/g++` 13, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13` |
| march | `-DFORGE_MARCH=x86-64-v4` |
| binaries | `/tmp/build-optpairs/forge` (audit build), `/tmp/build-v3/forge` (`+ -DFORGE_NNUE_V3=1`), `/tmp/build-tsan/forge` (`-fsanitize=thread`), `/tmp/build-planted/forge` (planted-fault control) |
| pins | **bench 11 = 312,866 · bench 13 = 862,329 · bench 16 = 3,024,920 · perft 5 = 4,865,609 — all four matched** |
| box | 4 cores, no SMT |

`scripts/pins.sh` re-runs the four. The v3 and TSan binaries were spot-checked on bench 11
(312,866 on the v3 build); the TSan and planted builds are not used for any pin-carrying number.

## What is measured, and where

| pair | script | evidence |
|---|---|---|
| Hash × Threads (400k nodes, A/A design) | `pair1_hash_threads.py` | `pair1-hash-threads.json`, `pair1-analysis.json` |
| Hash × Threads (2M nodes, Hash effect present) | `pair1b_hash_threads_2m.py` | `pair1b-hash-threads-2M.json`, `pair1b-analysis.json` |
| Hash × Threads (1 MB vs 256 MB, max pressure) | `pair1c_hash_pressure.py` | `pair1c-hash-threads-pressure.json`, `pair1c-analysis.json` |
| the pooled A/A-vs-A/B test | `pair1_pooled.py` | `pair1-pooled.json` |
| MultiPV × Threads | `pair2_multipv_threads.py` | `pair2-multipv-threads.json`, `pair2-analysis.json` |
| Hash × bail, MultiPV × bail | `pair3_hash_multipv_bail.py` | `pair3-hash-multipv-bail.json`, `pair3-analysis.json` |
| Hash-axis liveness + fault control for the bail grid | `pair3b_hash_axis.py` | `pair3b-axis-*.json`, `pair3b-analysis.json` |
| Move Overhead × floor (200 ms clock) | `pair4_overhead_floor.py` | `pair4-overhead-*.json`, `pair4-analysis.json` |
| Move Overhead × floor (overhead × clock grid) | `pair4b_overhead_clocks.py` | `pair4b-analysis.json` |
| Book Depth × OwnBook × Variety | `pair5_book.py` | `pair5-book.json`, `pair5-analysis.json` |
| Book Depth boundary, exact, on an in-book line | `pair5b_book_boundary.py` | `pair5b-boundary.json`, `pair5b-hits.json` |
| Book Variety quantification + pin | `pair5c_variety.py` | `pair5c-variety.json` |
| Threads × NNUE (behavioural) | `pair6_threads_nnue.py` | `pair6-analysis.json` |
| Threads × NNUE (TSan) | `tsan_soak.py` | `tsan.json`, `tsan.txt` |
| TSan planted-fault control | `tsan_soak.py` + `tsan_planted_race.sh` | `tsan-planted.json` |
| UseNNUE × NnueFile × NNUEArch | `pair7_loader.py` | `pair7-loader.json`, `pair7-loader.txt` |
| UseNNUE vs `eval` divergence | `pair7b_usennue_eval.py` | `pair7b-usennue-eval.json` |

Cited from the existing audit and not re-run: **Threads × drawn-root bail** (20 of 20 cells
identical, §3) and the same-value-resize-equals-`Clear Hash` result (§3, trap 3).

Support: `uci.py` (the driver), `grid.py` (cell runner), `analyze.py` (set-overlap helper, used
during design), `positions.json` (fixtures), `check_positions.py` (both-gate fixture validation),
`make_v2_nets.py` / `make_v3_nets.py` (net fixtures, generated not committed).

## Traps this seat hit, and how each was caught

Every one of these produced a number before it was caught. They are listed because the numbers in
`FINDINGS.md` are only worth what the instruments behind them are worth.

1. **A wall time measured around the whole subprocess.** `subprocess.run(...)` includes ~18–20 ms of
   process startup, and at a 200 ms clock that is the same order as the floors being measured. The
   first clock grid reported **1.3×–4.3× overshoot on plans the engine honours exactly** (a 6 ms
   plan "taking" 26 ms). Caught by noticing that the overshoot was *constant in milliseconds*
   (18–20 ms) across every cell, which is a signature of a fixed cost and not of a clock. Repaired
   by timing from the `go` write to the `bestmove` line; the corrected run reports 0.83×–1.0×.
2. **A TSan harness that stopped reading at `bestmove`.** ThreadSanitizer prints its report **at
   exit**, after the search is over, so the harness saw a clean pipe for a binary that was racing.
   Caught by the planted-fault build: a deliberately shared accumulator reported **0 races**. Two
   further fixes were needed after that — the planted store was eliminated as dead until a read was
   added, and only then did it report. The shipped run drains the pipe to process exit.
3. **A pipe with `quit` in it.** The brief's trap 1, and it bit the first TSan shell script: every
   search there printed a bare `bestmove` and **zero `info depth` lines**, so nothing was searched
   and the clean sanitizer output was noise about an idle process. Caught by asserting the info-line
   count per case; the TSan report now refuses to accept a case with 0 info lines.
4. **A grid where the option never reached the engine.** `NNUEArch` is not in the audit build at all
   (see `FINDINGS.md` §8), and a cell for it would have been "identical on every position" for the
   wrong reason. Caught by the acceptance check on `unknown option` in every cell, which is why that
   check runs before any grid is recorded. The fault control (`Bogus Option`) is in the evidence.
5. **Comparing a threaded cell with itself and calling it an effect.** The first Hash × Threads grid
   reported **12 of 12 positions differing** between Hash 16 and Hash 64 at Threads 4 — and the
   *same cell against itself* also differed 12 of 12. The whole comparison was discarded and
   rebuilt around A/A controls; `pair1-an*` is the rebuilt version and the superseded counts appear
   nowhere in `FINDINGS.md`.
6. **A "boundary" tested at fullmove granularity.** The first Book Depth probe varied the FEN's
   fullmove counter on the start position, which moves `game_ply` by 2 and cannot resolve a one-ply
   boundary. Replaced by walking a line that is in the book and stepping Book Depth across the
   boundary one ply at a time (24 of 24 cells).

## Withdrawn

- **"Hash at Threads 4 differs 12 of 12."** Withdrawn entirely — it is the same-cell spread. The
  replacement is a null: pooled mean Δagreement −0.012, p = 0.55.
- **"A large Move Overhead overshoots its plan by 1.3×–4.3×."** Withdrawn — a startup-cost artefact.
  The replacement is the opposite finding: the plan is honoured, and the real hazard is the cliff at
  `time ≤ overhead`.
- **"The TSan arm is clean."** Withdrawn as stated the first time, because the arm could not fire.
  Restated only after the planted-fault build reported as designed.

## Not done, and why

- **51 of the 82 advertised options are tunable spin values** behind `FORGE_EXPOSE_TUNABLES`; this
  report pairs 12 named settings and none of the tunables. "About 35 options" counts without them.
- **No real v3 network exists in this tree**, so v3 was tested with two synthetic 32-hidden nets
  built to the loader's format; evaluation quality and v3 × {Hash, Threads} are untouched.
- **`Threads 8` pairs are untested** except under TSan — 2× oversubscribed on this box.
- **No match, no self-play, no Elo.** Every number here is a fixed-depth, fixed-node or clock-capped
  search on fixture positions; nothing is a strength claim.
