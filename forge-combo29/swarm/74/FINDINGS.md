# FINDINGS — move generation at the edges

Branch `for-fable-and-opus/swarm-74`, base commit `6b98f217`, work in
`forge-combo29/swarm/74/`. Engine built from that tree unmodified; no source
changes were made or needed.

## Headline

**Move generation is correct at every edge I could reach: 0 mismatches out of
2,000 random positions at perft 3, 0 mismatches on 42 standard-suite cells
(including kiwipete d6 and position6 d6), and 0 mismatches on 11 hand-built
special-move fixtures.** No disagreement was found anywhere, so there is no
mismatch section to fill in — the fuzz found nothing, and that is the result.

| stage | compared | mismatches |
|---|---:|---:|
| standard suite (7 positions × depths 1–7) | 42 cells | 0 |
| special-move fixtures | 11 fixtures / 33 cells | 0 |
| fuzz, uniform random play | 2,000 positions | 0 |
| fuzz, directed en-passant (any ep) | 500 positions | 0 |
| fuzz, directed castling | 500 positions | 0 |
| **fuzz, targeted: ep discovers check** | **500 positions** | **0** |
| **fuzz, targeted: ep exposes king (illegal)** | **500 positions** | **0** |
| **fuzz, targeted: castling rights lost by rook capture** | **500 positions** | **0** |
| **fuzz, targeted: underpromotion to knight giving check** | **500 positions** | **0** |
| move-identity walk (depth 2 and 3, §3b) | 290,623 nodes | 0 |
| **total** | **5,075 count comparisons + 290,623 move-set comparisons** | **0** |

## 1. Standard suite

See `PERFT_TABLE.md` for every cell with the published count beside the measured
one. Summary: 42 cells, 42 agree. 28 of those published counts were independently
re-derived with python-chess and all 28 agreed, so the published table was not
taken on faith where it was cheap to check. Deepest runs: kiwipete d6
(8,031,647,685) and position6 d6 (6,923,051,137) both exact, plus position3 d7
(178,633,661).

## 2. Special-move edges

Each fixture is its own FEN with an independent python-chess count. The important
design point: **a green count does not prove the edge was tested.** So each
fixture carries required-present and required-absent move assertions, checked
against python-chess first; if a required move is illegal, or a forbidden move is
legal, the row is reported `FIXTURE DEAD` rather than green. The engine's
depth-1 move set is then compared to python-chess move-for-move, which is
stricter than comparing node counts and prevents two compensating errors from
cancelling.

| fixture | fen | edge asserted | d1 | d2 | d3 |
|---|---|---|---:|---:|---:|
| ep discovers check | `4k3/8/8/3pP3/8/8/8/4R1K1 w - d6 0 1` | `e5d6` present; capture vacates e5 and opens Re1→e8 | 15 | 85 | 1,369 |
| ep would expose king | `8/8/8/8/k2pP2R/8/8/4K3 b - e3 0 1` | `d4e3` **absent** (opens rank 4 onto Ka4) | 6 | 89 | 635 |
| castle through attack | `r4rk1/8/8/8/8/8/8/R3K2R w KQ - 0 1` | `e1g1` **absent** (f1 attacked), `e1c1` present | 23 | 470 | 10,190 |
| castle out of check | `4k3/8/8/8/1b6/8/8/R3K2R w KQ - 0 1` | both castles **absent** (Bb4 checks e1) | 4 | 56 | 1,475 |
| castle, rook attacked | `r3k3/8/8/8/8/8/8/R3K2R w KQq - 0 1` | both castles **present** (a1 attacked, king squares are not) | 26 | 352 | 8,852 |
| rights lost by rook capture | `r3k2r/8/8/8/8/8/8/R3K3 w Qkq - 0 1` | `e1g1` absent, `e1c1` present | 16 | 362 | 5,628 |
| promotion with capture | `nn6/P7/8/8/8/8/8/k6K w - - 0 1` | all four `a7b8*` present; all four quiet `a7a8*` absent | 7 | 40 | 411 |
| underpromotion knight check | `8/1P1k4/8/8/8/8/8/7K w - - 0 1` | all four `b7b8*` present, and verified by board state that **only** `b7b8n` gives check | 7 | 42 | 469 |
| double push beside pawn | `4k3/8/8/8/3p4/8/4P3/4K3 w - - 0 1` | `e2e4` present, setting an ep square beside black's d4 pawn | 6 | 38 | 248 |
| pin, moves along line | `4r1k1/8/8/8/8/8/4R3/4K3 w - - 0 1` | `e2e3`, `e2e4`, `e2e8` present; `e2a2`, `e2h2`, `e2d2` absent | 10 | 129 | 1,775 |
| pin, cannot leave line | `4r1k1/8/8/8/8/8/4B3/4K3 w - - 0 1` | `e2c4`, `e2d3`, `e2f3`, `e2g4` absent (control for the row above) | 4 | 64 | 791 |

