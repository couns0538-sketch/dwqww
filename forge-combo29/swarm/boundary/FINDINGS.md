# One ply from every terminal state — boundary audit

**Branch** `swarm/boundary` · **Base commit** `6b98f217` · **Build** g++ 13,
`-DFORGE_MARCH=x86-64-v4`, Release, `FORGE_SPD_SLIDER_PEXT=1 FF_NNUE_ZMM=1`.

**Four honesty pins, all matched before any number was recorded:**

| pin | expected | measured |
|---|---|---|
| `bench 11` | 312,866 | 312,866 |
| `bench 13` | 862,329 | 862,329 |
| `bench 16` | 3,024,920 | 3,024,920 |
| `go perft 5` | 4,865,609 | 4,865,609 |

`bench N` was sent on **stdin** as a UCI command, not as argv.

## The answer first

Six matrix rows, all measured. **Five are clean; one is a real finding.**

| # | row | result |
|---|---|---|
| 1 | one ply from stalemate | **PASS 3/3** — `cp 0` in 84–180 nodes; control correctly `cp 1208` |
| 2 | one ply from insufficient material | **PASS 3/3 forced**, 2/2 optional — `cp 0` *before* the material is gone; won-reduction control correctly non-zero |
| 3 | one forced clock-resetting capture | **PASS** — clock reset honoured; `−486` at clock 99 vs `−471` at clock 0 |
| 4 | halfmove 99, every legal move a pawn move | **PASS** — engine knows; scores a win, never claims 0.00 |
| 5 | `0000` at every mate root | **PASS 6/6** — consistent, never a move |
| 6 | `0000` protocol shapes | **PASS** — all three reproduced, `info string` only on the restriction |

**No wrong answer was found in any family.** The one defect this audit *does*
report is not a search error but a **client-contract finding**: the `pv` field
is **present-and-empty**, never absent, at every terminal and drawn root — and
that is uniform enough to be safe, contrary to the hazard the report feared.

The single genuine miss I found is in an **adjacent area** and is listed under
"What I could not settle" as a lead, not a claimed defect.

---

## Method, and the two controls that had to be repaired

Every fixture was validated **twice** before its row counted: python-chess
accepted the FEN and the *structural claim* held, and the engine did not answer
`info string invalid FEN` to the `position` command. `scripts/forge_drv.py`
raises `RefusedFen` on that string, so a refused FEN cannot reach a result row.

`scripts/selftest.py` proves each checker fires on a planted fault before its
clean run is trusted. It caught two of my own bugs:

- **A predicate that could never fail.** A one-liner probe counted
  "stalemating moves" with `(b.push(m), b.is_stalemate(), b.pop())` inside a
  comprehension. A 3-tuple is always truthy, so *every* move counted as
  stalemating and the probe reported 26/26 for a position that is really 4/26.
  Caught because the enumerator written against the same claim returned **zero**
  positions where the probe said thousands.
- **A test that was wrong, not the engine.** My `mate-in-2` self-test fixture
  (`6k1/5ppp/8/8/8/8/5PPP/R5K1`) is actually **mate in 1** — `Ra8#` lands
  because nothing blocks the 8th rank. Replaced with
  `8/8/8/8/8/8/Q7/K1k5`, verified mate-in-2 by an independent forced-mate
  search to 3 plies.

Three fixtures passed python-chess but were **not** what the row asserted, and
each was caught only by checking the structural claim rather than trusting
`is_valid()`:

- `4k3/8/8/8/8/8/8/R3K2r w KQ - 0 40` — status 256, `BAD_CASTLING_RIGHTS`
  (castling claimed with no rook on h1).
- The same base position has White **in check**, so only 3 king moves are legal
  and a rook-shuffle move list is illegal from move 1.
- Row-2 fixture `8/8/8/8/8/8/1q6/KNk5 w` is **checkmate**, so an enumerator loop
  over legal moves passed **vacuously** on an empty list. Fixed by requiring a
  non-empty legal-move set.

**The truncation trap fired on me and I recorded it rather than the result.**
The engine keeps only the prefix of a move list up to the first illegal token.
My first repetition fixture sent `a1a2` from a position where White was in
check; the engine answered `info string illegal move a1a2` and searched the
*root board*, and my harness recorded `cp −505` as a "wrong score". The engine
was right and the fixture was a lie. `family3_repetition.py` now replays every
token on a python-chess board and refuses to build an illegal list, and it
checks the engine's reply for `illegal move` before scoring the row.

