# RE-VERDICT of my mate/draw findings under FABLE_TO_swarm_6

Seat 11. File 6 says a repetition or fifty-move draw scored 0 is NOT a defect, because the
owner's match program ends the game at the third occurrence and at the 100th half-move. A cp 0
at a high counter is a defect ONLY when a forced mate ends no later than the 100th half-move:
test the same board at counter 0 with `go depth 20`+, read `mate N`, and require
`2N - 1 <= 100 - counter` AND the real-counter board still cp 0 at that depth.

## What I had claimed, and what it becomes

| my id | what I claimed | file 6 verdict | evidence |
|---|---|---|---|
| **S-C9 / S-F18 / S-F19 / S-P1** (with 21-F9) | "at halfmove 100 a MATE IN 1 is thrown away — the most consequential defect I have checked", plus a text patch (S-P1) | **NOT A DEFECT. Withdrawn as a defect.** At counter 100 the budget is `100-100 = 0` half-moves and a mate in 1 needs `2(1)-1 = 1`, so `1 <= 0` is FALSE — no mate can legally end the game at or before the 100th half-move, and the match program ends the game there. The engine is right to score it a draw. | `checks/inequality_test_pc20.txt`, `checks/defect_hunt_pc20.txt` |
| **S-F10 / S-F11 / S-F12** (the "9-ply-early draw" family, re-checking seat 05's S-F3) | "the fifty-move draw is applied about 9 plies early" / "a horizon effect" | **NOT A DEFECT — the premise was wrong.** I measured *when the score becomes cp 0 as the counter rises*, which file 6 says is correct play. Applying file 6's own test to the two boards I used: KRvK at counter 91 needs a mate in <= 5 (`2N-1 <= 9`); the board's true mate distance is **N=8** (15 plies > 9), so a draw is RIGHT; KQvK at 91 needs N<=5, true **N=6** (11 > 9), also RIGHT. Seat 05's finding (and my confirmation S-C7) should be read as "correct behaviour", not "early". | `checks/inequality_test_pc20.txt` rows 3-4 |
| **S-C7** (my CONFIRMS of seat 05's S-F3) | confirmed the H=91 threshold as a finding | **Stands as a measurement, but NOT as a defect confirmation.** The threshold is real and reproducible; file 6 says it is correct behaviour. I do not retract the numbers, only the implication that something is wrong. | `checks/check_s05_f3.txt` |

## The defect test I now run instead, and its result

`checks/defect_hunt_pc20.txt` — a mate-in-1 board at every counter 0..100, `go depth 20`, PC r15
under PC20, Threads 1, requiring a find wherever `2N-1 <= 100-H` (i.e. every H <= 99):
**all 7 eligible counters find `mate 1` (d1d8 / d8d1) in both colours; 0 defects.**

Base 6b98f217, Threads 1: mate found at H = 0, 90, 98, 99; only H=100 gives cp 0, and at H=100
the budget is 0 so that is correct. **0 defects on base too.**

## Standing corrections
- S-P1 (my text patch "fixing" the halfmove-100 mate loss) is **withdrawn**: there is no defect to
  fix, and file 3 already said the PC repair made a base patch unnecessary. The patch file stays in
  my folder with this note so nobody applies it.
- My STATUS lines calling this "the most consequential defect I have checked" are wrong and are
  corrected here rather than edited away.
- S-F38 / S-F39 / S-F40 (truncated FEN leaving a stale board) are **unaffected** by file 6 — that
  is a UCI input-handling matter, not a draw-scoring matter, and it is the strongest thing I have.
