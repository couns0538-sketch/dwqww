# Defensive bad-capture capacity patch

Prepared 2026-10-24 UTC for root-owned qualification; no native command was run
by the buffer agent. Exact patch base:
`f4911f2709bd5ae7e5fca7aea30aac5d87314a05` (h256_e12 lock).

## Finding and containment argument

Status: **UNCONFIRMED native overflow; fixed defensively at source level.**

`MovePicker::generate_captures()` copies the noisy `MoveList` into `moves_` and
sets `count_` to that list's size. `GoodCaptures` advances `index_` exactly once
per `pick_best()` call and can append each selected move to `bad_captures_` at
most once. This stage is entered once per picker; later quiet generation does
not append deferred captures. Therefore, assuming the existing MoveList
producer contract, `bad_count_ <= original noisy count <= MoveList::Capacity`.
The old 64-element deferred array did not express that full containment.

The production change makes that array `MoveList::Capacity` and adds a
compile-time assertion of the containment contract beside the private member.
Restoring the old size with the assertion retained fails compilation; this
does not reproduce an out-of-bounds write or establish legal reachability.
There are no new runtime gates, test hooks, pruning rules or ordering changes.
The array has 192 extra Move slots (768 bytes with the existing four-byte Move).

## New CTest

`forge_bad_capture_tests` calls the existing public Board and Searcher APIs.
It records parser acceptance and, if accepted, the actual noisy count,
`!Board::see_ge(move,0)` count, legal SEE-losing count, promotion count and
in-check state. It runs an ordinary depth-3 single-thread Hash-16 search and
checks legal best move/PV output for each accepted input. A rejected supplied
QA FEN is reported with its normal parser error and is not bypassed.

Fixed supplied FENs (unchanged):

1. `1Q1bq3/pr1Q1p1R/KQ1n1Q1b/1p1Q1n1Q/BQ1p1Q1r/1p1QpN2/1k1pR2p/5NB1 w - - 0 1`
2. `1krQ2b1/8/Q2pQnR1/p1Q3b1/Q1n2QrQ/p1QQpKp1/q1ppR2p/1NB1BN2 w - - 0 1`

The three ordinary controls come directly from existing Forge tests:

- Poisoned pawn: `3qk3/8/8/3p4/8/8/8/3QK3 w - - 0 1`. Its only noisy move
  `d1d5` is legal and SEE-losing. A normal root `search_moves` restriction
  requires that move to remain available after the deferred-capture stage.
- White promotions: `1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1`.
- Black promotions: `4k3/8/8/8/8/8/p7/1R2K3 b - - 0 1`.

Each promotion control has eight generated noisy promotions: four quiet and
four captures. Both controls require an actual legal SEE-losing move and a
non-check main-search starting node. The test does not require an overflow,
claim to saturate capacity or count a compile-time contract as native proof.

## Scope and pending qualification

The standalone patch adds only `src/search.cpp`, `tests/bad_capture_tests.cpp`,
the CMake target/test registration and an original `IDEA_SOURCE.md`. It imports
neither the old partial-iteration guard nor NNUE changes. No network, match,
trainer, timing claim or Elo claim is included. No native overrun checker,
equivalent trigger, input generator, fuzzer or parser bypass was attempted.

Root owns builds and qualification. Every new engine build must first pass
all-options-OFF bench 11 = 308972 before any other engine test. Still pending:
five-depth OFF identity (308972/745494/2460422/11901452/31111774), both requested
perft5 values, full CTest with exact FAIL lines, actual fixed-FEN census,
ASan/UBSan full suite and bench13, and assertions-profile/flags-ON qualification.
The expected existing suite state must be reported as one failing
`forge_tests` CTest with four FAIL lines, if reproduced, rather than four
failing CTests. With Python tests available, this new registration changes
the total CTest count from 14 to 15.
