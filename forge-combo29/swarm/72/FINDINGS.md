# FINDINGS.md — repetition, fifty-move, insufficient material (swarm/72)

Engine: Chess Engine Forge 5.31.0 (C++20), `forge-combo29/swarm/72/`,
branch `for-fable-and-opus/swarm-72`.
Oracle: python-chess 1.11.2.
Table of every rule clause: `RULES_TABLE.md` (**26 rows**).

## Summary

Five of the six areas in the brief are **correct**. One real rules defect was
found, and one claim in the brief was **refuted**.

| Area | Verdict |
|---|---|
| 1. Repetition key contents | correct — castling and legal-ep both hashed |
| 2. Threshold | correct — 3 occurrences, `matches >= 2` |
| 3. Fifty-move | correct — `>= 100`, resets work and are visible |
| 4. Interaction | **DEFECT** — a waivable draw claim suppresses a legal mate |
| 5. In-tree repetition | present and live; not shown load-bearing (31 footprinted positions, 0 verdict changes) |
| 6. Insufficient material | all 9 material sets agree with FIDE |

## The defect: a claimable draw is treated as an automatic draw

`src/search.cpp:493-500`, reached at `ply == 0` as well as below the root:

```493:500:forge-combo29/swarm/72/src/search.cpp
    if (!null_branch && (board.is_repetition() || board.halfmove_clock() >= 100)) {
        if (!board.in_check(board.side_to_move()) || board.has_legal_move()) return 0;
        return -MateScore + ply;
    }
```

The draw-by-threefold (FIDE 9.2) and draw-by-fifty-moves (9.3) are **claims
belonging to the player to move**. A player who can mate will decline the
claim and play the mate; 5.1.1 says the game is over the moment the mate is
delivered. The engine instead returns 0 *before generating a single move*, so
it cannot see the mate at all.

Measured, with a mate in one (`Ra1-a8`) legally on the board in every row:

| position | halfmove | mate available | engine score | engine move |
|---|---|---|---|---|
| `7k/8/6K1/8/8/8/8/R7 w - - 0 60` | 0 | `a1a8` | `mate 1` | `a1a8` |
| same, 98 | 98 | `a1a8` | `mate 1` | `a1a8` |
| same, 99 | 99 | `a1a8` | `mate 1` | `a1a8` |
| same, 100 | 100 | `a1a8` | **`cp 0`** | **`a1a2`** |
| same, 101 | 101 | `a1a8` | **`cp 0`** | **`a1a2`** |
| same, 149 | 149 | `a1a8` | **`cp 0`** | **`a1a2`** |
| threefold root (`a1a8` available) | 8 | `a1a8` | **`cp 0`** | **`a1a2`** |

The break is exactly at the documented threshold (99 → 100), which shows the
trigger itself is right and only the *consequence* is wrong.

### At game level it loses a won position

The static score is not the whole story. Letting the engine play the winning
side against a defender that only moves its king shows the consequence
(`tools/audit72/t_mate_game.py`):

| start halfmove | result |
|---|---|
| 99 (control) | plays `a1a8`, **mate in 1 move** |
| 100 (treatment) | `a1a2`, `a2a3`, `a3a4`, `a4a5`, `a5a6`, `a6a7`, `g6f7`, then `a7a8` **when it is no longer mate** — never converts |

Both starts are the identical position; only the clock differs, so nothing but
the threshold can explain the divergence. The engine walks its rook up the
board for eight moves, plays the mating square *after* the mate has gone, and
finishes with the halfmove clock at 116.

python-chess independently confirms these are claims and not terminal states:

```
Board('7k/8/6K1/8/8/8/8/R7 w - - 0 1').outcome()            -> None
Board('7k/8/6K1/8/8/8/8/R7 w - - 100 60').outcome()         -> None
Board('7k/8/6K1/8/8/8/8/R7 w - - 100 60').can_claim_fifty_moves() -> True
```

A correct engine may still treat a *repetition it can force* as a draw when
it is the weaker side, and may treat a fifty-move position as a draw when no
progress is possible — but it must not do so when a mate is deliverable. The
minimal fix is at the root only: do not return 0 at `ply == 0` before
generating moves, or check for an immediate mate first.

Impact: in any won position that reaches halfmove 100 or a threefold, the
engine stops converting and starts shuffling. This is a genuine strength
loss, not a bookkeeping nit — the game-level run above shows a mate in one
thrown away and never recovered.

## Refuted: the two-knights "defect"

The brief states KNN vs K is a draw and that `board.cpp:864` fails to
adjudicate it because it requires `knights == 0`.

The line is:

