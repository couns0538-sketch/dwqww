# RULES_TABLE.md — engine verdict vs FIDE, swarm/72

One row per rule clause tested. Source lines are from
`forge-combo29/swarm/72/src/board.cpp` and `src/search.cpp` in this branch.

The engine binary is `build/forge` (Chess Engine Forge 5.31.0, g++ 13,
`-O2`, Release). The oracle is python-chess 1.11.2, used for FEN validation,
legal move generation, `is_repetition(n)` counting, and `outcome()`.

Column **agree** compares the engine's behaviour against the FIDE reading
stated in the **fide verdict** column, not against the engine's own comments.

| # | Rule | FIDE clause | Engine behaviour | Engine source | FIDE verdict | Agree |
|---|------|-------------|------------------|---------------|--------------|-------|
| 1 | Position identity includes castling rights | 9.2.2 (identity = same player, same pieces on same squares, same *possible moves*) | Positions differing only in rights get different keys, so they are never merged | `compute_key()` `board.cpp:953-964`, `mix(900+castling_)` | different positions → must not be merged | **agree** |
| 2 | Position identity includes en-passant availability when a legal ep capture exists | 9.2.2.1 | ep square is hashed only when `has_legal_en_passant_capture()` is true | `board.cpp:959-961`, `board.cpp:674-676`, helper `board.cpp:927-951` | ep right that is legally exercisable makes positions different | **agree** |
| 3 | ep right that is NOT legally exercisable does not change identity | 9.2.2.1 ("possible moves are the same") | No capturer, or capturer pinned → key identical to the no-ep board | `has_legal_en_passant_capture()` `board.cpp:947` removes the captured pawn from occupancy before the attack test | positions are the same | **agree** |
| 4 | Repetition threshold = 3 occurrences | 9.2 | `matches >= 2` over reversible history, so 3 occurrences total | `is_repetition()` `board.cpp:844-853` (`return matches >= 2;`) | draw claim at the 3rd | **agree** |
| 5 | Occurrence 1 and 2 are playable | 9.2 | occ 1 → `cp+575`, occ 2 → `cp+575`, both searched normally | root bail `search.cpp:493-500` | no claim available yet | **agree** |
| 6 | Occurrences 3, 4, 5 are all draws | 9.2 | occ 3/4/5 → `cp0` at 5 nodes (root bail) | `search.cpp:493-500` | claim available at 3 and stays available | **agree** |
| 7 | Fifty-move trigger = 100 halfmoves | 9.3 | `halfmove_clock() >= 100` bails at the root | `search.cpp:493`, `search.cpp:409` | claim available at 100 | **agree** |
| 8 | 99 halfmoves is not yet a claim | 9.3 | hm 99 → searched (`cp0`, 80 nodes), not bailed | same | no claim | **agree** |
| 9 | 101 halfmoves is still a claim | 9.3 | hm 101 → `cp0`, 5 nodes | same | claim persists past 100 | **agree** |
| 10 | Pawn move resets the fifty-move clock | 9.3 | `a2a3` at hm 99 → hm 0 | `make_move` `board.cpp:669-670` | irreversible move resets | **agree** |
| 11 | Capture resets the fifty-move clock | 9.3 | `b1b8` capture at hm 99 → hm 0 | same | capture resets | **agree** |
| 12 | Quiet move increments the clock | 9.3 | `e1d1` at hm 99 → hm 100 | same | increments | **agree** |
| 13 | Clock reset is visible to the search | 9.3 | hm 99 with a pawn move available → `cp+748` (1082 nodes), not a drawn root | `search.cpp:493` reads the live clock | search must not declare a draw when a reset exists | **agree** |
| 14 | Threefold is NOT reached at 2 occurrences | 9.2 | occ 2 searched to `cp+575` | as row 5 | not yet a draw | **agree** |
| 15 | In-tree repetition detection exists below the root | 9.2 | instrumented build fires the repetition branch at `ply > 0`: 8 hits at depth 6, 158 at depth 10 from an occurrence-#2 root | `search.cpp:493-500` (`ply` guard only excludes `null_branch`) | repetition must be recognised wherever it arises | **agree** |
| 16 | In-tree repetition is *load-bearing* on the tested perpetual | 9.2 | ablated build (detection forced false) gives **identical** scores at depths 6–12 on every tested perpetual: `cp-23`, `cp-16`, `cp-11` both ways | ablation of `is_repetition()` | a forced perpetual should score 0 | **no measurable effect** (see limitation L2) |
| 17 | K vs K is dead | 5.2.2 | `insufficient=1` → draw | `is_insufficient_material()` `board.cpp:855-865` (`minor_count <= 1`) | dead draw | **agree** |
| 18 | KN vs K is dead | 5.2.2 | `insufficient=1` | same, `minor_count <= 1` | dead draw (no legal mate: exhaustive search finds none) | **agree** |
| 19 | KB vs K is dead | 5.2.2 | `insufficient=1` | same | dead draw (no legal mate) | **agree** |
| 20 | KNN vs K is NOT dead | 5.2.2 | `insufficient=0` → not a draw | `board.cpp:864` (`knights == 0 && …`) returns false whenever a knight exists | **not** a dead position: a legal mate exists, witness `8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1` | **agree** — the engine is right and the "defect" briefed to me is wrong |
| 21 | KNN vs KN is NOT dead | 5.2.2 | `insufficient=0` | same | mate exists, witness `8/8/8/8/8/1N6/8/K1knN3 b - - 0 1` | **agree** |
| 22 | KB vs KB, same colour complex, is dead | 5.2.2 | `insufficient=1` | `board.cpp:864` — all bishops on one colour | exhaustive search finds no legal mate | **agree** |
| 23 | KB vs KB, opposite colour complexes, is NOT dead | 5.2.2 | `insufficient=0` | same line: mixed colours fail the mask test | mate exists, witness `7b/8/8/8/8/8/B7/K1k5 w - - 0 1` | **agree** |
| 24 | KB vs KN is NOT dead | 5.2.2 | `insufficient=0` | same | mate exists, witness `8/8/8/8/8/8/B1n5/K1k5 w - - 0 1` | **agree** |
| 25 | KNN vs KB is NOT dead | 5.2.2 | `insufficient=0` | same | mate exists, witness `8/8/8/8/8/4N3/N2b4/K1k5 b - - 0 1` | **agree** |
| 26 | A claimable draw must not suppress a deliverable mate | 9.2, 9.3, 5.1.1 | At `halfmove_clock >= 100` with mate-in-1 on the board the engine returns `cp 0` and plays `a1a2` instead of mate `a1a8` (6 nodes). Same at a root threefold: returns `cp 0`, plays `a1a2` | root bail `search.cpp:493-500` returns 0 before any move is tried | 9.3/9.2 are **claims by the player to move**; the mover may decline and play mate. 5.1.1: mate immediately ends the game. A search that returns 0 here misjudges a won position as a draw | **DISAGREE** |