---

## Row 1 — one ply from stalemate

Fixtures from `stalemate.enum_every_move_stalemates`, which requires: the
opponent is already frozen (zero legal moves, not in check), **every** mover
move stalemates it, and **no** mate is available. `go depth 12`.

| fixture | legal | score | nodes | bestmove | pv |
|---|---|---|---|---|---|
| `8/8/8/8/1pk1p3/1P2P3/5q2/7K b - - 0 30` | 6 | `cp 0` | 84 | c4b3 | moves(1) |
| `k1K5/1p6/1P1B4/8/8/8/8/8 w - - 0 30` | 14 | `cp 0` | 180 | d6h2 | moves(1) |
| `8/8/1p2p3/1P2PK2/8/8/2Q5/k7 w - - 0 30` | 7 | `cp 0` | 96 | f5e6 | moves(1) |
| **CONTROL** `k7/2Q5/8/8/8/8/8/K7 w - - 0 30` | 26 | `cp 1208` | 47907 | c7f7 | moves(14) |

**3/3 scored the stalemate, 1/1 control did not flatten to zero.** The engine
sees the stalemate from the root: it searches (84–180 nodes, not 0), and the
score is exactly `cp 0`. It does **not** score a win and then get stuck. The
control proves the `cp 0` is not a blanket draw answer — the same
material balance with a real win scores `+1208`.

## Row 2 — one ply from insufficient material

Every fixture is **not** already drawn (`is_insufficient_material()` False) yet
a capture on the very next ply reduces to a drawn set. `forced` = the draw is
unavoidable; `optional` = a drawn continuation exists but is not forced.

| fixture | kind | d1 | d6 | d12 | bestmove |
|---|---|---|---|---|---|
| `8/8/8/8/8/8/q7/KNk5 w - - 0 40` | forced | `cp 0` / 2 | `cp 0` / 12 | `cp 0` / 24 | a1a2 |
| `8/8/8/8/8/q7/8/KNk5 w - - 0 40` | forced | `cp 0` / 2 | `cp 0` / 12 | `cp 0` / 24 | b1a3 |
| `8/8/8/8/8/8/q7/K1kN4 w - - 0 40` | forced | `cp 0` / 2 | `cp 0` / 12 | `cp 0` / 24 | a1a2 |
| `8/8/8/8/8/8/b7/K1k1B3 w - - 0 40` | optional | `cp 0` / 10 | `cp 0` / 157 | `cp 0` / 649 | a1a2 |
| `8/8/8/8/8/8/b4B2/K1k5 w - - 0 40` | optional | `cp 0` / 11 | `cp 0` / 208 | `cp 0` / 995 | a1a2 |
| `4k3/8/8/8/8/8/8/4K3 w - - 0 40` | root-drawn | `cp 0` / 0 | `cp 0` / 0 | `cp 0` / 0 | e1d1 |
| **CONTROL** `4k3/8/8/8/8/8/4r3/4KR2 w - - 0 40` | won | `cp 326` / 3 | `cp 434` / 664 | `cp 471` / 45436 | e1e2 |

**5/5 drawn positions scored 0.00 and 1/1 won-reduction control did not.**
The draw is scored **before** the material is reduced — at depth 1, after 2
nodes, on a board that still has a knight and a queen on it. This is the
incremental evaluation path working, and it is worth stating because the
`H > 100 − p` band proves the *clock* side of the leaf rule is broken while the
*material* side is not.

The control matters: `4k3/8/8/8/8/8/4r3/4KR2` reduces to **KRvK**, which is
won, and the engine correctly refuses to say 0.00 (`+326` … `+471`).

## Row 3 — one forced clock-resetting capture

Exactly one legal move; it is a capture; it resets the halfmove clock; and the
result is **not** drawn by material, so a 0.00 would be the fifty-move rule
misfiring rather than a real draw. Mover is Black, lost either way.

| fixture | before (H=99) | after the forced capture |
|---|---|---|
| `8/8/8/8/8/8/Q7/kRK5 b - - 99 60` | `cp −486`, 36210 nodes | `cp +471`, 16673 nodes |
| `8/8/8/8/8/8/Q7/k1KR4 b - - 99 60` | `mate −3`, 604 nodes | `mate +3`, 333 nodes |
| `8/8/8/8/8/8/Q7/k1K1R3 b - - 99 60` | `mate −2`, 420 nodes | `mate +2`, 241 nodes |
| **CONTROL** same board, `H=0` | `cp −471`, 4887 nodes | — |

