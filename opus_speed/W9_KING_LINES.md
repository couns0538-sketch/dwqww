# W9: FORGE_SPD_KING_LINES - brief step 4 (one new bit-exact hot-path switch), 2026-11-05 17:45-18:31 PC clock

The switch was written by worker jobd (fable), from its notes `F:\ospd\w9\NOTES.md`. The main session copied them
here after the worker's runs, because the workers ran out of their model credits before handing back. The
on-top-of-(d) result was read from that pack's own `bitexact.log`.

Status: speed is UNPROVEN (no timing run here; QA times it). This is **not a lock** and makes no Elo claim.

## Idea
The lock answers two questions per move:
- `Board::is_legal` for every move the picker returns, with a full attacked-square scan of its own king (three table
  reads plus two slider lookups with the post-move occupancy);
- `Board::gives_check` for every legal move, with a direct-attack lookup plus two slider lookups from the enemy king,
  all with per-move occupancy edits.

Both answers depend on facts of the position that stay the same across all of its moves:
- **pinned**: pieces of the side to move that alone block an enemy slider's line to their own king;
- **discovered-check candidates**: its pieces that alone block one of its own sliders' lines to the enemy king;
- **check squares**: the squares from which each piece type checks the enemy king.

With the switch on:
- The board computes these facts once per position, on first use.
- It keeps them across make / unmake inside `Undo` / `NullUndo`.
- It answers normal moves from them:
  - a non-king, non-en-passant move while not in check is legal iff the mover is not pinned or stays on the line
    through its king;
  - a normal move gives check iff its destination is a check square of the mover's type, or the mover is a candidate
    that leaves its line.
- En passant, castling, promotions, king moves and positions in check keep the lock's full tests verbatim.

So every answer equals the lock's, and the search visits the same nodes. Idea source: own code; the pin / blocker
technique is textbook and the lock's own `see_ge` already uses it. No code from other engines.

## Files
| file | md5 | what |
|---|---|---|
| `patches/b4_king_lines_after_w8.patch` | 21ecde2e | trial_w8 -> w9dev: `include/forge/board.hpp` (switch default + `KingLines` + members in `Undo` / `NullUndo` / `Board`), `src/board.cpp` (`is_legal`, `gives_check` under `#if` with the lock text under `#else`; `single_blockers`, `refresh_king_lines`; snapshot / invalidate / restore in make / unmake / null move; invalidation in `set_fen`); 172 added, 0 removed |
| `patches/trial_w9.patch` | ddefd1fe | lock -> `F:\ospd\src\trial_w9` (make_stack: 9 switches default 0, 0 lock lines removed) |
| `w9/kl_diff.cpp` | d9050912 | differential harness (own code): a restatement of the lock's `is_legal` / `gives_check` rules through public accessors, run against the switched board |
| `w9/kl_diff_kl1_12k.txt`, `w9/kl_diff_bundled_12k.txt` | c9245871 (both) | harness results, switch alone / with bundle (d)'s board defines |

**Update 2026-11-05 20:06 PC clock (leftover job 3b, CR NIT = self-review K3; comment only):**
- Three comment lines now sit above the `is_legal` declaration in `include/forge/board.hpp` of both `F:\ospd\src\trial_w9`
  and `F:\ospd\src\w9dev`. They say the KING_LINES fast path is exact only for already pseudo-legal moves.
- Both patches were regenerated with the recipe that reproduced the old files byte for byte first:
  - `trial_w9.patch`: ddefd1fe -> 8bf44bab;
  - `b4_king_lines_after_w8.patch`: 21ecde2e -> d680f9bf.
- The old and new patches differ only in the comment, the hunk offsets and one timestamp line. `patch -p1 -F0` onto a
  fresh lock copy (and trial_w8.patch + b4) equals the trial_w9 tree (`F:\ospd\tmp\k3proof_20261105-200606`).
- No code changed; nothing was rebuilt, retimed or locked. The packs above (bde33433, 5f5f4ece) and the md5 column
  are from the source before the comment.

## Results
- **Switch-0 identity** (18:00:37-18:01:08): `build_variants lp_v1` of `F:\ospd\src\trial_w9` gives sha256
  `fd3a51903e73dc1fa20263f1dcc7a4eec506592e9f25e50b8f8739ca36873072`, the lock FD3A5190 byte for byte. Quick pins OK.
- **Pack `w9_king_lines_alone`** (18:01:08-18:06:10; `-Define FORGE_SPD_KING_LINES=1`): exe sha256
  `bde33433295ed7059a06f1cbeb4a399ffa72ec03fd8dbbed5183a34fa5b566fe` (pc1 = pc2).
  - **Pins PASS**: L1 net on + off d11/13/16/20/22, 10 / 10; L2 perft 5 startpos + kiwipete, 2 / 2.
  - L3 2,000 / 2,000 FENs identical.
  - L4 MSVC ASan 2587341 = ref and UBSan 3024920 = cand d16, 0 reports.
  - VERDICT BIT-EXACT (L1-L4, quick L3).
- **Pack `w9_king_lines_on_d`** (18:26:38-18:30:37): bundle (d) (five, ZMM dropped, + T12B_BADCAP + NNUE_AVX512) +
  KING_LINES, exe sha256 `5f5f4ece24f6d6ca7a34f5c9c4a158e1270da35688e284b85a3a591e264cf1b5` (pc1 = pc2).
  - **Pins PASS**: L1 10 / 10, L2 2 / 2.
  - L3 2,000 / 2,000; L4 ASan + UBSan PASS.
  - VERDICT BIT-EXACT (L1-L4, quick L3).
- Both packs: speed_pack reports `verified: lock + trial_w9.patch = the built source`.

## Own checks of the worker (before the kit builds)
- **Switch 0:** `g++ -E -P` of all seven other units is identical between trial_w8 and w9dev.
- **Syntax:** `g++ -fsyntax-only` is clean for the switch alone and with bundle (d)'s defines.
- **Differential harness** over `data/fens_12k_v2.txt`. For each FEN it checked the parent position, every child, a
  grandchild, the parent again after unmake, the null-move child, and the parent after the null move.
  - Scale: 996,318 positions and 30,490,130 pseudo-legal moves (28,713,739 legal, 1,070,770 checking).
  - **0 legality and 0 check mismatches**, both for the switch alone and with bundle (d)'s defines.
  - The harness catches errors: a planted wrong pin rule (a board.cpp mutant, kept at `F:\ospd\w9\board_mutant_pin.cpp`)
    gives 556,251 legality mismatches on 301 FENs.
- **Bug found and fixed by the harness before any build:** `set_fen` builds its candidate as a copy of `*this`, so a
  valid cache of the previous position survived into the new one. It is now invalidated where `set_fen` installs the
  position.

## Not done
- No independent review of this switch. The reviewer worker (patchrev) ran out of model credits before it started.
  The open review questions, for whoever picks it up:
  - every special move class (discovered checks by the mover, double checks, en-passant horizontal pins, castling-rook
    checks, promotion checks);
  - cache validity on every board copy / FEN path;
  - thread safety of the lazily filled cache.
- No ABBA, no L3b warm-table identity, no Threads 2-4 smoke: the lock path is incomplete.