**Row count: 26**

## Supporting detail for the rows that need it

### Row 2–3: why the ep handling is right

The engine hashes the ep square only when a *legal* capture exists:

```927:951:forge-combo29/swarm/72/src/board.cpp
bool Board::has_legal_en_passant_capture() const {
    if (ep_square_ < 0) return false;
    const int target = ep_square_;
    const Piece pawn = side_ == White ? WP : BP;
    const int captured_square = side_ == White ? target - 8 : target + 8;
    const std::array<int, 2> candidates = side_ == White
        ? std::array<int, 2>{target - 9, target - 7}
        : std::array<int, 2>{target + 7, target + 9};
    const int king = king_squares_[static_cast<std::size_t>(side_)];
    if (king < 0) return false;
    const std::uint64_t base_occupancy = occupied_[White] | occupied_[Black];
    const std::uint64_t captured_bit = 1ULL << captured_square;
    for (const int from : candidates) {
        if (!on_board(from) || abs_int(file_of(from) - file_of(target)) != 1 ||
            squares_[static_cast<std::size_t>(from)] != pawn) {
            continue;
        }
        std::uint64_t occupancy = base_occupancy;
        occupancy &= ~(1ULL << from);
        occupancy &= ~captured_bit;
        occupancy |= 1ULL << target;
        if (!square_attacked_with_occupancy(king, opposite(side_), occupancy, captured_bit)) return true;
    }
    return false;
}
```

