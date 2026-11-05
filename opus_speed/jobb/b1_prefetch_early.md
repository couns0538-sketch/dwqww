STATE: READY FOR TIMING
# B1 change 3: FORGE_SPD_PREFETCH_EARLY (child TT prefetch before make_move)

Worker b1tt (Job B part 1), started 09:23 PC clock. Status: checks (a), (b), (c) PASS at 09:45 (plain builds).
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

**(b) switch 1 node identity: PASS** (`lp_check.py run` net on and `--opt UseNNUE=false`, `compare` against the lock
plain runs `jobb\b1\lock\lp_on.json` / `lp_off.json`; log `jobb\b1\prefetch_early\s1\lp_pair.log`, 09:40:51-09:43:09):
- net on: bench d11/13/16/20/22 = 312866 / 862329 / 3024920 / 12389307 / 34048354 (= pins), perft 5 startpos 4865609,
  kiwipete 193690690, 8 bench FENs at `go depth 13` nodes + bestmove equal -> `NODE IDENTITY: ALL OK`.
- net off: 375354 / 907205 / 2448617 / 13573040 / 24506465 (= net-off pins), perft equal, 8 FENs equal -> ALL OK.

**(c1) early key is exact: PASS.** Assert build `jobb\b1\prefetch_early\assert_s1\forge.exe` (switch 1, no
`-DNDEBUG`; the assertion text `child_key == board.key()` is in that exe and not in the `-DNDEBUG` one: `grep -c` 1
vs 0): `bench 16` + the 8 bench FENs at `go depth 13` ran without an assertion failure, bench d16 = 3024920 (pin),
the 8 bestmoves equal the lock's; log `jobb\b1\prefetch_early\assert_s1\run_bench16_fens13.log`.

**(c2) coverage (verify copy, never shipped): 95 % of children get the early prefetch, 0 wrong keys.** Copy
`F:\ospd\src\b1_prefetch_early_count` (diff `jobb\b1\prefetch_early\verify_count.diff`, made by
`jobb\b1\tools\make_pf_count_copy.py`) counts, at both sites, children prefetched early, children prefetched late
(no early key: en-passant square on the board, or a double push next to an enemy pawn), and early keys that differ
from `board.key()` after `make_move`. Same run as (c1): early 3,502,511, late 185,238 (early share 0.9498),
early-key mismatches 0; bench d16 = 3024920; log `jobb\b1\prefetch_early\count_s1\run_bench16_fens13.log`.

**(c3) codegen (plain build, `jobb\b1\prefetch_early\s1\forge.dis` vs `jobb\b1\lock\forge.dis`): as designed.**
- Lock: at each site `call Board::make_move` then `prefetcht0` (qsearch 0x14001e2c2 -> 0x14001e2fb, the second
  qsearch copy 0x14001e5fe -> 0x14001e635; search 0x14001f79d -> 0x14001f7cf). The ProbCut `make_move` (0x1400211d8)
  has no prefetch.
- Switch 1: `call Board::key_after` -> `test %al,%al; je` -> cluster address (`mulq` cluster_count, `shl $6`, add
  clusters base) -> `prefetcht0` -> the move's bookkeeping (record_move inlined) -> `call Board::make_move` ->
  `test; jne` (skipped when the early key existed) -> late `prefetcht0` from `board.key()`. qsearch: 0x14001e39c,
  0x14001e3c8 (early), 0x14001e4e1 (make_move), 0x14001e50c (late); second copy 0x14001e840 / 0x14001e86c /
  0x14001e97e / 0x14001e9a9. search: 0x14001f92b / 0x14001f953 / 0x14001fa55 / 0x14001fa7a. ProbCut unchanged.
- In this plain (non-LTO) build `key_after` is an out-of-line call into board.cpp (127 instructions incl. the early
  exits); the LTO+PGO kit build can inline it. Not checked here: the kit exe's codegen.

## Summary of checks
| check | result | log |
|---|---|---|
| patch applies to a fresh lock copy, reproduces the tree | PASS | (diff -r empty) |
| (a) switch 0 vs lock plain, `cmp -l` | PASS: bytes 137, 138, 217, 218 only | `jobb\b1\prefetch_early\cmp_s0_vs_lock.txt` |
| (b) switch 1 lp_check net on, pins + 8 FENs | NODE IDENTITY: ALL OK | `jobb\b1\prefetch_early\s1\lp_pair.log` |
| (b) switch 1 lp_check net off | NODE IDENTITY: ALL OK | same |
| (c1) assert build: early key == real key at every node | no assertion; d16 = pin | `jobb\b1\prefetch_early\assert_s1\run_bench16_fens13.log` |
| (c2) coverage counter | early 94.98 %, mismatches 0 | `jobb\b1\prefetch_early\count_s1\run_bench16_fens13.log` |
| (c3) objdump | early prefetch before make_move, late one only as fallback | `jobb\b1\prefetch_early\s1\forge.dis` |

## Risks / open items
- Speed is UNPROVEN and may be zero or negative: the extra work per searched move is the `key_after` call (in the
  plain build an out-of-line call with a few table loads) and one more predictable branch; the gain exists only if
  TT misses are a cost at the child's probe. The bench and the gate use a 16 MB table, which is small next to the
  L3 cache, so the gain may be small (SPEED_LIST row 7: "likely < 1 %"). The coordinator's ABBA decides.
- Prefetch earlier also means a prefetched line can be evicted again before use when the move's bookkeeping is long
  (not measured).
- `key_after` duplicates `make_move`'s key formula. A later change to the key scheme (new key terms) must change both;
  the assert build and the counter above catch a mismatch, the `-DNDEBUG` build would only lose the prefetch's
  benefit (a wrong cluster prefetched), never the node identity.
- Stacking with FORGE_SPD_TT_NOTLS: disjoint lines (board.hpp / board.cpp / search.cpp prefetch sites vs the TT class
  and TT call sites); not built together here.
- Not run here (coordinator / crew): kit pc1 = pc2 build, 12k-FEN identity (`fens_12k_v2.txt`), ABBA.
