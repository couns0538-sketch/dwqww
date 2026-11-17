# Swarm seat 69 — determinism of fixed-budget searches

Branch `for-fable-and-opus/swarm-69`, base commit `6b98f217`.
Work folder `forge-combo29/swarm/69/`.

## What this seat measures

The properties a harness author relies on when they pin a search by node count or depth
and treat the answer as a property of the position. Every result below is about
`Threads 1`: above one thread this engine does not produce a fixed answer at all, which
an earlier seat already established and this seat does not re-derive.

## The build

Both builds are Release, GCC 13.3, `-march=x86-64-v4`, built in separate worktrees outside
the repository:

| build | source | exe |
|---|---|---|
| base | commit `6b98f217` | `~/builds/base-build/forge` |
| PC | `6b98f217` + the `pc_r15.patch` text from `soak_all/FABLE_TO_swarm_5.md` | `~/builds/pc-build/forge` |

The PC patch was extracted from the handoff doc between its fence lines and its sha256 must
be `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a` before use; it was
checked and matches.

### Honesty pins (both builds, default options, fresh process per line)

| build | bench 11 | bench 13 | bench 16 | go perft 5 |
|---|---|---|---|---|
| base | 312,866 | 862,329 | 3,024,920 | 4,865,609 |
| PC | 312,866 | 862,329 | 3,024,920 | 4,865,609 |

All four match the documented pins on both builds. `id name` on both:
`Chess Engine Forge 6.4.24 candidate`.

## Two harness defects found before any measurement

### The piped-EOF trap

`printf 'uci\nisready\nposition startpos\ngo depth 8\n' | forge` prints **zero**
`info depth` lines and answers `bestmove a2a3`. The engine reads EOF while the search is
running, aborts, and publishes a fabricated legal move. That answer is perfectly
reproducible, so a harness built on a pipe would report a stable measurement of a search
that never happened. This is the same class of defect as a silently refused FEN.

Every number in this report therefore comes from an interactive driver that keeps stdin
open and blocks on `bestmove` with a timeout (`ucih.py`).

### Where the `invalid FEN` diagnostic appears

Confirmed by planting both cases (`fault_proof.py`):

* with `isready` after `position`, the diagnostic lands in the **position reply**, before `readyok`;
* with no `isready` between them, it lands in the **`go` output**, ahead of the first `info depth`.

Both streams are scanned. A FEN that python-chess rejects is never sent at all.

The dangerous middle class is a FEN python-chess calls **valid** and the engine refuses:
`4k3/8/8/8/8/8/8/R3K2R w K - 0 0` (fullmove 0). python-chess accepts it, the engine answers
`invalid FEN: invalid FEN fields`, and without a scan the harness would record the node count
of the *previous* board. That exact FEN is the F2 fault in the proof file.

## Fault-planting proof

`fault_proof.py` — 7 checks, 7 caught their planted fault, 0 uncaught:

| check | planted fault | caught |
|---|---|---|
| F1 | FEN python-chess rejects | before contact with the engine |
| F2a | FEN engine refuses, `isready` after `position` | position reply |
| F2b | FEN engine refuses, no `isready` | `go` output |
| F3a | piped-EOF truncation | reproduced: 0 info lines, `bestmove a2a3` |
| F3b | driver immune to it | 8 info lines, `bestmove d2d4` |
| F4a | two genuinely different cells | compare as different |
| F4b | two identical cells (control) | compare as identical |

The environment wrappers were proved to bite separately (`job1/wrapper_proof.py`, 9 checks,
0 failed): `taskset` really pins the core, `nice -n 19` really changes the nice value,
`ulimit -v 65536` really kills a `Hash 512` allocation while `Hash 16` fits, and
`ulimit -v 4096` kills the engine outright. Without that, every "0 differing" row under a
resource limit would be vacuous.

## The matrix: what varies and what does not

Budgets `go nodes 50000` and `go depth 12`, `Threads 1`, `Hash 16`, base build, 40 positions
(the first 40 of set O). A cell is (nodes, bestmove, score, depth); a variant "differs" when
any of the four moves.

