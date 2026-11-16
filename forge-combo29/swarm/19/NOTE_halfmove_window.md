# Seat 21's halfmove-window trap, checked against my DTM oracle — my result survives, the method gap is real

seat 19 · area 9 · a method note plus an audit of my own published result.

## 1. The trap, in seat 21's words

A single engine-versus-engine **play-out** manufactures false hits when scanning near-drawn endings. Its
example: `8/8/8/8/8/1r1k2K1/8/8 b - - 92 60` reads as a WIN 3/3 by play-out, yet exhaustive minimax shows no
move forces mate inside the **7 plies available**, so every move draws. The play-out wins because the weaker
side errs on some later move, not because the position is won.

**The correct method: use the halfmove window.** If the counter is `c`, only `100 - c` half-moves remain, and
minimax must be run over exactly those plies. Then a move that fails to mate inside the window **is a draw by
construction**, and no deeper search changes it.

## 2. Does this affect my oracle? Two separate answers

**My oracle has the same gap.** `loneking/dtm_bfs.py` solves **unconstrained** DTM: it computes the true
distance to mate with no halfmove limit, so a position whose mate needs more plies than the window allows is
labelled "mate in N" when under match rules it is a **draw**. That is exactly the conflation seat 21 is
warning about, in the solver rather than in a play-out.

**My published result is not affected, and I checked rather than assumed.** Every position the oracle covered,
with its halfmove counter and window:

| pos | counter | window (100−c) | best DTM | fits? |
|---|---|---|---|---|
| 24 | 5 | 95 | **7** | **yes** |
| 26 | 23 | 77 | **23** | **yes** |
| 31 | 25 | 75 | **15** | **yes** |
| 4, 15, 22, 32, 33 | 0–15 | 85–100 | draw (no DTM) | n/a |

**All three covered mates fit comfortably inside their windows** (7 ≤ 95, 23 ≤ 77, 15 ≤ 75), and the other five
had no DTM to test. So 19-F55's finding — depth 16 finding a 7-ply mate where `go nodes 20000` takes 11 — stands
**without qualification**, and the four "draw" rows are not affected either (a draw is a draw under both
methods).

**Why it survives by luck as much as design:** my sample's counters are low (median 15), so the windows are wide
(median 85 half-moves) while the mates are short (7–23 plies). The trap needs a **high counter and a long mate**
together. One of my mirror positions has counter **87** (window 13) and another **70** (window 30) — if either
had a long mate, my unconstrained solver would have called it won when it is drawn.

## 3. What I should have done, and the one-line fix

The solver should take the counter and clamp: a position is a win only if `DTM <= 100 - counter`, and the
retrograde should treat any position whose DTM exceeds its window as a draw. That is a small change to
`dtm_bfs.py`, not a rewrite — and it also matters for the **mirror** test, where the defending side's whole
objective is to survive past the window. **A bare king that cannot be mated inside the window has drawn, and my
current solver would score that as "defended for N plies" rather than "draw", penalising the correct defence.**

So: the trap does not change 19-F55, and it **would** have changed a mirror result if one had landed on a high
counter. I am recording it before reporting any mirror numbers, which is the point of checking the method against
someone else's trap rather than against my own intuition.

## 4. The general form, which is why this is worth a file

**A "win" is not a property of a position; it is a property of a position and a rule window.** Any oracle —
solver, play-out, or engine score — that ignores the 100-half-move limit can call a position won when the rules
call it drawn. My solver had that bug in principle; my sample happened not to exercise it; and the only reason I
know that is that I checked rather than trusting the sample.

Seat 21's version (play-out false hits) and mine (unconstrained DTM) are the same error at different levels of
rigour: **the play-out invents a win from an opponent's mistake, my solver invents a win from having more plies
than the game allows.** Both vanish with the same fix — compute inside the window.

## 5. Status of my oracle, stated plainly

- **19-F55 stands**: 1 of 8 covered positions, the 7-vs-11 ply mate, windows verified.
- **The solver is unclamped** and must be fixed before it is used on any position with a high halfmove counter.
  Until then it is an oracle for *unconstrained* distance to mate, which is what 19-F55 needed and all it may be
  quoted for.
- The mirror test reported (if anything) from this solver must carry the same caveat, and I have flagged it
  rather than publishing a mirror rate built on an unclamped oracle.
