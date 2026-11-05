# B1 change 3: FORGE_SPD_PREFETCH_EARLY (child TT prefetch before make_move)

Worker b1tt (Job B part 1), started 09:23 PC clock. Status: IN PROGRESS (checks filled in as they land).
Source idea: own R7 option R7PrefetchEarly (SPEED_LIST row 7, "unknown, likely < 1 %, re-judge by ABBA"); the
code here is written fresh for the lock tree. Patch: `opus_speed/patches/b1_prefetch_early.patch` (against the lock
source, `patch -p1` inside a fresh lock copy). Edited tree: `F:\ospd\src\b1_prefetch_early`. Builds and logs:
`F:\ospd\jobb\b1\prefetch_early\`. No timing was done and no nps number is reported; the coordinator's ABBA decides.

## Design (own words)
The lock prefetches the child's TT cluster right after `make_move` (qsearch lock :847, main search :1126), from
`board.key()`. The child probes the table a short while later (after its stop / draw / mate-distance checks), so the
prefetch has little time to complete. With the switch at 1 the prefetch is issued before the move's bookkeeping
(`ss->current_move`, `record_move` = NNUE dirty pieces, `make_move` itself), from a child key computed without
making the move:
- `Board::key_after(move, key)` (new, board.cpp, uses the same `Z` table, `piece_key` and `CastlingMasks` as
  `make_move`) xors the same terms `make_move` applies: captured piece on the to-square (`piece_key(sq, Empty)` is 0,
  so a non-capture adds nothing), moving piece off the from-square, moving or promoted piece onto the to-square, the
  rook's two squares for a castle, old and new castling-rights keys, the side key.
- The only terms that are not cheap are the en-passant ones, which need `has_legal_en_passant_capture()` on the
  current or the child board. `key_after` returns false (no early key) when the current position has an
  en-passant square (that also covers every en-passant capture, and the move flag is checked too), and for a double
  push when an enemy pawn attacks the passed square (then the child may get an en-passant term). A double push with
  no enemy pawn next to the passed square gets no en-passant term in `make_move` (its candidate test is the same
  `attacks::pawn & enemy pawns`), so that key is exact.
- Search: `early_key = board.key_after(move, child_key); if (early_key) prefetch(child_key);` before the move's
  bookkeeping, and after `make_move` the lock's prefetch runs only when there was no early key. So every child is
  prefetched exactly once, early when the key is cheap and exact, late (as in the lock) otherwise.
- `assert(!early_key || child_key == board.key())` right after `make_move`: compiled out under `-DNDEBUG`, active in
  the assert build, where it checks the early key against the real one at every node.
- Only the two prefetch sites of the lock; null move and ProbCut have no prefetch in the lock and get none here.

## Lines touched (all inside `#if FORGE_SPD_PREFETCH_EARLY`, lock text verbatim under `#else`; patch adds lines only)
- `include/forge/board.hpp`: switch guard after the includes; `key_after` declaration before `make_move`.
- `src/board.cpp`: `Board::key_after` definition before `Board::make_move` (lock :719).
- `src/search.cpp`: qsearch before lock :840 (early prefetch) and lock :847 (late prefetch only without an early
  key); main search before lock :1119 and lock :1126 (same).
- Diff size: +59 / -0 lines.

## Why node-identical
A prefetch is a hint: it reads nothing into the program's state and writes nothing. The child key is computed by a
const member function into a local; no board, search-stack or TT state changes. The only other difference is which
cache line is prefetched and when. So the searched tree cannot change; the pins and the FEN runs below check it.

## Checks
Builds: the job's plain line via `F:\ospd\jobb\b1\tools\plain_build.sh` (assert build: `nodebug_build.sh`, the same
line without `-DNDEBUG`), g++ 15.2 ucrt64, each run inside its source copy; no warnings; 0 `vfmadd` in each exe.

| exe | sha256 | what |
|---|---|---|
| `jobb\b1\lock\forge.exe` | f205cbc3... | plain build of the lock (reference) |
| `jobb\b1\prefetch_early\s0\forge.exe` | ca8583a6... | b1_prefetch_early, switch 0 (default) |
| `jobb\b1\prefetch_early\s1\forge.exe` | d11a5c22... | `-DFORGE_SPD_PREFETCH_EARLY=1` (the candidate) |
| `jobb\b1\prefetch_early\assert_s1\forge.exe` | d103db07... | switch 1, no `-DNDEBUG` (early key == real key asserted) |
| `jobb\b1\prefetch_early\count_s1\forge.exe` | 393d39ab... | counter verify copy, switch 1 |

Patch `opus_speed/patches/b1_prefetch_early.patch` sha256 e003b8b9...: applied with `patch -p1` to a fresh lock copy
(`F:\ospd\src\b1_prefetch_early_ptest`) it reproduces `F:\ospd\src\b1_prefetch_early` exactly (`diff -r` empty).
Switch default line `#define FORGE_SPD_PREFETCH_EARLY 0`: one line, `include/forge/board.hpp` only.

**(a) switch 0 = lock: PASS.** `cmp -l lock\forge.exe prefetch_early\s0\forge.exe` differs in 4 bytes only: 137, 138
(PE link timestamp), 217, 218 (PE checksum); log `jobb\b1\prefetch_early\cmp_s0_vs_lock.txt`.