| input changed | positions differing, `go nodes 50000` | positions differing, `go depth 12` |
|---|---|---|
| working directory (`/tmp/...`, `/`) | 0 / 40 | 0 / 40 |
| `LANG`/`LC_ALL`/`LC_NUMERIC` + `TZ` | 0 / 40 | 0 / 40 |
| environment variable ORDER + `TZ` | 0 / 40 | 0 / 40 |
| CPU affinity (`taskset -c 0`, `-c 1`, `-c 2`) | 0 / 40 | 0 / 40 |
| `nice -n 19` | 0 / 40 | 0 / 40 |
| `ulimit -v` 2 GB | 0 / 40 | 0 / 40 |
| `ulimit -v` 64 MB (memory pressure) | 0 / 40 | 0 / 40 |
| `ulimit -s` 8 MB (stack) | 0 / 40 | 0 / 40 |
| `ulimit -n` 256 (file descriptors) | 0 / 40 | 0 / 40 |

**None of the nine machine-environment inputs moves a fixed-budget answer.** The 0/40 rows
are real cells, not silent matches: every variant reported the same non-trivial node counts
and bestmoves as the reference, and the wrapper proof above shows each wrapper was in force.

The invariance is not a base-build artifact: locale + TZ, `taskset -c 1`, `nice -n 19` and
`ulimit -v 65536` each give **0 / 20** differing cells on the **PC** build too
(`job1/pc_env_check.raw.txt`).

## Memory pressure

One cap is a point, not a boundary, so `ulimit -v` was stepped from 1 GB down to 16 MB
(`job2_memory_pressure.py`, 12 positions, `go nodes 50000`).

| cap | `Hash 16` | `Hash 256` |
|---|---|---|
| 1 GB, 256 MB, 128 MB, 96 MB, 80 MB, 64 MB | searched, **0 / 12 differ** | 1 GB only: searched, 0 / 12 |
| 48 MB … 16 MB | **died on 12 / 12** | died on 12 / 12 |

Bisected cliff:

| Hash | largest cap that DIES | smallest cap that WORKS |
|---|---|---|
| 16 | 59 MB | **60 MB**, and the answer is bit-identical to no cap |
| 256 | 290 MB | **300 MB**, likewise identical |

So the failure mode is a clean death, not a quiet change. Above the cliff the answer does
not move at all; below it there is no answer. **There is no band where memory pressure
silently changes a fixed-budget result.** That is the safe shape for a harness — but it
also means a harness must treat "engine exited without `bestmove`" as a hard failure and
never as a missing cell, because an out-of-memory kill looks like a short read.

The cliff is roughly the table size plus ~40 MB (16 MB table -> 60 MB; 256 MB table ->
300 MB), so a harness that raises Hash must raise the memory cap with it or it will see
every cell die.


## Hash size

`Threads 1`, base build, **fresh process per cell**, first 24–40 positions of set O,
compared against `Hash 16` on the same position and budget.

| budget | Hash 16 vs 64 | Hash 64 vs 256 | Hash 16 vs 256 | Hash 16 vs 1 |
|---|---|---|---|---|
| `go nodes 50000` | 0 / 24 | 0 / 24 | 0 / 24 | 11 / 24 |
| `go nodes 200000` | 2 / 24 | 0 / 24 | 2 / 24 | 24 / 24 |
| `go nodes 500000` | 17 / 24 | 0 / 24 | 17 / 24 | 24 / 24 |
| `go nodes 1000000` | 24 / 24 | 9 / 24 | 24 / 24 | 24 / 24 |
| `go nodes 2000000` (40 positions) | **40 / 40** | — | — | — |

So the honest answer to "is `Hash 16` vs `Hash 64` identical at a fixed node budget" is:
**only below roughly 200,000 nodes.** At 500,000 it moves 17 of 24 positions; at
1,000,000 it moves all 24; at 2,000,000 it moves all 40. `Hash 1` is different even at
50,000 nodes.

Of 178 differing cells in the sweep, **15 also moved the bestmove** and **13 differ by
exactly one node**. A one-node difference matters because the count is what a harness
divides by or compares, and the bestmove changes are what a strength comparison sees.

A warm process differs from a fresh process at **every** Hash size (40 / 40, both
budgets), so table size does not rescue the reuse trap: warm-16 vs fresh-16 is 40 / 40
apart. The two traps are separate and both have to be avoided.

### What this means for a harness

1. Start a **fresh process per cell**. Nothing else makes a reused process agree with a
   fresh one — not `Clear Hash`, not a bigger table.
2. If a process must be reused, send **`ucinewgame`** before every `position`, never
   `Clear Hash`. `ucinewgame` reproduced the fresh answer in 25 of 25 cells; `Clear Hash`
   in 1 of 25.
3. Pin **Hash** and do not change it between compared runs, above all above ~200,000
   nodes. "Bigger Hash is just faster" is false in this engine at large budgets.
4. Treat a one-node difference as a real difference. It is 13 of the 178 cells here.

