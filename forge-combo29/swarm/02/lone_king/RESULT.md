# Independent check of the lone-king wrong-move claim — DOES NOT REPRODUCE on this board

Board given to me: `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` — White has a **bare king** (1 man) against four
Black men (rook, bishop, knight, king). Each legal move scored separately with `searchmoves` at depths **16, 18 and
20**, on **both** builds. Threads 1, Hash 16, OwnBook false, PC20 on the PC build and S14 on the base; every search
the first of a fresh process (COLD); interactive driver.

## the board and the moves
python-chess confirms the board is valid: `is_valid() True`, `status() 0`, 1 White man, 4 Black men, halfmove 18.
**Four legal moves**, and every one was scored: `c6d7`, `c6c7`, `c6d6`, `c6c5`.

## the scores (PC r15 + PC20 vs base + S14, Threads 1)

| move | PC d16 | PC d18 | PC d20 | base d16 | base d18 | base d20 |
|---|---|---|---|---|---|---|
| `c6d7` | cp -1146 | mate -14 | **mate -8** | cp -1131 | cp -1131 | cp -1131 |
| `c6c7` | cp -1195 | cp -1195 | **mate -11** | cp -1084 | mate -22 | mate -13 |
| `c6d6` | cp -1173 | mate -9 | **mate -8** | cp -1179 | cp -1192 | cp -1219 |
| `c6c5` | mate -23 | mate -9 | **mate -8** | cp -1121 | cp -1222 | mate -16 |

## what I found, and it is the opposite of a wrong-move defect
1. **The four moves do NOT all score the same**, at any depth on either build: 4 distinct scores at d16 for both,
   and at d20 the PC build has 2 distinct and the base has 4. So the premise that `bestmove` cannot reveal which
   move scored best does not hold on this board — the scores separate the moves.
2. **Every mate score I could fully replay VERIFIES**: 6 of the PC build's 8 mate scores end in checkmate at
   exactly the claimed distance when replayed with python-chess, and the other 2 are TRUNCATED (the engine emitted
   a PV shorter than the claimed distance — a display limitation, not a wrong score). No score was wrong.
3. **The distances improve monotonically with depth**, which is the correct behaviour and the thing that would
   break if the score were fabricated: PC `c6d7` cp -> mate -14 -> mate -8, `c6d6` cp -> mate -9 -> mate -8,
   `c6c5` mate -23 -> mate -9 -> mate -8. A mate distance may shorten with depth; it must never lengthen, and none
   did.
4. **The PC build is BETTER on this board, not worse**: at d20 all four of its moves are scored as mate, while the
   base build still scores two moves as plain cp (-1131 for `c6d7`, -1219 for `c6d6`). So the r15 patch appears to
   improve mate finding here, which is consistent with the `MateAlphaGuard` / bare-king switches file 5 describes.

## verdict: I could NOT reproduce a lone-king wrong-move defect on this board
Neither build plays an illegal move, scores a mate that is not there, or reports a mate that gets longer with
depth. If another seat has a specific claim about THIS board, it is not visible in the four root moves' scores at
d16/d18/d20 — so either the defect needs a different instrument than per-move `searchmoves` scores, or the board
in the claim differs from the one given to me, or the defect is about something other than the root score
(e.g. the move chosen WITHOUT searchmoves, or a node-count anomaly).

**What would settle it:** the reporting seat's exact command and its raw output. I am not able to confirm or
refute their claim from the description alone, and I would rather say so than manufacture agreement.

## the two harness faults I hit first, both caught before any number was recorded
1. My mate-PV check tested `|score| >= 10000`, but this engine reports mate as a DISTANCE (`mate -8`), not a large
   cp value, so the check never fired and every verdict was `None`. Fixed to discriminate on the engine's own
   `score` KIND (`mate` vs `cp`), which is the only reliable signal.
2. Then I misread negative mate distances as "worse with depth" when -23 -> -9 -> -8 is SHORTER and correct. The
   corrected table above is the accurate reading.