All 11 fixtures: 33 cells, 33 agree, 0 problems.

The underpromotion row deserves its note: the claim "only the knight gives check"
is verified by pushing each promotion and querying `board.is_check()`, not
asserted in a comment. b8=Q/R/B all leave Kd7 unattacked.

## 3. Fuzz

- Generator: random legal playouts from the start position (4–80 plies), so
  positions are legal by construction, then validated anyway.
- Comparison: `go perft 3` versus a recursive perft over python-chess's
  `legal_moves`.
- **2000 positions generated, 2000 compared, 0 mismatches, 0 engine refusals,
  64,383,829 nodes summed, seed 74000.**
- Every position passed a perft-1 and perft-2 board-identity check against
  python-chess before its depth-3 number was scored.

### Coverage is measured, not assumed

Uniform random play is a weak probe for exactly the moves this task cares about.
Measured over the 2,000 compared positions:

| edge | positions where it was available |
|---|---:|
| en-passant capture | 8 / 2,000 |
| promotion | 19 / 2,000 |
| castling | 67 / 2,000 |
| side to move in check | 85 / 2,000 |
| a pinned piece present | 171 / 2,000 |
| **no legal moves (checkmate)** | **13 / 2,000** (0 stalemate) |

A green result over 19 promotions would say almost nothing about promotion
handling. So the fuzz was extended in two ways.

First, two broadly directed generators (still legal positions via random play):

| directed set | positions | edge available | mismatches |
|---|---:|---|---:|
| en passant | 500 | ep capture 500/500 | 0 |
| castling | 500 | castling 371/500, in check 90/500 | 0 |

Second — and this is the part with real marginal value — a **targeted** mode
(`--target`) per named edge. Each target has a generator that samples until the
edge is genuinely live, and a predicate that proves the edge from python-chess's
own semantics, re-checked per position inside the run so a drifting generator
shows up as a refusal rather than a false green.

| target | positions | what the run proves held in every one | mismatches |
|---|---:|---|---:|
| `ep-check` | 500 | ep capture available 500/500, giving **discovered** check (pawn itself does not attack the king from its new square) | 0 |
| `ep-expose` | 500 | ep right present 500/500, capture **suppressed as illegal** 500/500 | 0 |
| `rook-rights` | 500 | one right intact with its rook, the other lost with no friendly rook on the square | 0 |
| `knight-check` | 500 | a knight promotion gives check and **no queen promotion does** | 0 |

The two ep shapes are *constructed* rather than sampled, because the geometry is
too specific to stumble on (the earlier sampling version reached ep-exposes-king
zero times in hundreds of thousands of attempts). The constructors, predicates
and counters were each checked against hand-verified truth cases, including
negatives: e.g. `edge_ep_discovers_check` is true on the constructed position and
false on startpos; `edge_underpromotion_knight_check` is true with White to move
and false with Black to move in the same placement.

Two claims worth separating, because the second is the one that would otherwise
be assumed:

- *knight-check*: verified that the knight checks and the queen does not, in
  60 of 60 sampled positions. (The first version of that verification script
  demanded that **all** promotions check and reported 0/60; the positions were
  fine, the check was wrong. Corrected and re-run.)
