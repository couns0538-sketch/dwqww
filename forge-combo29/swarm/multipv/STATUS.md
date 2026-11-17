# STATUS — swarm/multipv (MultiPV output audit)

Branch: `swarm/multipv`
Base: `6b98f217` ("Checkpoint standalone NNUE v3 work and evidence")
Work directory: `forge-combo29/swarm/multipv/`
Engine source: **unmodified.** No file under `src/` or `include/` is touched. This seat adds a
harness, evidence and a report.

## Verdict in one line

The MultiPV output is structurally clean where the engine controls it (ordering, index order,
completeness at fixed depth, no over-claiming) and **wrong where a client actually looks**: PV-length
monotonicity fails in 116 of 160 final blocks, and the `multipv 1` line is the single-PV search's
answer in only 22 of 40 positions.

## The six properties, with counts

| # | property | result | denominator |
|---|---|---|---|
| 1 | emission order (wire) | **0 violations** | 1,920 blocks |
| 1 | index order (sorted by `multipv`) | **0 violations** | 1,920 blocks |
| 3 | score monotonicity at fixed depth | **0 violations** | 1,920 blocks |
| 4 | completeness at fixed depth | **0 missing / 0 dup / 0 extra** | 1,920 blocks |
| 4 | completeness under a budget | **32/32/32 (node)**; **36,36,33 (movetime, 3 repeats)** | 40 positions |
| 4 | `N > legal moves` overflow | **0** | 5 sparse × 2 MPV × 2 budgets |
| 2 | PV-length monotone in index | **116 violations** | 160 final blocks |
| 2 | line 1 not the longest | **80** | 160 final blocks |
| 5 | `bestmove` ≠ printed `multipv 1` `pv[0]` | **0** | 160 searches |
| 5 | `multipv 1` == single-PV answer | **22 identical** | 40 positions |
| 6 | book path emits `multipv` lines | **0 at MPV 2/3/6** | 3 arms + 3 controls |
| 6 | drawn root emits >1 index | **never (max index 1)** | 4 shapes × 4 MPVs |

## Controls, and what each one rules out

| control | result | what it rules out |
|---|---|---|
| four honesty pins on this build | **4/4 match** | wrong binary |
| checker selftest, planted faults | **26 checks / 13 faults / 0 failures** | checkers that cannot fail |
| wire control on real output | **43 assertions / 0 blind** | checkers blind to a real block's shape |
| determinism, MPV 1 and MPV 4 vs itself | **10/10 and 10/10 identical** | run-to-run noise |
| MultiPV 1 PV-length-vs-depth baseline | **289 of 480 blocks PV > depth** | reading extensions as a MultiPV bug |
| MultiPV 1 PV-vs-`seldepth` baseline | **0 of 480 violate** | reading `depth` as a bound on a PV |
| book `OwnBook false` on the same position | **at least 16 info lines** | attributing the book silence to the position |
| depth-only move stability (no MultiPV) | **12 of 40 change** | attributing all move churn to the setting |
| `searchmoves` judge noise floor | **12 of 12 pairs differ** | using a restricted re-search as a judge |

## Deliverables

```
forge-combo29/swarm/multipv/
  FINDINGS.md                  THE REPORT. Generated from the template, zero markers
  FINDINGS.template.md         source with [[markers]]; edit this, then run render.py
  STATUS.md                    this file
  scripts/
   00_build_and_pins.sh       build with g++ + LIBRARY_PATH, check the four honesty pins
   run_all.sh                 one-command reproduction, about 8 minutes
   multipv_lib.py             strict UCI harness (Threads 1, wait on bestmove, FEN gate)
   check_multipv.py           the property checks, plus a planted-fault selftest
   wire_control.py            mutates real captured blocks; 43 assertions, 0 blind
   audit.py                   properties 1-4 + the MultiPV 1 baseline + promotion attribution
   judge.py                   property 5's judge (deeper full-width search) and its control
   instability.py             A/B/C three-arm instability, setting vs depth
   agreement.py               the judge noise floor that retired the searchmoves judge
   fastpaths.py               property 6: book, drawn roots, precedence, searchmoves
   budget_stability.py        the same budget measurement three times; reports every repeat
   render.py                  template -> FINDINGS.md; fails if any marker survives
   lint_scripts.py            the 4 static checks CI raised against this seat's first push
  evidence/
   audit.json                 structural, controls, agreement, time pressure, promotion
   judge.json                 property 5 verdicts and the depth-only control
   instability.json           A/B/C arms
   agreement.json             judge noise floor
   fastpaths.json             book, drawn, precedence, restricted
   budget_stability.json      per-repeat budget counts, so the range is in the evidence
   pins.json                  the four honesty pins
   selftest.json              checker selftest counts, lifted from its own output
   wire_control.json          wire-control counts, lifted from its own output
   wire/                      raw stdout: pins.txt, selftest.txt, wire_control.txt, engine.md5
```

## Build

`/usr/bin/c++` on this image is clang 18 with a broken header path. Build with:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build build -j4
```

Pins on this build: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 —
**4/4**. Binary md5 `ecf97f8c071a91149c38dc1a193433f9`.

## What is deliberately NOT done

- **No patch.** The PV-length and promotion behaviours are the engine working as written; changing
  them is a design decision for the owner, not a defect repair. The report names the predicate a
  book/bail repair would need and leaves the patch to the drawn-root seat, which already has it with
  controls.
- **No Threads > 1 work.** Findings §3: nothing is reportable above Threads 1.
- **No clock play.** `go movetime` and `go nodes` only; the clock seat owns real budgets.
- **No claim about whether a standard GUI needs PV monotonicity.** The violation count and its
  mechanism are measured; the convention's force on clients is not something this seat can settle.

## The report is generated, so it cannot ship unrendered

`FINDINGS.md` is the file a reader opens and it is **generated**. The first push of this branch got
this wrong — the marker template was `FINDINGS.md` and the resolved text went to a second file
nobody would open, so 115 placeholders sat in the PR. The layout is now:

| file | role |
|---|---|
| `FINDINGS.template.md` | source a human edits; carries the counter markers; banner says it is not the report |
| `FINDINGS.md` | **the deliverable**; generated, zero markers, the one in the diff |

`render.py` has five checks, each with a planted fault in `--selftest`:

1. **missing** — a marker naming no counter
2. **residual** — any marker surviving into its own output; deletes the output rather than leave one
3. **type** — a dict/list resolved into prose
4. **suspicious** — 24 named denominator counters that must be nonzero, so a lookup returning 0 by
   default fails instead of printing `0` as a measurement
5. **reflow** — the markdown re-wrap cannot alter tables, fences, headings, lists or block quotes,
   and is idempotent

`render.py --check` fails when the committed `FINDINGS.md` is stale or contains a marker, and it is
the last stage of `run_all.sh`.

## Reproduction

```bash
cd forge-combo29
./swarm/multipv/scripts/00_build_and_pins.sh .   # must print PINS MATCH
./swarm/multipv/scripts/run_all.sh build/forge   # writes evidence/, renders FINDINGS.rendered.md
```

`run_all.sh` exits non-zero if any stage fails. The last two stages are `render.py` (fails if a
marker survives into its output, if a marker names no counter, or if a denominator resolves to 0)
and `render.py --check` (fails if the committed `FINDINGS.md` is stale or contains a marker).
