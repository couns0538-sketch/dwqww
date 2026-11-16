# Attempt to cover NEGATIVE mate scores (job 9's stated gap) — NOT COVERED, and why

## What I tried (all timed out or found nothing, so nothing is claimed)
Job 9's report says plainly that `mate < 0` (the engine being mated) has **no coverage**. I tried to
close that gap and could not do it efficiently. Recording the attempts so nobody repeats them.

1. **Swap the side to move on a known white-to-move mate position.** Taking
   `8/8/5K2/8/8/7k/8/6Q1` (white forces mate in 3 plies) and giving BLACK the move gives black 1 legal
   move, but python-chess reports **no forced mate** for white from there — the mate was a
   first-move-only tactic, so the swapped position is not a losing position at all, it is a draw-ish
   king shuffle. Same for the other two I tried. So "swap the side" does not produce a losing position.
2. **King+queen vs king-and-queen, black to move, searching placements exhaustively.** A black queen
   gives black enough counterplay that a *forced* mate against it is rare, and the exhaustive
   mate-distance search over 64x64x64 placements with a queen on the board did not finish inside the
   command limit (timed out at 200 s).
3. **Black with very few moves (h1/a1/h8 corners).** Found only positions that are already checkmate
   or stalemate, or where the black king has exactly one move and the "mate" evaporates — i.e. not a
   usable negative-mate test.

## Why this is genuinely hard (worth recording)
A **forced mate against a side that has its own material** is much rarer than a forced mate in a bare
king ending, and the reference computation (exhaustive over all defences) is exponentially more
expensive when the defender has a queen or rook. My job-9 construction relied on the defender having
almost no material, which is exactly the case where no counterplay exists and the mate is forced
quickly. The same property that made job 9 clean makes negative scores hard to reach.

## What I will NOT do
I will not report a negative mate score as "tested" on the strength of the one candidate I built that
turned out to have no mate in it, and I will not weaken the definition of "forced mate" to manufacture
cases. The gap stands and is stated in S-F11's limit line and in REPORT_job9.md.

## What would close it (for whoever has the time)
Feed real game positions where one side is already lost — from actual lost games rather than
constructed endings — and record the score sign at the match budgets. Engine-vs-engine games at a
large material deficit would supply them cheaply. That is the route I would take with a longer window.