- *rook-rights*: verified in 60 of 60 that one right survives with its rook while
  the other has no friendly rook. The lost rook may have been replaced by an
  enemy piece rather than leaving an empty square — "rook gone" means "no
  friendly rook", not "empty".

## 3b. Move identity, not just counts

Perft compares node *counts*. A bug that substitutes one legal move for another
while preserving the total is invisible to it, and the same goes for a whole
family of generator errors. That limitation is worth closing rather than
disclaiming, so `identity.py` walks the tree comparing the engine's **move set**
against python-chess's at every node.

The engine only prints a divide at the root of a `go perft` call, so the walk sets
the position to each child and asks `go perft 1`, making the comparison per-node.
Child FENs go through `fen_with_ep()` for the reason in §5b — using `board.fen()`
would silently compare a weaker position at every node whose ep capture is
illegal.

| walk | positions | nodes compared | move sets equal | differences |
|---|---:|---:|---:|---:|
| depth 2 | 2,000 | 28,940 | 28,940 | 0 |
| depth 3 | 1,200 | 196,916 | 196,916 | 0 |
| depth 3 (targeted families) | 400 | 64,767 | 64,767 | 0 |

**290,623 nodes compared move-set-for-move-set, 0 differences** (28,940 + 196,916 + 64,767, three separate runs, not one). That is a
strictly stronger statement than the count results: at every one of those nodes
the engine emitted exactly the legal moves python-chess did, no more and no fewer.

The walk is not skipping the interesting nodes — measured on the 400-position
targeted walk:

| edge live at the node | nodes |
|---|---:|
| legal en-passant capture available | 100 |
| en-passant right present but **suppressed as illegal** | 248 |
| a promotion available | 17,787 |
| castling available | 57 |

Those ep and castling numbers are small in absolute terms even though the walk
is deep, because the root positions are deliberately sparse and the branches fill
in material. The count results in §3 cover those edges at far higher density; the
identity walk's contribution is that where it *does* visit them, it confirms the
move set rather than the count.

Self-test: `identity.py --self-test` takes a real position, removes one engine
move and adds a different one while **keeping the count identical**, and requires
the set comparison to catch it. It reports `engine-only ['a1a8'], python-only
['a2a3']`. That is precisely the bug class the count comparison cannot see.

## 4. Mismatches

**None.** No position in any stage disagreed, so there is no FEN or divide to
report. The reporting machinery for that case is present and proven: the fuzz
prints the FEN, the seed, the generating move list, the engine and python totals,
the delta, and a per-root-move divide of differing children. `fuzz.py --self-test`
plants an off-by-one engine count and the run reports it with a localising divide
(`b6b5: engine 982 python 981`, total delta 1), which is what the real report
would look like.

## 5. The FEN trap, measured

This mattered more than any movegen question here, because it manufactures
exactly the false positive this task hunts for.

Measured behaviour on this build:

1. An illegal FEN produces `info string invalid FEN: ...` **always** — the
   diagnostic is never suppressed.
2. Its **location depends on where you read**. With `isready` after `position`,
   it lands in the position reply before `readyok`. Without it, in the `go`
   output ahead of the node counts. Both in a fresh session and after a
   predecessor.
3. After a refusal the board **stays on the previous position**, so
   `go perft N` returns a perfectly plausible number for the wrong board.

Demonstrated: after kiwipete, `position fen 7k/8/8/8/8/8/8/K6R w - - 0 1 QQ`
followed by `go perft 1` answers **`nodes 48`** — kiwipete's legal move count,
with one `info string invalid FEN` line earlier in the stream. To a harness that
reads only the perft output, that is a movegen bug report on a position that was
never loaded.

Defences in `uci_perft.py`, all four proven to go red in `self_test()`:

1. python-chess validates the FEN before the engine ever sees it.
2. The position reply is scanned for the diagnostic (raised as `FenRejected`).
3. The `go perft` output is *also* scanned; an `info string invalid FEN` there
   means the counts below belong to another board and are never scored.
4. Board identity is proved before any deep comparison: `go perft 1` must equal
   python-chess's legal move count **and** produce the identical move set, and for
   depth ≥ 3 `go perft 2` must equal python-chess perft 2. Gate 4 is what catches
   the case where the diagnostic is somehow missed — a wrong board almost never
   shares both counts and the move set.

