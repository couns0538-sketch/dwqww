# FILE 6 RECLASSIFIES MY CLOCK-99 THREAD: NOT A DEFECT

Seat 25. Read `FABLE_TO_swarm_6.md` and applied its prescribed test to every board of mine. Build PC r15,
PC20, Threads 1, Hash 16.

## File 6's rule, applied literally

> A cp 0 at a high counter is a defect ONLY when a forced mate exists that ends no later than the 100th
> half-move. Test: the same board with counter 0, `go depth 20` or more, read `mate N`; it is a defect only if
> `2N - 1 <= 100 - counter` AND the board with the real counter still scores cp 0 at that depth.

Why the rule is right and my framing was wrong: the owner's match program **ends the game itself** at the third
occurrence and at the 100th half-move. There is no claim to make and no way for the opponent to decline. In my
S-F20 sequence I showed black "refusing" with `h7h6` - but under the match program the game would already have
been scored drawn at the 100th half-move, before black's reply mattered. My "the opponent can decline" premise
came from human FIDE claiming rules, which do not govern the owner's matches.

## The test on my boards (counter 99, budget = 100 - 99 = **1 half-move**)

| board | counter-0 score at depth 24 | 2N-1 | <= 1? | real-counter score | defect? |
|---|---|---|---|---|---|
| `r4rk1/pp1b1ppp/4p3/3pP3/... w` | cp -185 | - | - | cp 0 | NO |
| `r4rk1/1pR4p/p1b1pbp1/5p2/... w` | cp -255 | - | - | cp 0 | NO |
| `2r3k1/5pb1/4q1np/5Np1/... b` | cp -357 | - | - | cp 0 | NO |
| `8/5pk1/4p3/3nK1p1/... b` | cp -56 | - | - | cp 0 | NO |
| `8/3n2Q1/2k4p/8/... b` | cp -2472 | - | - | cp 0 | NO |
| `8/8/4k3/3rp1RR/... w` | cp -387 | - | - | cp 0 | NO |
| `8/8/4K1k1/8/4N1P1/... w` | cp +34 | - | - | cp 0 | NO |
| `2R5/4P3/r7/... b` | cp -481 | - | - | cp 0 | NO |

**0 of 8 boards survive.** None of them has a forced mate at any distance, so a cp 0 there is correct under the
match-program rules. At counter 99 the budget is one half-move: only a mate-in-1 would qualify, and none of these
boards has one.

## What this means for my findings

| finding | status after file 6 |
|---|---|
| S-F3, S-F4, S-F5, S-F11, S-F12, S-F13, S-F14, S-F15, S-F16, S-F17, S-F18, S-F20 | **NOT A DEFECT** - reclassified. The measurements are all correct and reproduce; the *judgement* that they were faults was wrong, because a match program ends the game at the 100th half-move so the score 0 is right. |
| S-F19 (remove the fifty-move test) | **withdrawn** - already withdrawn by my own A/B; now also unnecessary, since there is nothing to fix. |
| S-F22 / S-F23 (refusable-aware repair) | **not to be pursued** - file 6 says seat 12's claimable-draw patch is not to be pursued for the same reason. My repair fixes a "bug" that is not a bug. |
| S-F21 (the 323 cp / 408x risk measurement) | **still valid as a measurement**, and now it matters the other way: it shows that acting on the misclassification would have been harmful. It stands as evidence against the change, not for it. |
| S-F1, S-F8, S-F9, S-F10 (mate-score errors) | **unaffected** - these are wrong mate NUMBERS at normal counters, unrelated to the fifty-move rule. S-F1/S-F8 were also shown REPAIRED on the PC build. |
| S-F6, S-F7 (mate 0, 64 phantom lines) | **unaffected** - terminal-root reporting, not the fifty-move rule. File 6 does not address them. |
| S-F11 (reachability by a 99-ply walk) | still a true statement about legal play; no longer a defect claim. |

## The correction I owe the record

I built an entire thread - mechanism, cost, two repairs - on a premise that file 6 shows is wrong for the
owner's actual match program. The measurements in that thread are sound and reproduce; the interpretation was
not. Three things I would keep from it: the instrumentation method (it found the true chain, and it is what
let me answer this so quickly), the A/B discipline (it is what caught my own bad repair), and the withdrawal
habit. What I would drop is the severity language I used, especially "the engine pretends to draw and the
opponent refuses", which describes human rules and not the owner's matches.
