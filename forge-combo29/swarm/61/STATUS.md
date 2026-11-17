# swarm/61 — verification seat, live status

## Standing rules I am enforcing in every script here

1. `Threads 1`, `Hash 16` on every search; no clock search with a zero increment.
2. Every FEN and every move validated with python-chess **before** it is sent.
3. `info string invalid FEN` scanned in **both** the position reply and the `go` output, before
   any `info depth` is parsed. Any sighting aborts the run.
4. Waits are on `bestmove` with a wall timeout; never on an `info depth` line.
5. `go infinite` is always followed by `stop`.
6. Every check prints its row count as a literal beside its verdict.
7. Every script plants a fault and must exit nonzero on it.

## The FEN diagnostic — measured here, not taken on trust

`fen_location.py` (3 cases, all measured on my own base build):

| case | in position reply | in go output | emitted |
|---|---|---|---|
| A: `position` then `isready` | **yes** | no | yes |
| B: `position` then `go`, no isready | yes | no | yes |
| C: fresh session, first position | **yes** | no | yes |

`rows examined: 3`. Conclusions:

- The corrected clause holds: the diagnostic is emitted in every case, including a fresh session.
- In all three it precedes the first `info depth` line.
- A reader that scans only post-`readyok` output **misses case A** — measured, not argued.

So the operative rule is "scan the whole window from `position` through `bestmove`", and a harness
that reads one named reply is the failure mode.

## Built and verified

- Base `6b98f217`, GCC 13.3.0, `FORGE_MARCH=x86-64-v4` (host has avx512f+bmi2).
  Note: `/usr/bin/c++` is clang-18 here and its link step cannot find `-lstdc++`; CMake must be
  configured with `-DCMAKE_CXX_COMPILER=g++`.
- Honesty pins re-derived on that build: **312866 / 862329 / 3024920 / perft 5 4865609** — all four match.

## Findings so far

1. **Two source harnesses carry the FEN-refusal bug the brief describes.** `swarm/19`'s prefetch
   harness (`checks/prefetchreal/run.py`) sends `position` then `isready` then `go`, so it is in
   case A: a refused FEN is consumed silently by the `isready` drain and the search reports a normal
   answer on the *previous* position. `swarm/23`'s `final_recheck.py` has the same shape. Neither
   validates its FENs with python-chess. This does not by itself falsify their numbers — but their
   row counts are only as good as their position lists.
2. `FORGE_FIX_ROOT_DRAWN` (the r15 drawn-root repair) is **not committed as source anywhere I can
   reach**: it is referenced by seats 01 and 23 but the patch text lives in a handoff file that is
   not in the branches. I cannot build a genuine PC r15 tree, so I will not report a PC column as if
   I had.
3. `-DFORGE_MATE_ALPHA_GUARD=1` alone does **not** repair the drawn root. A build with only that
   flag is byte-identical to base (sha256 `e06310ec…`), which is a useful negative control and a trap
   for anyone who reads "PC build" as "the fix build".

## In progress

Re-deriving the prefetch 9.80%, PC20 per-node 6.4%, PC20 node saving 8.7%, and the drawn-root rows
from committed raw data and from my own measurements.