Self-test output (`python3 uci_perft.py <binary>`): planted bad count → red,
published-vs-python disagreement → refused, illegal FEN → rejected in gate 1,
board swap → detected, go-stream diagnostic → caught.

### 5b. A second FEN trap: python-chess silently deletes an ep square

Found while building the targeted generators, and it damages exactly the edge
this seat was asked to prove:

```python
>>> chess.Board("8/8/8/8/k2pP2R/8/8/4K3 b - e3 0 1").fen()
'8/8/8/8/k2pP2R/8/8/4K3 b - - 0 1'
```

`Board.fen()` **drops the en-passant square when no legal ep capture exists** —
because the only capture is illegal. That is precisely the ep-exposes-king
position. So a generated position built to test that edge silently loses it on
the way to the engine, and the comparison then runs on a different, weaker
position and reports green. The engine itself accepts the FEN with the square
present and returns the same count as python-chess (`nodes 6`), so the engine is
fine; the pitfall is in the harness.

Fix: `fen_with_ep()` in `fuzz.py` serializes the square unconditionally and is
used for every constructed position. The hand-written fixture in §2 was never
affected because its FEN is a literal, but any *generated* version would have
been — which is why the targeted `ep-expose` set is only trustworthy now.

This is the same class of failure as §5: a silent, plausible-looking substitution
that turns a real edge case into a vacuous green.

### 5c. `go perft` ends at a bare `nodes N`, and framing that is a trap

`go perft N` does **not** print a `bestmove`. It ends at the total line:

```
g1f3: 20
g1h3: 20
nodes 400          <- end of reply; nothing follows
```

Measured: no `bestmove` after perft in any session, and five consecutive perfts
on five different positions stay perfectly aligned. So treating `nodes N` as the
terminator is correct for this build — but it is an unwritten contract, and a
harness that gets it wrong desyncs silently rather than failing loudly. If even
one line followed the total (or the total were read before the divide finished),
the stray line would be attributed to the **next** command's reply, and every
subsequent comparison would be scoring the wrong reply against the right board.

Two consequences worth separating:

- Any implementation that waits for `bestmove` after `go perft` will hang forever.
  `go perft` is synchronous and never sends one.
- Any implementation that stops at `nodes N` is trusting that nothing follows.

The harness does the second, and now proves the framing rather than assuming it.
`Divide.check_consistent()` requires the child table to sum to the printed total
and to be non-empty, and the self-test drives it to red on a planted
non-adding-up divide and on an empty one. A drifted stream almost always breaks
that sum, so the invariant converts a silent desync into a loud error.

**The mate edge, found by that invariant going off:** a position with no legal
moves prints `nodes 0` and *no divide lines at all*. That is a real answer, not a
desync. My first version of the rule rejected it, and 13 of the 2,000 fuzz
positions are checkmate (measured, 0 stalemate) — so the "generates nothing" case was being silently
dropped from the set. Fixed to accept `nodes 0` with no children, and pinned by a
self-test using an actual mate (`rnbqkb1r/p1ppp2p/8/1p3ppQ/4n2P/P1N4R/1PPP1PP1/R1B1KBN1 b Qkq - 1 6`,
verified checkmate, engine and python-chess both 0). Both extremes are now
covered: perft 0 prints `nodes 1` with no divide, mate prints `nodes 0` with no
divide, and everything in between must add up.

## 6. Faults found in my own scaffolding

Recorded because each one, had it gone unnoticed, would have produced a
confident and wrong report:

1. **A double push onto an occupied square.** The directed en-passant generator
   put the enemy pawn *on* the landing square, so the push was never legal and
   the loop spun forever. Caught by a hang, then by validating the push against
   `legal_moves`.
2. **A push by a pinned pawn.** The same generator pushed blindly, leaving the
   mover in check and producing a FEN python-chess rejected as
   `OPPOSITE_CHECK`. Caught by FEN validation, not by luck.