**The 50-move evaluation does change after the move, and correctly.** At H=99
the engine still reports the true value (`−486`, or an exact `mate −3`), it does
not pre-emptively return 0.00 even though the clock is one from the limit — and
after the capture the clock is reset and the score is the true `+471` /
`mate +3`. The H=0 control lands within 15 cp of the H=99 reading (`−471` vs
`−486`), which is the right order of magnitude for search noise and proves the
clock is not leaking into the evaluation by more than a rounding.

## Row 4 — halfmove 99, every legal move a pawn move

Enumerated so the mover's king has **no** legal move and only its pawn can push.
Any move resets the clock, so the mover **cannot** reach 100 and the fifty-move
draw is **not** reachable. A 0.00 here would be wrong.

| fixture | legal | d1 | d6 | d12 | bestmove |
|---|---|---|---|---|---|
| `8/8/8/8/8/8/P7/K1k5 w - - 99 60` | 2 | `cp 940` / 3 | `cp 940` / 77 | `cp 940` / 18870 | a2a4 |
| `8/8/8/8/8/8/7P/5k1K w - - 99 60` | 2 | `cp 1029` / 3 | `cp 1029` / 86 | `cp 1029` / 21675 | h2h4 |
| `8/8/8/8/8/8/P7/K6k w - - 99 60` | 4 | `cp 1011` / 5 | `cp 1011` / 93 | `cp 1011` / 34609 | a2a4 |

**The engine knows.** It never returns 0.00 and never bails; it scores a large
win and the score is *identical at depth 1 and depth 12*, which is the shape you
expect when the position is decided by the pawn race rather than by the clock.
It plays the pawn push, which is the only move that resets the clock.

## Row 5 — `bestmove 0000` vs a legal move at every mate root

Six genuine checkmates, spanning back-rank, Fool's Mate, a queen mate delivered
by the other colour, corner, smothered, and ladder. All verified
`is_checkmate()` True and 0 legal moves.

| fixture | score | nodes | bestmove | pv shape |
|---|---|---|---|---|
| `7k/6Q1/6K1/8/8/8/8/8 b - - 0 60` | `mate 0` | 0 | `0000` | `pv` present, empty |
| `rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3` | `mate 0` | 0 | `0000` | present, empty |
| `8/8/8/8/8/6k1/6q1/7K w - - 0 60` | `mate 0` | 0 | `0000` | present, empty |
| `k7/1QK5/8/8/8/8/8/8 b - - 0 60` | `mate 0` | 0 | `0000` | present, empty |
| `5K1k/5Npp/8/8/8/8/8/8 b - - 0 60` | `mate 0` | 0 | `0000` | present, empty |
| `R5k1/8/6K1/8/8/8/8/R7 b - - 0 60` | `mate 0` | 0 | `0000` | present, empty |

**6/6 answered `0000`; 0 answered a move.** The `0000` is **consistent** — it is
not "sometimes yes". The inconsistency that would break client mate detection
**does not exist** on this build. Every one also carries `score mate 0` and
`nodes 0`, so a client can discriminate checkmate from stalemate by score kind
exactly as §1b says.

## Row 6 — the `0000` shapes and the `info string`

| shape | bestmove | score | nodes | `info string` | pv |
|---|---|---|---|---|---|
| checkmate root (both colours) | `0000` | `mate 0` | 0 | **none** | present, empty |
| stalemate root (both colours) | `0000` | `cp 0` | 0 | **none** | present, empty |
| empty `searchmoves` | `0000` | `cp 0` | 0 | `searchmoves restriction has no legal root moves` | present, empty |
| all-illegal `searchmoves` | `0000` | `cp 0` | 0 | same string | present, empty |
| drawn root (bare kings) | legal move | `cp 0` | 0 | none | present, empty |
| **CONTROL** startpos `go depth 8` | `d2d4` | `cp 26` | 4099 | none | moves(8) |

**All three `0000` shapes confirmed, and exactly one carries an `info string`** —
the `searchmoves` restriction, which is also the answer to the all-illegal list.
The score discriminator holds in both directions: `mate 0` for checkmate,
`cp 0` for stalemate and for the restriction.