## Second build as the available proxy for a second machine

A second build of the identical source, in a different directory, with `-g` added,
produces a different binary (4,869,512 vs 794,944 bytes) and **the same answers**:
0 / 40 differing at `go nodes 50000` and at `go depth 12`, and it passes all three bench
pins. No dependence on build address, allocation order, an uninitialised read or a
timestamp was detected.

This is a proxy and not a second machine. A different CPU, a different `-march`, or a
different compiler is **untested**; see the limits section of `FINDINGS.md`.

## Transposition-table initial state

`go nodes 50000`, `Threads 1`, `Hash 16`, base build, 5 positions, 5 trials each, compared
against a fresh-process cell for the same position.

| reset applied before each search | cells differing from a fresh process |
|---|---|
| `ucinewgame` | **0 / 25** |
| `ucinewgame` + `Clear Hash` | **0 / 25** |
| `Clear Hash` alone | **24 / 25** |
| nothing | **24 / 25** |

This verifies the brief's claim and sharpens it. Read off the source:

* `ucinewgame` calls `Searcher::clear()` (`src/search.cpp:2679`): it clears the table **and**
  every worker's butterfly/continuation/capture history, correction history and search stack.
* `Clear Hash` calls `Searcher::clear_hash()` (`src/search.cpp:2667`): it clears the table and
  then `Worker::clear_caches()`, which is **only** `evaluator_.clear()`
  (`include/forge/search.hpp:452`). The histories survive.

So `Clear Hash` is not a cold reset, exactly as documented — and the histories are strong
enough that the answer moves in 24 of 25 cells.

### The carried state is reproducible, not noise

Three independent processes replayed the same command sequence and produced **identical**
cells (3 of 3 processes identical, for `Clear Hash`, nothing, and `ucinewgame`). Inside one
process the two replays differed (`replay1 == replay2`: False, False, False for `Clear Hash`;
True, True, True for `ucinewgame`). The same position searched four times in a row in one
process:

| reset | four consecutive cells on one position | stable |
|---|---|---|
| `ucinewgame` | 37135 `f1e2` cp 72 d13, repeated 4× | yes |
| `Clear Hash` | 37135 cp 72, 41762 cp 37, 39116 cp 44, 30366 cp 35 | no |
| nothing | 37135 cp 72, 35939 cp 44, 22411 cp 38, 44706 cp 35 | no |

The drift is deterministic and directional — the histories keep accumulating from the
position that was just searched. A harness that reuses a process and calls `Clear Hash`
will get a *stable-looking but wrong* node count, and the error grows with how many searches
the process has already run.

## Cross-build node counts on non-lone-king roots

`go depth 12`, `Threads 1`, `Hash 16`, base vs PC, same 200 positions of set O.
Set O has **0 lone-king roots of 200**, so all 200 are eligible.

| set | node counts differ | bestmoves differ | any field differs |
|---|---|---|---|
| O, non-lone-king, n = 200 | **0 / 200** | **0 / 200** | 0 / 200 |
| G, non-lone-king, n = 341 | **0 / 341** | **0 / 341** | — |
| G, lone-king (control), n = 12 | **12 / 12** | 4 / 12 | — |

Repeated at `go nodes 200000` to show the result is not a `go depth` artifact:
0 / 200 and 0 / 341 non-lone-king differ, 12 / 12 lone-king control differ.

So the cross-build divergence is confined to lone-king roots **in node counts as much as
in bestmoves**, and the predicate separates the two classes completely (0 of 541 outside
the class, 12 of 12 inside it). The sizes are large when it happens: +161,907 nodes on
`8/6qk/8/8/8/1p4p1/4K3/8 b - - 0 1`, and the same FEN is -94,836 at `go nodes 200000`.

The two builds answer a fixed-budget non-lone-king search identically, so a harness that
compares node counts between them on ordinary positions is comparing like with like.

## Four answers requested after the first report

**1. The piped fabrication is per-position, not one fixed move.** 13 distinct fabricated
moves across 60 positions; 0 of 60 equal the real answer; **all 60 are legal**, so a
legality check accepts 60 / 60. A piped run is *not* detectable by its move. It is
detectable only by `info depth` lines == 0 (60 / 60). The move is also budget-independent:
the same 6 fabrications for the same 20 positions at depth 4, 8, 12 and at 50k and 500k
nodes. **The fabrication is a function of the position alone.**

