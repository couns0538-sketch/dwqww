# S-F3 WITHDRAWN — correction by seat 11

## What I claimed
In `REPORT_job1.md` and `FINDINGS.md` I wrote S-F3: "REFUTES the brief's known line: an
impossible-castling FEN is now REFUSED, not accepted."

## Why it is withdrawn
`handoff/fable-opus-combo29-all-20261114:forge-combo29/soak_all/FABLE_TO_swarm_1.md`
lists under ALREADY KNOWN:

> FEN: an impossible castling right is accepted and trusted (perft 3 differs from
> python-chess's 8,802 on the same board: the engine 8,902).

The brief says a FABLE_TO_swarm file can only make the rules stricter, and Opus's statement
is from the PC. I cannot outrank it with a cloud build, and my evidence does not actually
contradict it.

## What my evidence really shows (nothing contradictory)
I tested two DIFFERENT things and conflated them.

1. **A castling right with no king/rook on the home squares** — the engine REFUSES this
   outright (`invalid FEN: castling right without king and rook`, board.cpp:313). Cases
   k1–k3, k6–k9, k11, k12 of `job1/castle2_run/`; d4/d7/f6 of `job1/castle_run/`.
   This is a *different* input from "a reachable-looking position whose rights are
   impossible in a game", and refusing it is not the claim Opus is making.

2. **Rights that are structurally present but game-impossible** (king/rook on home squares,
   squares between blocked, king in check, rights on the wrong side to move) — here the
   engine and python-chess agree on every case I could construct:
   `job1/castle_battery.txt` — 12 comparable cases, **0 differences**, including kiwipete
   (97862 = 97862) and startpos (8902 = 8902).

So: I found no case where accepted-and-trusted rights give a wrong perft. Opus's 8,902 vs
8,802 example is a *specific board Opus used* that I have not reproduced; its difference is
presumably a legality rule python-chess applies that this engine does not (most likely
castling out of / through check on a board I did not hit, or a rights combination my battery
did not contain). I am NOT claiming Opus is wrong. I am saying my test did not reach the case.

## Standing correction
- S-F3 as written in `FINDINGS.md` is WRONG and is marked withdrawn in place.
- The remaining true statement is narrow and NOT new: "castling rights with no king/rook on
  the home squares are refused" — this is stricter input validation than the brief implies,
  but it is not a defect and Opus has already covered the real castling issue.
- My S-F2 (consecutive digits) is ALSO already known per Opus's first bullet
  ("17" and "44" read as 8 empty squares). It is not NEW; it is at most a confirmation.
  My only addition beyond Opus is the *proof of harmlessness*: the accepted non-canonical
  rank yields the identical board (perft 4 = 1870 both spellings), so it is cosmetic, not
  corrupting. That refinement is what I keep.
- My S-F1 (extra tokens after the sixth FEN field are silently discarded) is NOT in Opus's
  list and stands as NEW.
