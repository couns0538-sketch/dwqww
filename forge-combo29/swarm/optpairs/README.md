# forge-combo29 — option-pair interactions (`swarm/optpairs`)

Which of the engine's options interact, measured on the audit base `6b98f217`.

**Result first: [`FINDINGS.md`](FINDINGS.md).** Method, build, pins and the traps this seat hit are
in [`STATUS.md`](STATUS.md). Raw evidence is in [`evidence/`](evidence/).

## The short version

| pair | interacts? |
|---|---|
| Hash × Threads | **no** — not even at Hash 1 MB against 256 MB (pooled p = 0.55 over 28 positions) |
| Hash × drawn-root bail | **no** — 0 of 8 bailing roots, with the Hash axis proved live 7 of 8 elsewhere |
| MultiPV × drawn-root bail | **no** — 0 nodes and empty pv at MPV 1/2/3 |
| MultiPV × Threads | **yes** — Threads does nothing above MultiPV 1 (identical 6 of 6; MPV 1 control differs 6 of 6) |
| Book Depth × OwnBook × Variety | **yes** — OwnBook/Depth decide *whether*, Variety decides *which*, and it is the only RNG |
| Move Overhead × clock floor | **yes** — a cliff at `time ≤ overhead`, not a smooth shift |
| Threads × drawn-root bail | **no** — cited from §3, 20 of 20 |
| Threads × NNUE | **no race found** — TSan clean over 10 threaded cases, with the arm proved able to fire |
| UseNNUE × NnueFile × NNUEArch | **yes** — strict precedence, and `NNUEArch` is not in the shipped build at all |

Two findings that are not about pairs:

- **`NNUEArch` is unreachable in the audited binary** — the brief's CMake recipe never defines
  `FORGE_NNUE_V3`, so the engine answers `unknown option NNUEArch`. `tests_astra_v3/` tests a build
  the audit does not ship.
- **`eval` and the search disagree about `UseNNUE`** when a v3 net is loaded: the search uses the
  hand-crafted evaluation (6 of 6 positions match the no-net arm exactly) while `eval` reports
  `nnue_v3` (6 of 6).

## Layout

```
FINDINGS.md          the result, then the evidence, one section per pair
STATUS.md            build, pins, what was measured, traps hit, what was withdrawn
scripts/
  pins.sh            the four honesty pins
  uci.py             driver: fresh process per cell, reads to bestmove, checks option acceptance
  grid.py            cell runner: repeats, acceptance, difference criterion
  pair*.py           one script per pair; each writes its own JSON
  check_positions.py fixture validation through python-chess AND the engine
  make_v2_nets.py    builds the v2 net fixtures (no binaries are committed)
  make_v3_nets.py    builds the v3 net fixtures
  tsan_*.py|sh       the sanitizer arm and its planted-fault control
  run_all.sh         rebuild and re-run everything
evidence/            every JSON the scripts produced
evidence/superseded/ first runs kept only because STATUS.md cites them as withdrawn
evidence/nets/       generated net fixtures (gitignored; hashes in README.txt)
```

## Reproducing

```bash
cd scripts && ./run_all.sh
```

Rebuilds the three binaries, re-runs the pins (all four must match before anything is recorded),
validates the fixtures, regenerates the net fixtures and runs every grid. The threaded and
clock-timed grids want an otherwise idle box: this machine has 4 cores and the same cell differs from
itself on 12 of 12 positions at Threads 4.

## What this folder does not claim

No match, no self-play, no Elo. Every number is a fixed-depth, fixed-node or clock-capped search on
fixture positions. `Threads 8` is untested except under TSan (it is 2× oversubscribed on this box).
No real v3 network exists in this tree, so v3 *evaluation quality* is untouched — only the loader
path and the precedence were measured.