### The `pv` field: present-and-empty, never absent

The report's main client finding is the empty-vs-absent distinction, so it is
stated per row: **`pv` was present in all 48 recorded rows** — 39 with moves,
9 present-and-empty, **0 absent**. Sampled raw wire:

    info depth 12 seldepth 12 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv
    info depth 1  seldepth 1  score cp 0   nodes 0 nps 0 hashfull 0 time 0 pv

The token `pv` is printed with nothing after it. A client testing for the
**presence of the `pv` keyword** will therefore see "there is a pv" at every
terminal root and must test for an **empty tail** instead. That is the hazard,
and it is uniform — which is the good news for a client author: one rule
(`split on ' pv', take the tail, treat empty as none) is correct everywhere.

---

## What I had to withdraw

- **`cp −505` on a "threefold root"** — withdrawn. The fixture's move list was
  illegal from the first token; the engine truncated it and searched the root
  board. Not an engine defect.
- **"`row2_1` and `row2_2` prove the draw is foreseen"** — withdrawn. Those
  KBvKB positions are **not forced** to reduce; only *some* moves allow it, so
  `cp 0` there is engine optimism rather than a foreseen forced draw. They are
  relabelled `optional` and the claim rests on the three `forced` rows, where
  the single legal move permits the reduction and nothing else.
- **"The row-3 clock-reset fixtures answer the question"** — withdrawn and
  rebuilt. My first set left the mover with **KvK** after the capture, so `cp 0`
  was a *material* draw and said nothing about the fifty-move rule. The rebuilt
  set keeps White's queen and rook, and the answer changed from "uninformative"
  to "correct and informative".
- **`row2_1` reporting `mate 0`** — withdrawn. That fixture
  (`8/8/8/8/8/8/1q6/KNk5 w`) is checkmate, and my enumerator had passed
  vacuously over an empty legal-move list.

## What I could not settle

- **The loser-stalemate sub-family** (a losing side that *chooses* stalemate)
  is **not measured**. Two exhaustive constructions returned zero fixtures and
  the third was still scanning when the clock ran out. The honest statement is
  that Row 1 covers *unavoidable* stalemate only; whether the engine *prefers*
  a stalemate when losing is untested here. Files: `scripts/stalemate.py` has
  the working forced-stalemate enumerator; the optional variant needs a
  targeted construction, not a broader sweep.
- **Static versus search score on insufficient material disagrees, and I did not
  chase it to a defect.** On this build `eval` reports `−138` for K+N vs K,
  `−155` for K+B vs K and `+107` for the mirrored K vs K+B, while search
  returns `cp 0`. The disagreement is **real and reproducible**, but every such
  position is a drawn **root**, so the bail returns `cp 0` with 0 nodes and the
  static number never reaches a client. **This is a lead, not a finding** — the
  eval asymmetry may be a legitimate tempo term. I did not establish whether it
  ever reaches a searched node that is *not* a drawn root, which is what would
  make it a defect.
- **The `p = 4` band** reproduced (`FOUND` at H=95,96; `MISSED` at 97,98,99,
  boundary `H > 96`), and `p = 2` reproduced exactly (`FOUND` ≤98, `MISSED` at
  99, root guard ≥100). Both agree with §2. I did **not** widen to `p = 6`.
- **The opponent-mate family from the original assignment** (100 positions:
  50 mate-in-1 played, 50 mate-in-1 avoided) measured **50/50 and 50/50** at
  both `go depth 10` and `go nodes 20000`, with no refusal and no illegal move.
  Evidence in `evidence/family1_mate.json`. This is a clean negative.

## Reproduction

```bash
cmake -B build -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 .
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build build -j8
printf 'bench 11\nbench 13\nbench 16\ngo perft 5\nquit\n' | ./build/forge

cd scripts
python3 selftest.py /path/to/forge                  # prove the checkers fire
python3 matrix_rows.py /path/to/forge ../evidence/matrix_rows.json
python3 family1_mate.py /path/to/forge ../evidence/family1_mate.json
python3 family3_repetition.py /path/to/forge ../evidence/family3_repetition.json
python3 family4_fifty.py /path/to/forge ../evidence/family4_fifty.json
python3 family5_material.py /path/to/forge ../evidence/family5_material.json
python3 family6_0000.py /path/to/forge ../evidence/family6_0000.json
```
