PROPOSAL F1: every "not weaker at 2,000 soft nodes" check in the plan (the tune's match (3), A4's switch, N7's
bundle, the 2-billion gate of N5) is played as an SPRT between "3 Elo weaker" and "level", not as a fixed number
of games with a bar on the interval's lower end or on the point value.

KIND: explanation (arithmetic anyone can redo), with a test.

EVIDENCE:
- The width of an interval at this depth is measured: 6,000 games at 2,000 nodes gave +/- 7.5 (PLAN J6:
  "+79.2 +/- 7.5"). So the standard error at 6,000 games is 7.5 / 1.96 = 3.83, at 4,000 games 4.69 (+/- 9.2).
- N1's bar ("6,000 games, point at least 0 AND lower bound at least -3") therefore needs a MEASURED +4.5 or
  more. A change that is truly level passes with probability 1 - Phi(4.5 / 3.83) = 12 %; a change that is truly
  +3 passes with 35 %. The same bar at 4,000 games (N5, N7, and what I wrote for A4) needs a measured +6.2:
  a level change passes with 9 %. These bars do not test "not weaker"; they demand a gain and mostly refuse.
- The tune's declared bar for the same question ("4,000 games, point value not below -5") errs the other way:
  a change that is truly 5 Elo weaker passes with 50 %, one that is truly 10 weaker with 14 %.
- An SPRT with H0 = -3 and H1 = 0 (alpha = beta = 0.05) accepts a level change with 95 % and refuses a change
  3 weaker with 95 %, and it stops by itself when the difference is large (the last tuned set moved this depth
  by +79). Expected length when the truth is exactly one of the two: about 2.94 x 2 x 0.165 / 0.00432^2 = 52,000
  games (a third of the games drawn; a 3 Elo step is 0.00432 of a point); less with paired openings.
- Cost: self-play makes 5,818 searches a second on the PC's 16 threads at this depth and a game has about 128
  searched plies: about 45 games a second of pure search, so 52,000 games are about 20 minutes of search. Through
  the match runner it has not been timed: "under an hour" is an estimate.

COST: no card. At most about one processor hour per check where 4,000 to 6,000 games were planned (minutes).
For the tune's match (3) it is an addendum to the tune's declaration, which is allowed only before that match
has a result (none of the five has started; the tune is at 33,375 of 40,000 iterations).

HOW IT IS JUDGED:
- The rule: SPRT, H0 = -3 Elo, H1 = 0 Elo, alpha = beta = 0.05, paired openings, cap 100,000 games. H1 = holds.
  H0 = does not hold. At the cap with neither: holds only if the 95 % lower bound is above -3.
- Before it is used: the runner is shown to decide both ways on known answers. A against A (level by
  construction) must end H1; A against A with a node handicap whose cost is not in doubt (the weaker side at
  1,000 soft nodes, half the nodes) must end H0. Both runs are kept as raw files.
- The margin -3 is the number N1, N5 and N7 use at this depth (J4 uses it at 250,000 nodes and names no number at
  2,000). If the owner or Opus want another margin, the form stays and only the number changes.

WHAT WOULD CHANGE MY MIND: a measured interval at 2,000 soft nodes that is much narrower than +/- 7.5 at 6,000
games (then the fixed bars are less harsh than computed here); or the wish that the tuned values must show a
GAIN at self-play depth, not just no loss: then the bar is an SPRT [0, 3] and the plan says "gain" in words.