3. **`board.pin()` misread.** python-chess returns an all-ones mask when nothing
   is pinned, so "a pin exists" tested true 5/5 on positions with no pin.
   Replaced with per-piece `is_pinned`.
4. **Two illegal fixture FENs.** An "in check" fixture whose black king sat
   behind White's rook (opposite check), and a promotion fixture whose quiet push
   was not actually blocked, which the `FIXTURE DEAD` guard caught.
5. **`Board.fen()` dropping the ep square** (§5b). Caught because the round-trip
   predicate disagreed with the live board object: `ep_square` was `f3` on the
   board but `None` after serializing and reparsing.
6. **Two wrong verification scripts of my own.** The knight-check verifier
   demanded every promotion check (0/60 on good positions), and the rook-rights
   verifier required the lost rook's square to be empty when the correct
   predicate is "no friendly rook". Both reported failures against correct data;
   both were fixed and re-run.
7. **A double import that silently disabled an assertion.** `from uci_perft
   import Divide` inside `uci_perft.py`'s own self-test re-executes the module
   under a second name when it is run as `__main__`, so the imported
   `EngineError` was a *different class object* and the `except` clause never
   matched. The rule was firing and the self-test was crashing instead of
   passing. Caught because the traceback showed the raise at the call site
   rather than the handler.
8. **The divide invariant rejected checkmate.** Requiring a non-empty divide is
   right for ordinary positions and wrong for mate, which prints `nodes 0` with
   no divide. It refused 4 positions in a 300-position sample; measured properly,
   13 of the 2,000 fuzz positions are checkmate, so the whole "generates nothing"
   case had been dropped from the set. Caught only because the refusal count went
   from 0 to 4 and I chased it instead of widening the rule.

Every one of these was caught by a gate, which is the point: the gates are the
finding, not just the numbers.

## 7. What this does not establish

- Depth 3 is shallow. The fuzz proves move generation, castling rights, ep and
  promotion legality across 3,000 positions, not search correctness, and says
  nothing about evaluation, pruning or time management.
- The fuzz positions from uniform random play are over-represented in quiet,
  undeveloped, high-material positions. That is now offset for all four named
  edges by 500 targeted positions each, but note what the targeted sets are: each
  one is deliberately concentrated on its edge, so they prove that edge in bulk
  and prove little about the rest of the position. The fixture set remains the
  only place where a single position is asserted move-for-move.
- Perft only checks move *counts*. This seat additionally compares move **sets**
  at 290,623 nodes (§3b), which closes the same-count-substitution hole across
  that sample — but the set comparison is per-node at shallow depth, not a proof
  over every node of every deep run. A same-count substitution elsewhere in the
  tree would still survive.
- No source changes were made, so this says nothing about whether the engine
  would still pass after edits.

## Reproducing

```bash
cd forge-combo29 && cmake -S . -B build-swarm74 -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ \
  && cmake --build build-swarm74 -j4
cd swarm/74
python3 uci_perft.py ../../build-swarm74/forge     # prove the harness can fail
python3 suite.py ../../build-swarm74/forge         # 42 cells, ~98s
python3 fixtures.py ../../build-swarm74/forge      # 11 fixtures, 33 cells
python3 fixtures.py ../../build-swarm74/forge --self-test
python3 fuzz.py ../../build-swarm74/forge --count 2000 --seed 74000   # ~70s
python3 fuzz.py ../../build-swarm74/forge --count 500 --seed 4 --ep
python3 fuzz.py ../../build-swarm74/forge --count 500 --seed 5 --castle
# targeted edges (the seat's marginal value)
python3 fuzz.py ../../build-swarm74/forge --count 500 --seed 21 --target ep-check
python3 fuzz.py ../../build-swarm74/forge --count 500 --seed 21 --target ep-expose
python3 fuzz.py ../../build-swarm74/forge --count 500 --seed 21 --target rook-rights
python3 fuzz.py ../../build-swarm74/forge --count 500 --seed 21 --target knight-check
```

Note on the build: `cmake` defaults to clang here, and clang cannot link against
`libstdc++` on this image (`cannot find -lstdc++`). Building with
`-DCMAKE_CXX_COMPILER=g++` works and reproduces every published count.