```855:865:forge-combo29/swarm/72/src/board.cpp
bool Board::is_insufficient_material() const {
    constexpr std::uint64_t DarkSquares = 0xAA55AA55AA55AA55ULL;
    const std::uint64_t pawns_rooks_queens = bitboards_[WP] | bitboards_[BP] | bitboards_[WR] |
                                             bitboards_[BR] | bitboards_[WQ] | bitboards_[BQ];
    if (pawns_rooks_queens != 0) return false;
    const std::uint64_t knights = bitboards_[WN] | bitboards_[BN];
    const std::uint64_t bishops = bitboards_[WB] | bitboards_[BB];
    const int minor_count = std::popcount(knights | bishops);
    if (minor_count <= 1) return true;
    return knights == 0 && ((bishops & DarkSquares) == 0 || (bishops & ~DarkSquares) == 0);
}
```

It does require `knights == 0` at line 864. That is **correct**, because FIDE
5.2.2 only draws a position when neither side can mate "with any series of
legal moves", and two knights *can* mate:

```
8/8/8/8/8/1N2N3/8/K1k5 b - - 0 1   -> is_valid True, is_checkmate True
```

That is a legal position, black is mated, and the material is exactly
KNN vs K. The same construction yields mates for KNN vs KN
(`8/8/8/8/8/1N6/8/K1knN3 b - - 0 1`), KB vs KN (`8/8/8/8/8/8/B1n5/K1k5 w - - 0 1`)
and KNN vs KB (`8/8/8/8/8/4N3/N2b4/K1k5 b - - 0 1`). The engine calls none
of them a draw, which is right.

Where the engine *is* generous is the opposite direction: KB vs KB with
bishops on opposite colours is also **not** dead (mate exists; witness
`7b/8/8/8/8/8/B7/K1k5 w - - 0 1`), and the engine does not call it a draw —
correct.

Full nine-set result:

| material | legal mate exists? | FIDE | engine |
|---|---|---|---|
| K vs K | no (exhaustive) | draw | draw |
| KN vs K | no (exhaustive) | draw | draw |
| KB vs K | no (exhaustive) | draw | draw |
| KNN vs K | **yes** | not draw | not draw |
| KNN vs KN | **yes** | not draw | not draw |
| KB vs KB same colour | no (exhaustive) | draw | draw |
| KB vs KB opposite colour | **yes** | not draw | not draw |
| KB vs KN | **yes** | not draw | not draw |
| KNN vs KB | **yes** | not draw | not draw |

## Repetition key: correctly FIDE-complete

Both fields FIDE requires are present, including the two cases naive
implementations get wrong:

| fixture | python-chess | engine keys |
|---|---|---|
| castling rights only (`KQ` vs `-`) | placement identical | **differ** |
| castling rights only (`K` vs `Q`) | placement identical | **differ** |
| ep capture legal (`d4e3`) | `d4e3` legal | **differ** |
| ep square set, no capturer | no ep move | **match** |
| ep pseudo-legal but pinned | `e5d6` illegal | **match** |

The pinned case is the interesting one: `has_legal_en_passant_capture()`
replays the capture with the removed pawn excluded from occupancy, so a
discovered check down the opened file correctly makes the ep right
non-existent — and therefore non-distinguishing.

This directly contradicts the earlier seat's fixture bug (a key that skipped
castling). In this build the key includes castling rights, so that bug is not
present here.

## Threshold and fifty-move: correct

| occurrences | engine score | nodes | reading |
|---|---|---|---|
| 1 | `cp+575` | 7745 | searched |
| 2 | `cp+575` | 7713 | searched |
| 3 | `cp 0` | 5 | root bail |
| 4 | `cp 0` | 5 | root bail |
| 5 | `cp 0` | 5 | root bail |

| halfmove | engine | reading |
|---|---|---|
| 99 | `cp 0`, 80 nodes | played on |
| 100 | `cp 0`, 5 nodes | bailed |
| 101 | `cp 0`, 5 nodes | bailed |
| 99 + pawn move available | `cp+748`, 1082 nodes | reset wins |
| `a2a3` from hm 99 | hm → 0 | reset |
| `e1d1` from hm 99 | hm → 100 | increment |
| `b1b8` capture from hm 99 | hm → 0 | reset |

## In-tree repetition

**Detection exists.** An instrumented build counting the repetition branch,
split by ply, shows it firing well below the root:

| search | `ply > 0` hits | `ply == 0` hits |
|---|---|---|
| root threefold, depth 5 | 0 | 5 (one per iterative-deepening pass) |
| occurrence-#2 rook cycle, depth 6 | **8** | 0 |
| occurrence-#2 rook cycle, depth 10 | **158** | 0 |
| perpetual study, depth 10 | **6** | 0 |

It also leaves a **footprint**: with the repeating move forced, the ablated
build visits 4187 nodes where the stock build visits 4186 at depth 6. A branch
that executes perturbs the tree even when its verdict does not change, which is
what makes a null about it checkable.

**It is not shown to be load-bearing.** Two scans, and the difference between
them is the point:

