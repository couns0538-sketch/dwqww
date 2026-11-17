# Status

Branch `swarm/hashgap`, base `6b98f217`. Every run below is complete; nothing is
in flight and no result here is a partial.

## Builds used

| build | directory | macro | pins |
|---|---|---|---|
| default (shipped path) | `/home/ubuntu/build-hashgap` | `FORGE_TT_TRACE` undefined | 312,866 / 862,329 / 3,024,920 / perft 5 4,865,609 |
| instrumented | `/home/ubuntu/build-trace` | `-DFORGE_TT_TRACE=1` | identical to the above |

Compiler `/usr/bin/g++` (the workspace's `/usr/bin/c++` is clang 18 with a broken
header path; `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13` was set for both).
Both builds are `-O3 -march=x86-64-v4`, Threads 1 for every measured cell.

**The instrumented build reproduces all four pins bit-exactly.** That matters
because it means the results are a property of the engine, not of the counters.
The same source also builds with the macro off and still gives the pins, so the
patch is additive: a default build compiles the shipped code unchanged.

## Runs completed

| script | cells | status | evidence |
|---|---|---|---|
| `smoke.py` | 4 | PASS: determinism, counters move, `ttstats` sane | `evidence/` (console) |
| `grid.py` | 480 | 0 refused | `evidence/grid.jsonl` |
| `verify.py` | — | 5 predictions judged, 4 confirmed 1 refuted | `evidence/analysis/verify.txt` |
| `analyze.py` | — | divergence, counter separation, eviction depths | `evidence/analysis/analyze.txt` |
| `governor.py` | — | load vs evictions correlated | `evidence/analysis/governor.txt` |
| `mechanism.py` | 288 | 0 refused | `evidence/mechanism.jsonl` |
| `nullcontrol.py` | 576 | 0 refused; **null control 0/16 everywhere** | `evidence/nullcontrol.jsonl` |
| `depth_vs_nodes.py` | 448 | 0 refused | `evidence/depth_vs_nodes.jsonl` |
| `threshold.py` | 720 | 0 refused | `evidence/threshold.jsonl` |
| `score_size.py` | — | score deltas + wall-clock mapping | `evidence/analysis/score_size.txt` |
| `geometry.py` | 240 | 0 refused; **the control that split the question** | `evidence/geometry.jsonl` |
| `two_effects.py` | 144 | 0 refused; baseline vs load increment, with CIs and Fisher p | `evidence/two_effects.jsonl` |
| `cluster_remap.py` | 24 | 0 refused; remap measured on real keys | `evidence/cluster_remap.jsonl` |
| `controls.py` | 128 | 0 refused; same-cell 0/16 | `evidence/controls.jsonl` |

## Trustworthy

* The two-effects decomposition: baseline 11/24 at Hash 65, increment to 23/24 at
  Hash 16/32 with Fisher p = 0.00026.
* The null control (0/16 at every size, every budget).
* Cluster remap at ≥99.996% for a 1.02× step, with identical 37.8% cluster sharing.
* The practical table (1/40 move changes at 750k, 33/40 score changes).
* Reproducibility: identical cell in two fresh processes gives identical
  bestmove, score and node count, 0/16 at both 1M and 2M.

## Not trustworthy / not attempted

* **Which probe flips which cell.** Not isolated. Both the no-cutoff and no-move
  arms remain size-dependent, so the effect is distributed across the read path.
* **Per-position attribution** of a flip to the geometry baseline or the load
  increment. Only the aggregate split is measured.
* **Strength.** No games. Move-difference rates are not Elo.
* **Threads > 1, wall-clock searches, sizes above 256 MB or below 1 MB.**
* **The earlier report's exact positions**, which were never recorded. My counts
  use my own position sets.

## Method notes a successor should keep

* **One fresh process per cell, always.** `Clear Hash` is not a cold reset on this
  engine (24/25 positions differ from a fresh process); `ucinewgame` is. The
  driver here constructs a new process and never relies on either.
* **Never pipe a `go` command and close stdin.** EOF aborts the search and the
  engine reports a fabricated `bestmove`. `ucih.py` requires an `info depth` line
  and raises without one, so a fabricated answer cannot enter a result row.
* **A refused FEN raises.** `position` replies `info string invalid FEN` and the
  driver turns that into an exception rather than a result.
* **Include a null control.** The `no_read` arm is what licenses every other
  claim: with no probe read, all sizes agree. Without that row, "the table causes
  this" would be an inference from correlation.
* **Check that load and pressure are actually different variables.** The 64-vs-65
  pair is one megabyte apart and split the question into two components. Without
  it the report would have been a plausible correct-sounding collision story or a
  plausible correct-sounding refutation, and both would have been half wrong.
* **The piped-harness trap reproduces on demand.** `two_effects.py` was first
  written to pipe `go nodes 2000000` and close stdin; it **hung for the full
  300 s timeout** and had to be rewritten onto `ucih.py`. That is the same failure
  the earlier seat documented, met live rather than read about. The driver's
  requirement for an `info depth` line is what turns it into an error instead of a
  fabricated result.

## Reproducing

```bash
# default build (pins)
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake -S forge-combo29 -B build -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4

# instrumented build
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake -S forge-combo29 -B build-trace -DCMAKE_CXX_COMPILER=/usr/bin/g++ \
        -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-DFORGE_TT_TRACE=1"
cmake --build build-trace -j4

cd forge-combo29/swarm/hashgap/scripts
python3 smoke.py /path/to/build-trace/forge
python3 grid.py /path/to/build-trace/forge ../evidence/grid.jsonl
python3 verify.py ../evidence/grid.jsonl
python3 geometry.py /path/to/build-trace/forge ../evidence/geometry.jsonl \
        <positions file>            # the decisive control
python3 nullcontrol.py /path/to/build-trace/forge ../evidence/nullcontrol.jsonl <positions file>
```

`<positions file>` is any file of one FEN per line, `#` comments allowed. The runs
here used `forge-combo29/tests_r3fu_12/positions.txt` (10,000 game-walk positions)
and a disjoint slice at `scripts/positions_setB.txt`.

## One correction to my own work

An earlier version of `verify.py` tested the zero-displacement control as "both
tables displaced nothing at all", which is trivially true almost nowhere because
depth-0 qsearch churn is constant. It was rewritten to test "no displacement at
depth ≥ 1", which is the claim that matters, and the finding was unchanged. The
refuted prediction (P5, `hashfull`) is kept in `FINDINGS.md` rather than deleted.
