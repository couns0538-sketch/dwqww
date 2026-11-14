# Ethereal

Ideas only. All seven departments are in.

## King safety

Importance: routine. No opened page shows current Stockfish weaker here. The default build scores shelter, storm, and attacker pressure, plus a small pawn-and-king net. Shelter uses only the king’s file and the file on either side. An attacker counts only when it hits the neighborhood on a square defending pawns do not cover twice. The formula stays off until two pieces attack, or one piece attacks and a queen remains. Only the positive part becomes a penalty, squared in the middlegame. Safe-check pressure is P21. The three-file shield as a switch on that penalty is P22. A pawn-and-king residual, which keeps the kings that P9 strips out, is P23.

## Time controls

Importance: routine. The 2022 two-way node signal gained about ten Elo on increment controls and about twenty on a short no-increment session. Stockfish is stronger on the base schedule and on a stable best-move name. It is weaker on the node signal, which only shortens. Lengthening a node-poor best move, requiring nodes before a stable-name discount, and refusing to let a flat score cancel a split are one idea, T12.

## Clean search structure

Importance: routine. This is a way to keep experiments from publishing a score the later phases never see. It is not a pruning formula.

What Ethereal does. One node routine is a fixed phase list. The root is the same routine with early exits off. A quiet horizon is a shorter list, entered only when depth is exhausted and the king is not attacked. The ordering update and a quiet re-search were marked as the dominant phases in the author’s notes at 11.80. Singular verification can mark the parent’s move generator finished, which is a side channel. The preface can rewrite the node’s own depth before any move is searched.

Where Stockfish differs. It also uses one worker routine, a separate quiescence routine, and numbered phases. It can answer from the table only after the static eval. It enters quiescence on any non-positive depth, including check. Singular exclusion is a fresh search that ignores one move and does not finish the parent’s generator. Neither engine has a single commit phase.

Ideas. The commit gate is S17. The verification verdict is S18. The frozen preface is S19.

## Pawn structure

Importance: routine. Current Stockfish is not weaker here. Its net sees pawn squares and an explicit feature for pawn pairs on the same file or an adjacent file. Ethereal’s named rules are more explicit and thinner, and the neural-eval path skips them inside a wide material band.

What is distinctive. A defect is provisional. A pawn that can capture an enemy pawn is not treated as isolated, because the capture can connect it or trade it off. Backward requires a neighbor, an attacked step, and nothing behind, and that case does not also get the connected bonus. There is no island term and no wing-majority term. Open files and blocked pawns only adjust how closed the position is. The large measured gain was a small pawn-and-king net added on top of the hand-written score, about +26 Elo at 10+0.1 and about +23 at 60+0.6, with wide error bars, and the king is inside that gain so the pawn-only share is unknown.

Ideas. The before-versus-after capture class is P7. A healthy wing majority is P8. A pawn-only correction head, with the kings stripped out so this stays out of king safety, is P9.

## Mobility

Importance: breakthrough. See B5.

What Ethereal scores. Each piece’s attacks inside one pawn-filtered area. Captures and friendly squares still count, and bishop and rook reach may pass through friendly sliders. The curves punish a tiny count hard. A second term charges squares attacked once by us and at least twice by the enemy, with no friendly pawn. A bishop is worse when more of our rammed pawns sit on its color. When a network build is on, that net replaces this eval except at an extreme material score.

Where Stockfish is weaker. On empty flights, not on piece-to-piece attacks. The current eval is the network plus a scale. Threat features are real attacks onto a filtered set of pieces. Empty squares are outside that feature. A piece with nowhere quiet to step never appears unless some other piece’s attack lands on a listed target. Removing the whole hand-crafted eval was not a test of an empty-flight feature.

Ideas. Lesser-safe empty flights are B5. Battery reach scored apart from real moves is P12. A restriction penalty only for the piece that cannot leave is P13, and it must not double-count B5.

## Passed pawns

Importance: routine. No opened match shows Stockfish losing to Ethereal on passers. Both trust a net where passers usually decide the game. A 2020 Stockfish test that deleted a half-bonus and scored lever pawns as full passers was about 2 to 3 Elo. The live gap is narrower than the old hand-crafted reputation.

What the fallback model does. It runs only when endgame material is far outside a wide band, so most passer endings never reach it. A pawn is passed when no enemy pawn stands on its path or the adjacent files ahead. A candidate requires every stopper to be a lever and enough helpers on the front square. The value of a real passer depends on whether the next square is empty and attacked. King distance is charged once, for the leading passer on a file. Connected passers, the piece on the blockading square, and promotion races are outside that function.

Ideas. Ordering the quiet lever, with no static bonus, is S16. The path state when material and the net disagree is P10. Two safe adjacent passers are P11.

## Tuning method

Importance: routine. The method beats a game-based tuner only while the played evaluation is still an explicit weighted sum. Once a network is the evaluation, the author wrote that this style of tuning had little room left.

What the method is. Many explicit terms are fit together against the game result. The value the search receives, including the phase blend and a later shrink, is what the derivative sees. A depth-12 quiet band keeps decided positions from owning the scale. One position per game beat many positions from the same game in the author’s account. Reported match gains from the coupled step were about +10, +3.4, and +2.3 Elo, and the joint fit was the smallest. Absolute error did not work. SPSA, by contrast, spends games on each nudge and is a poor way to move hundreds of correlated weights.

Ideas. The wrapper-aware joint step is X1. The quiet band checked on a second book is X2. A game-result target against a search-score target, for explicit terms only, is X3. That last one is not the net mix in D9.

## Sources

https://raw.githubusercontent.com/AndyGrant/Ethereal/master/src/search.c
https://raw.githubusercontent.com/AndyGrant/Ethereal/master/src/evaluate.c
https://github.com/AndyGrant/Ethereal/commit/513a93c23219f2a71b70085c3f88def359399567
https://github.com/AndyGrant/Ethereal/releases/tag/V12.50
https://talkchess.com/viewtopic.php?t=74877
https://www.chessprogramming.org/Texel%27s_Tuning_Method
https://github.com/official-stockfish/Stockfish/pull/2613
https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/evaluate.cpp
