# swarm/multipv — MultiPV output audit

Audit seat for the MultiPV **output** of `forge-combo29` at base `6b98f217`. Read
[`FINDINGS.md`](FINDINGS.md) for the report and [`STATUS.md`](STATUS.md) for the scorecard.

**Engine source is unmodified.** `src/` and `include/` here are the base commit's files, byte for
byte, so the four honesty pins can be checked against this branch.

## Why this tree is trimmed

The base commit's `forge-combo29/` is 4.0 GB, almost all of it unrelated test transcripts
(`tests_astra_parity`, `tests_astra_mateguard`, …). This branch carries only what is needed to
build the engine and reproduce every number:

```
forge-combo29/
  src/  include/  CMakeLists.txt     the engine, unmodified from 6b98f217
  tests_r3fu_12/positions.txt        the corpus this audit draws from
  scripts/check_pins.sh  LOCK.md  README.md
  swarm/multipv/                     this seat's deliverable
```

Nothing is missing for reproduction: the audit reads `tests_r3fu_12/positions.txt` and the built
binary, and nothing else.

## Build

`/usr/bin/c++` on this image is clang 18 with a broken header path. Use:

```bash
cd forge-combo29
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build build -j4
```

Expect the four honesty pins to match — bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920,
perft 5 = 4865609. `scripts/00_build_and_pins.sh` does the build and the four checks in one step and
prints `PINS MATCH` only if all four hold.

## Reproduce

```bash
cd forge-combo29
./swarm/multipv/scripts/00_build_and_pins.sh .     # build + pins, must print PINS MATCH
./swarm/multipv/scripts/run_all.sh build/forge     # ~9 min; writes evidence/, renders the report
```

`run_all.sh` runs the checker self-tests **before** the measurements, prints each stage's counters,
and ends with `render.py`, which turns `FINDINGS.template.md` into `FINDINGS.md` and **fails if any
`[[counter]]` marker survives into its own output**. `FINDINGS.md` is the file a reader opens; it is
generated, so it cannot be committed with a placeholder in it.

## Layout

| file | what it is |
|---|---|
| `FINDINGS.md` | **the report a reader opens.** Generated; every figure resolved, zero markers |
| `FINDINGS.template.md` | the source a human edits. Carries `[[marker]]`s instead of typed numbers |
| `STATUS.md` | verdict, the six properties as a table, control inventory, limits |
| `scripts/multipv_lib.py` | strict UCI harness — Threads 1, wait on `bestmove`, FEN gate |
| `scripts/check_multipv.py` | the property checks + `--selftest` with 13 planted faults |
| `scripts/wire_control.py` | mutates real captured blocks; proves no checker is blind |
| `scripts/audit.py` | properties 1–4, the MultiPV 1 baseline, promotion attribution |
| `scripts/judge.py` | property 5's judge (deeper full-width search) and the depth-only control |
| `scripts/instability.py` | three-arm A/B/C: setting vs depth |
| `scripts/agreement.py` | the `searchmoves` noise floor that retired the first judge |
| `scripts/fastpaths.py` | property 6: book, drawn roots, precedence, `searchmoves` |
| `scripts/budget_stability.py` | the budget measurement three times, so the range is visible |
| `scripts/render.py` | renders the template into `FINDINGS.md`; 4 checks incl. zero-residual; `--selftest` |
| `evidence/` | every JSON the report cites, plus raw stdout under `evidence/wire/` |
