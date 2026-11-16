# DRAWN-ROOT DOORS: base tree vs the PC tree — NO drawn-root patch from this swarm is needed on the PC tree

**One sentence for the reader in a week: do not apply seat 01's patch, seat 12's patch, seat 28's patch or
any other drawn-root patch from this swarm to the PC tree — the PC's own engine already repairs every door,
as measured below on the PC r15 build under PC20.**

## The table — pasted output of `doors_side_by_side.py` (`doors_side_by_side_out.txt`)

| door | base: bestmove | base: score | base: nodes | PC20: bestmove | PC20: score | PC20: nodes | requirement | verdict |
|---|---|---|---|---|---|---|---|---|
| door A1: mate in 1, halfmove 100 | f2f3 | cp 0 | 0 | a1a8 | mate 1 | 252 | must find the mate | PC20 FIXED |
| door A2: mate in 1, halfmove 150 | f2f3 | cp 0 | 0 | a1a8 | mate 1 | 252 | must find the mate | PC20 FIXED |
| door A3: counter-resetting pawn mate, halfmove 100 | h6h7 | cp 0 | 0 | h6h7 | mate 2 | 398 | must find mate 2 | PC20 FIXED |
| door B1: mate in 1 on the third repetition | f2f3 | cp 0 | 0 | a1a8 | mate 1 | 240 | must find the mate | PC20 FIXED |
| control C1: mate in 1, halfmove 99 (always worked) | a1a8 | mate 1 | 252 | a1a8 | mate 1 | 252 | must find the mate | both OK |
| control C2: K v K (genuine automatic draw) | a1b1 | cp 0 | 0 | a1b1 | cp 0 | 0 | may answer at once, 0 nodes is correct | unchanged |
| control C3: KQ v K at halfmove 150 (claimable draw) | h6c1 | cp 0 | 0 | h6h2 | cp 0 | 336 | score must stay cp 0 | unchanged |

## What the two doors are

Both live in `src/search.cpp`, in the `root_drawn` shortcut at about line 2250 of the base tree:

```cpp
const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                           board.is_insufficient_material());
if (root_candidates.empty() || root_drawn) { /* report without searching */ }
```

- **Door A — `halfmove_clock() >= 100`.** Fifty-move is a draw a player may CLAIM, not an automatic one.
  The shortcut answers the first legal move with **0 nodes**, so a mate on the board is missed. Covers
  A1, A2 and A3 above; A3 additionally needs the counter to be reset-capable (a pawn move).
- **Door B — `is_repetition()`.** Threefold is likewise claimable. Same 0-node answer, same missed mate.

## Why the PC tree needs no patch

FABLE_TO_swarm_3 records that the PC's engine has searched such roots like any other since 15 November,
with only insufficient material still answered at once. That is exactly what the table shows: every one of
A1/A2/A3/B1 SEARCHES on PC20 (240-398 nodes) and returns a mate score, while C2 (K v K, a genuine
automatic draw) still answers from the shortcut in 0 nodes and C3's score stays `cp 0`.

## What is base-tree only, and therefore still worth a decision

| my finding | what it says | status on the PC tree |
|---|---|---|
| S-F5 / S-C1 | a mate in one at halfmove 100 is not found on the base tree | **repaired** on PC20 — no action |
| S-F4 | the same door exists through `is_repetition()` | **repaired** on PC20 — no action |
| S-F17 | my 5-line patch closes both doors on the base tree | **must not be applied** to the PC tree |
| S-F18 | claimable vs automatic draws, the shape of the defect | explanatory only |

If a base tree is ever used for analysis or a match, ONE of the three competing base-tree fixes is still
needed there — seat 01's `job2c` combined patch, seat 12's bypass, or mine. See `README.md` for the
comparison and my own preference. On the PC tree: none of them.

## Provenance of every number here

- **base**: `~/build/base-release/forge`, sha256 `e06310ec…16a83`, Release GCC 13.3.0, commit `6b98f217`,
  Threads 1, Hash 16, OwnBook false, S14 also sent (harmless on base).
- **PC20**: PC r15 build, patch sha256 `d6bd72c531f785f4…` verified, exe sha256 `068f0927768d30be…`, built
  with `-DFORGE_MATE_ALPHA_GUARD=1`; S14 + CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true,
  MateAlphaGuard true, OwnBook false, Threads 1, Hash 16.
- `go depth 12` for every row, `ucinewgame` + `isready` before every search, every bestmove checked for
  legality with python-chess. A rejected option stops the run with an error rather than being skipped.

## How to see it again

```
cd forge-combo29/swarm/28/pc20
python3 doors_side_by_side.py ~/build/base-release/forge ~/build/r15-pc/forge /tmp/doors
```

Raw: `out_doors/doors_side_by_side.tsv`.