The removed-occupancy replay is what makes the pinned-capture case come out
right: after the ep capture the line is opened, so the capture is illegal and
the ep square must not distinguish the position. Three shapes were tested:

| ep fixture | python-chess | keys |
|---|---|---|
| `4k3/8/8/8/3pP3/8/8/4K3 b - e3` vs `- -` | legal ep `d4e3` | **differ** (correct) |
| `4k3/8/8/8/4P3/8/8/4K3 b - e3` vs `- -` | no pseudo, no legal | **match** (correct) |
| `k3r3/8/8/3pP3/8/8/8/4K3 w - d6` vs `- -` | pseudo `e5d6`, legal none (pinned) | **match** (correct) |

### Row 20: the two-knights claim, refuted

The brief stated that KNN vs K is a draw and that the engine fails to
adjudicate it because `board.cpp:864` requires `knights == 0`.

The code does require `knights == 0` — but that is *correct* here. FIDE 5.2.2
draws a position only when **neither player can checkmate with any series of
legal moves**. With two knights, mate is possible, so the position is not
dead. A witness was found by exhaustive placement search and re-verified at
runtime:

`8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1` — legal position, black to move is
checkmated, material is exactly KNN vs K.

So the engine returning `insufficient=0` for KNN vs K agrees with FIDE. The
same reasoning clears KNN vs KN, KB vs KN and KNN vs KB, all of which also
have constructive mates. The two genuinely dead multi-piece sets are
KB vs KB same colour (no legal mate, exhaustive) and the ≤1-minor sets.

### Row 26: the one real rules defect

```493:500:forge-combo29/swarm/72/src/search.cpp
    if (!null_branch && (board.is_repetition() || board.halfmove_clock() >= 100)) {
        if (!board.in_check(board.side_to_move()) || board.has_legal_move()) return 0;
        return -MateScore + ply;
    }
```

At `ply == 0` this returns 0 *before* `legal_moves()` is generated, so a
position that is both claimable-drawn and won is scored as a draw:

| fixture | mate on board | engine |
|---|---|---|
| `7k/8/6K1/8/8/8/8/R7 w - - 99 60` | `a1a8` | `mate 1`, plays `a1a8` |
| `7k/8/6K1/8/8/8/8/R7 w - - 100 60` | `a1a8` | `cp 0`, plays `a1a2` |
| threefold root, `a1a8` available | `a1a8` | `cp 0`, plays `a1a2` |

python-chess confirms the FIDE reading: `outcome()` is `None` for both of
these boards (they are not terminal), while `can_claim_fifty_moves()` and the
repetition claim are available — i.e. a *claim the mover may waive*. The
engine treats a waivable claim as an automatic draw, which is the same
modelling error in both places.

Practical consequence: in a winning position at halfmove ≥ 100 (or on a
threefold) the engine stops converting and shuffles. This is a real
strength loss in any game that reaches such a position while still won.

## Limitations of this audit

- **L1.** The audit exercises the engine through UCI plus two purpose-built
  C++ probes that link the real `Board`/`Searcher`, not the shipped binary's
  internals. Behaviour is the same code path.
- **L2.** Row 16 is stated as "no measurable effect" rather than "defect".
  In-tree detection demonstrably executes (row 15) and demonstrably changes the
  search tree — with the repeating move forced, the ablated build visits 4187
  nodes where the stock build visits 4186 at depth 6 — but I could not
  construct a position where removing it changes a *score*. A 199-position
  differential scan returned zero differences, which I explicitly do **not**
  count as evidence: zero node-count differences there prove the branch never
  executed, so that corpus cannot speak to the question. The honest reading is
  that the tested fixtures are not repeat-dependent, not that in-tree
  detection is broken.
- **L3.** All 26 rows are for the six cases the brief named plus the
  combinations those imply. This is not a proof of correctness for arbitrary
  material (e.g. KBB vs KN).
