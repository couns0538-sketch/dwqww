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