*Opening positions (vacuous).* 199 roots from the shipped opening corpus, each
placed on occurrence #2 by a verified 4-ply reversible cycle, depth 8, both
binaries. Result: 0 score differences **and 0 node-count differences**.
Identical node counts prove the branch never executed — in an opening position
a forced repetition is nowhere near the best line, so the search never explores
it. Instrumenting two scanned positions confirms `in_tree=0`:

| position | in-tree hits | result |
|---|---|---|
| `rnbqkb1r/pp1pn1pp/2p5/3P4/2P1pp2/4B2N/PP2PPPP/RN1QKB1R w` | 0 | `cp117` |
| `rn1qkb1r/p1p1ppp1/1p1pbn2/7p/3P4/2N1PN2/PPP1BPPP/RBQK2R w` | 0 | `cp54` |

A null from a corpus that cannot reach the code is vacuous, so this is not
counted as evidence.

*Footprint-selected endgames (a real null).* 600 generated endgames (rook/rook,
Q/Q+R, B+B with pawns), each root on occurrence #2. The instrumented build is
run **first** and only roots where the branch fired are kept, so the comparison
cannot be empty by construction:

| measurement | result |
|---|---|
| roots where a cycle was playable | 62 |
| roots with a repetition footprint below the root | **31** |
| footprint range | 1–24 executions per search |
| positions where stock and ablated scores differ | **0** |

That is a genuine null: the branch ran, up to 24 times in one search, and no
verdict moved.

**And the null is not a missed draw.** A position scoring ≈ −550 while the
branch fires could be either "really lost" or "engine failed to find the
draw". Those separate under deeper search — a missed draw trends toward 0, a
real loss trends further negative:

| root | depth 6 | depth 8 | depth 10 | depth 12 |
|---|---|---|---|---|
| `3r3k/8/8/q7/4Q3/8/8/K7 w` | −550 | −564 | −571 | **−1010** |
| `7k/8/7r/8/4Q3/8/5q2/K7 w` | −536 | −544 | −553 | **−560** |
| `7k/8/5r2/3Q4/8/8/5q2/K7 w` | −546 | −552 | −558 | **−559** |

All three deepen, so these are confirmed losses, not missed draws.

**Conclusion:** the mechanism is present, live, and leaves a trace; removing it
changed no score on 31 positions where it demonstrably executed. What I cannot
claim is that in-tree detection is load-bearing — no fixture showed a draw
becoming a loss when it was ablated.


Constructing a position where the repetition is provably decisive is the one
piece of work this audit did not finish. The selection machinery is in place
(`tools/audit72/select_fixture.py`, `find_loadbearing.py`,
`verify_perpetual.py`), and the constraint that made it hard is worth
recording: a perpetual must keep material constant, because otherwise the
"checking" move is really a winning capture and the position is not a draw at
all. An earlier verifier of mine accepted exactly such a line and would have
produced a false accusation; the corrected one rejects it.

## Fixture integrity

Two hand-written fixtures were rejected before they could produce wrong
numbers:

- `7k/8/6K1/8/8/8/P7/7R w - - 99 60` — engine: `side that moved left its
  king in check`.
- `4k3/8/8/4P3/8/8/8/4K3 b - e6 0 1` — engine: `inconsistent en-passant
  square`.

Both would have left the previous board loaded and silently measured it. Every
fixture in every suite now passes: python-chess validation → both reply
streams scanned for `invalid FEN` → `go perft 1` move count and move set equal
to python-chess. `tools/audit72/test_guards.py` proves each of those gates can
fail, including a stale-board trap that demonstrates the exact failure mode.

## Two nulls of mine that were withdrawn

Both are instances of the same rule applied in opposite directions, and both
are recorded because they are the kind of error that reads as a finding.

**1. A missing witness.** An early perpetual verifier accepted a line where the
"checking" move actually won a piece — `Qxf8+` after an interposition. That is
not a draw by repetition, and the fixture would have shown a correct engine to
be wrong. The corrected verifier requires the material balance at the looping
position to equal the balance at the root, so a winning capture can no longer
be mistaken for a perpetual.

**2. A null without a footprint.** The 199-position opening scan returned zero
differences, which looked like evidence that in-tree repetition never matters.
It was not: node counts were also identical, proving the branch never executed.
The fix was to select candidates by the footprint (keep only roots where the
branch fires) rather than by intuition. That re-run is a real null — 31
positions, 1–24 executions each, still zero verdict changes — and its losing
scores were confirmed as genuine losses by a depth trend rather than a missed
draw.

The general rule both teach: **an absence needs the same proof as a defect, and
a null needs a footprint.** To show a code path does *not* matter, show that it
ran and that nothing followed.


## Recommendation

One fix, in `search.cpp:493-500`: do not return 0 at `ply == 0` before
generating moves. Either exempt the root, or check for an immediate mate
before taking the draw. The threshold logic underneath is already correct, so
the change is small and local.
