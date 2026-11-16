# WITHDRAWN — S-F32, S-F33, S-F34 (the "wrong move" on the lone-king board)

**Status: WITHDRAWN. There is no ordering flaw on that board on either build.**
The raw measurements are correct and are kept; the INTERPRETATION was wrong.

## The mistake, in one line

I read the sign of a mate score in a LOST position backwards.

## Why that is so, from the engine's own source (not from another seat's word)

`src/search.cpp:211-212`:
```cpp
[[nodiscard]] int mated_in(int ply) { return -MateValue + ply; }
[[nodiscard]] int mate_in(int ply)  { return  MateValue - ply; }
```

So the side to move being mated in `ply` plies scores `-MateValue + ply`. **`ply` grows with distance, so the
score GROWS with distance**: being mated in 20 plies scores HIGHER (less bad) than being mated in 16.

`src/search.cpp:272-279` prints it as `mate -N`, `N = (MateValue - |score| + 1) / 2`, i.e. N is the mate
distance in MOVES for the losing side.

**Therefore `mate -10` is a BETTER score for the losing side than `mate -8`.** Choosing the longer mate is
**maximum resistance** and is exactly what a correct engine does.

## What that means for the reported board

`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` — **White is to move and White is lost** (White has only a king
against rook + bishop + knight). So:

| move | score | meaning | for White |
|---|---|---|---|
| c6c7 | mate -11 | White mated in 11 | **better** |
| c6d6 | mate -8 | White mated in 8 | worse |

The engine plays `c6c7`. **That is correct play.** It survives three moves longer than the alternative.
Same on base, where `mate -13` beats `cp -11.9` for the same reason (a loss scored precisely as a mate is not
worse than an imprecise large centipawn loss).

## What is NOT withdrawn

- The numbers themselves: c6c7 = mate -11 at 16.1M nodes, c6d6 = mate -8 at 142.5M nodes at depth 20 on the
  PC build; base at depth 18 gives c6c7 = mate -22, c6d6 = cp -1192. All correct.
- S-F35 (the reconciliation) and S-F37 (the Hash-32MB / OwnBook-true settings trap) stand: they are about
  measurement hygiene, not about the defect.
- S-F38, the method note: the `searchmoves` score and the free-choice score are not comparable at the same
  nominal depth because they do not search the same tree (seldepth 43 on 16M nodes vs seldepth 37 on 166M
  here). That mismatch is what produced the apparent contradiction in the first place.

## The lesson I am recording for myself

A finding of the form "the engine plays a move it evaluates worse" requires **two** independent things to be
true: that the scores are comparable, and that I know which direction is better. I checked neither before
reporting. The sign of a mate score is worth verifying from source every single time, and a restricted search
is not a free search.