**2. The `Clear Hash` drift does change the best move.** 70 / 200 positions at
`go nodes 50000` — not a score nuisance. Score differs 195 / 200, depth 132 / 200, and 129
differ in nodes with the move unchanged. Budget-stable: 12 / 40 at 50k, 11 / 40 at 500k on
a 40-position prefix. `ucinewgame`: 0 / 200 on every field.

**3. Hash 128 vs 256 first matters at `go nodes 1,000,000`.** 0 / 24 at 50k, 200k and 500k;
2 / 24 at 1M; 15 / 24 at 2M; 24 / 24 at 4M. 64 vs 128 behaves identically. **The correction
this produced: Hash 64 vs 256 is 0 / 24 at 500,000** — so the earlier 17 / 24 at 500k was
Hash 16 being too small, not table growth. The practical floor at 500k nodes is ~64 MB, not
~16 MB.

**4. History does not leak.** A repetition-laden position followed by another search gives
the identical cell with or without `ucinewgame` (4 / 4 sequences). The repetition state is
rebuilt from the `position` command each time.

### This produced one correction to an earlier finding of mine

69-F8b said `position fen` and `position startpos moves` were interchangeable (0 / 6). They
are not. They agree at 0 and 1 repetitions (0 / 4 cells) and **diverge at 2 and 3
repetitions (4 / 4 cells)** — a FEN cannot carry repetition history and a move list can.
Job 3c missed it because its 40-ply games contained no threefold. My test could not see the
difference, so the claim was too wide; it is corrected in `FINDINGS.md` as 69-F8c.

The base build's drawn-root bail is reachable this way: on a threefold root reached by move
list, base answers `0 nodes, cp 0, a2a3` and PC answers `34,047 nodes, cp 22, e2e4`. Via
`position fen` both answer `56,720 / e2e4 / cp 30`. A harness comparing the two builds on
game positions delivered by move list would see a divergence that is not there in the FEN
form.

## One table: what varies and what does not

Fixed-budget answer = (nodes, bestmove, score, depth). `Threads 1` throughout.

| input | does it change a fixed-budget answer? | denominator |
|---|---|---|
| working directory | **no** | 0 / 40, two budgets |
| `LANG` / `LC_ALL` / `LC_NUMERIC` / `TZ` | **no** | 0 / 40, two budgets |
| environment variable order | **no** | 0 / 40, two budgets |
| CPU affinity (cores 0, 1, 2) | **no** | 0 / 40 each, two budgets |
| `nice -n 19` | **no** | 0 / 40, two budgets |
| `ulimit -v` 2 GB | **no** | 0 / 40, two budgets |
| `ulimit -v` 64 MB (memory pressure) | **no** | 0 / 40, two budgets |
| `ulimit -v` down to the cliff | **no** — it dies instead | 0 / 12 at every cap that ran; 12 / 12 deaths below 60 MB |
| `ulimit -s` 8 MB | **no** | 0 / 40, two budgets |
| `ulimit -n` 256 | **no** | 0 / 40, two budgets |
| a second build of the same source | **no** | 0 / 40, two budgets |
| base build vs PC build, non-lone-king | **no** | 0 / 200 (set O), 0 / 341 (set G) |
| **process reuse + `Clear Hash`** | **YES** | 24 / 25 cells |
| **process reuse + no reset** | **YES** | 24 / 25 cells |
| **process reuse + `ucinewgame`** | no | 0 / 25 (fen), 0 / 6 (game walk) |
| **`position fen` vs `position startpos moves`** | **YES, once a threefold is in the move list** | 0 / 4 at 0–1 repetitions, 4 / 4 at 2–3 |
| **Hash 16 vs 64, ≥ 200k nodes** | **YES** | 17 / 24 at 500k, 24 / 24 at 1M, 40 / 40 at 2M |
| **Hash 16 vs 1, any budget** | **YES** | 11 / 24 at 50k, 24 / 24 above |
| **PC build, lone-king root** | **YES** | 12 / 12 |
| **piped stdin (EOF during search)** | **YES** | 0 info lines, per-position fabricated bestmove (13 distinct / 60), all legal |
| **reuse + `Clear Hash`, bestmove** | **YES** | 70 / 200 at 50k nodes |
| **reuse + `ucinewgame`** | no | 0 / 200 on every field |
| **Hash 128 vs 256** | **YES at ≥1M** | 0 / 24 at 500k, 2 / 24 at 1M, 15 / 24 at 2M, 24 / 24 at 4M |
| **Hash 64 vs 256 at 500k** | **no** | 0 / 24 (the earlier 17 / 24 was Hash 16 being too small) |
| **repetition history across `ucinewgame`** | **no leak** | 4 / 4 sequences identical |

