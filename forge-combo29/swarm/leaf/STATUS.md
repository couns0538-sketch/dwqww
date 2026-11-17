# Status — leaf clock-100 mate rule

**State: complete. Verdict SHIP. Pin cost zero.**

| deliverable | state | where |
|---|---|---|
| `FINDINGS.md` | done | `forge-combo29/swarm/leaf/FINDINGS.md` |
| `STATUS.md` | done | this file |
| `patches/` | done | `patches/leaf_clock100_mate.patch.txt`, `patches/leaf_clock100_mate_hpp.patch.txt`, `patches/upstream/` |
| `scripts/` | done | 8 files, all run against the delivered tree |
| `evidence/` | done | pins ×4 builds, band sweep, 40-position delta, 7 families ×3 builds, compose, planted fault |

## The rule

At a node with `halfmove_clock() >= 100`, the old code scored a draw unless the side to move was
checkmated. The fifty-move draw is a **claim** and FIDE 9.3 makes a claim optional, so a move that
mates ends the game before the opponent can claim: a clock-100 node is worth `mate_in(1)` when the
side to move can mate at once, and a draw otherwise. Checkmate itself is still left to the caller's
move loop, so existing mate accounting is untouched.

Old band `p <= 100 - H`; correct band `p <= 101 - H`. The patch closes the one-ply gap for every
mate length, not just for the reported cell.

## Acceptance, all met

1. **`6k1/8/5PPP/8/8/8/8/R6K b` at hm 97/98/99/100** — `mate -1`, `mate -1`, **`mate -1` (was `cp 0`)**, `cp 0` root guard. Control `6k1/5ppp/8/8/8/8/8/R5NK b` stays `cp 0` at every clock.
2. **All 11 lock pins bit-identical** on base, composed, fixed, and fixed ASan+UBSan. The four
   named honesty pins reproduce exactly; ASan+UBSan produced zero sanitizer lines, and
   `scripts/planted_fault.sh` proves the sanitizer was armed on the new function.
3. **Seven adversarial families 7/7** on the fixed build (base 3/7, composed 6/7). Composition
   byte-identical in both orders; reverse-applying the patch restores the shipped `24912a43…` hash.
4. **40 ordinary positions: 40/40 node-and-score identical, max |delta| 0.0000 %** — the fix does
   not search one ply deeper.

## Pin cost

**Zero.** The rule fires only at clock >= 100; no bench FEN reaches one. Measured on four builds,
not argued.

## What is not claimed

- Not "recovers lost games". The brief's bound (1 forced mate in 798 band plies over 792,081)
  stands as the honest scale; my own cruder probe found 0.53% of random-play plies at clock >= 98.
- Does not implement optional-claim semantics in general. Only the one exception the rules compel.
- No `Threads > 1` run of the new path; no MultiPV run.
- The seven families are my own construction from the categories the findings doc names, not the
  original seat's fixture files.
