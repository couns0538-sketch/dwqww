# Leela Chess Zero

Ideas only. The WDL department has not reported yet. Fortress and plan reports already use the public WDL write-up; see V1.

## Policy-guided move ordering

Importance: breakthrough. See B1.

What Leela does. On a new position the network writes a probability for every legal move. Search walks the move with the highest sum of the average backed-up outcome and an exploration term proportional to the prior. Untouched moves are ordered by that prior. The prior is trained to imitate where search spent its effort. The ranking is kept soft so an underrated move can still be early. Training runs have used a larger exploration term at the root than inside the tree.

Where Stockfish is weaker. The published description is alpha-beta plus hand-designed ordering, with a neural net used as an evaluation, not as a move-probability head. At a freshly reached node, captures and moves that have already cut off somewhere can be ordered. A new quiet idea has no placement-based rank until a cutoff has been seen. No page opened here measured how often today’s Stockfish misses a quiet only because it lacks a prior. The weakness is the missing signal.

Ideas. The fading quiet prior is B1. The softer root weight is N1. Retiring the prior when a cutoff disagrees is N2.

## Value networks from self-play

Importance: breakthrough. See B2.

What Leela does. The value target is the finished game, written when the game ends, from the side to move. A mix with the value after search exists and is published as optional, with a long config comment that leaves the weight at zero so the target stays the game result. Search still chooses which positions are worth learning, by preferring records where the no-search value and the post-search value disagree. A later change cuts a game when the move played was much worse than the best move. The prefix then gets a stand-in from that best move’s search value. No external engine writes the value label.

Where Stockfish is weaker. This is not a match-strength claim. The recorded training target is the evaluation along the way. Depth 9 is described as the sweet spot for that generator. The game result is a second input. Published master-net recipes keep the result as the smaller share, ending near 0.7. Notes say Leela-derived sets carried more positional evaluations and produced better nets, and that training from scratch on only those sets worked worse. The published gain came from a better teacher score, with the result as a minority correction.

Ideas. The stable-miss residual is B2. Piece-count outcome weights are V3. Suffix-only outcome labels are V4.

## Selective search versus full-width

Importance: routine.

What Leela does. A visit budget with no nominal depth. Each visit walks the edge that currently scores highest, evaluates a new leaf, and backs the value up. The move played is the root edge with the most visits. Reported depth is an average. Selective depth is the deepest line. An exploration constant widens or deepens the tree and is built to grow as visits accumulate, after a constant value locked onto one move at large node counts. The root has its own copy so the root can stay wider. An unvisited edge gets a placeholder that becomes more pessimistic as more siblings are touched. A root move that cannot become best in the time left is dropped. Under parallel evaluation, an in-flight visit counts as visited and the backed-up value stays unchanged.

Where Stockfish is weaker. In the long, narrow, non-forcing setting. The 2017 time-scaling figure shows selective search pulling further ahead of Stockfish 8 as thinking time grew. Those matches are the whole system, not this mechanism alone, and the Stockfish setup was disputed by its author. Stockfish is already selective inside a depth quota: the first moves are searched fully, later moves more shallowly, and a shallow fail-high is searched again. The quota remains. That quota loses in long quiet plans and wins when every plausible move needs a real search. After the neural leaf, the opened record has Stockfish winning the listed superfinals from Season 19. A full swap to Monte-Carlo search is the wrong experiment. The useful piece is the budget: a wide shallow look, then a deep trunk.

Ideas. The long-clock live set is S1. The zero-visit interior is S2. Unscored in-flight visits are T8.

## Visit counts as confidence

Importance: routine.

What Leela does. The played move is a visit vote. The signal that stops the clock is a catch-up test: if the remaining time cannot buy enough visits to close the gap between first and second, stop. A factor above 1 stops earlier. The same comparison drops hopeless root moves. The default clock itself budgets time from the ply and a game-length curve, then banks whatever the catch-up test did not spend. A check that stops when the visit distribution stops moving exists and defaults to off. A time manager that spends a reserve when a challenger’s recent rate would pass the leader was the default, then put back.

Where Stockfish is weaker. It already has a confidence clock: the budget stretches when the best move changes or the evaluation falls, and shrinks when the same best move has lasted and when almost all nodes sit on that move. The node-share term only bites once the best move holds roughly three quarters of the nodes, inside a narrow band. It does not ask whether the remaining nodes could change the move, and it has no split between “searched most” and “best score,” because those are the same move.

Ideas. The slope stop is T1. Banking time on a frozen distribution, including a tie, is T2. Holding the clock while the effort leader and the value leader differ is T3.

## Opening variety

Importance: routine.

What Leela does. Variety is a training schedule. Temperature 0 plays the best move. Dirichlet noise is a training device on a policy prior and does not transfer onto a value-only net. The schedule that spreads openings uses a temperature that waits, then decays, an offset on visit counts before the sample, a value cutoff, and an absolute first-play value at the root so each untried root move looks urgent until it is searched. Deeper in the tree, unvisited moves look worse than their parent. Match defaults do not copy the root rule. AlphaZero’s evaluation play was greedy. Its training play sampled in proportion to root visits.

Where Stockfish is weaker. In the 2018 comparison Stockfish’s variety was an external book. A secondary match that let a book choose Stockfish’s openings was very similar to the bookless match, and more than 90 percent were draws. Forcing the selective engine to sample, for 30 plies, only among moves within 1 percent of the best value raised the reported winning rate in that setting from 5.8 percent to 14 percent. A footnote says the extra variety also produced more losses. This is the 2018 report only.

Ideas. The near-tie sample is O1, shared with the Stockfish variety gap and Dragon’s variety knob. Book-exit training games are O4. The opening clock hold is T4.

## Positional sacrifices

Importance: routine. The annotated games are against classical Stockfish in 2019 and early 2020. From the first neural-evaluation superfinal, Stockfish is the stronger engine, and the sacrifice difference sits inside matches Stockfish won.

What Leela does. The value after material has been given, when the compensation is piece activity or a changed structure. A linear probe of one network’s last body layer separates a material label and also separates mobility, space, and pawns, so activity and structure are readable beside material. Season 15 game 61 is a blocked kingside that ties pieces to one wing. Season 17 games give pawns for a file, a square, or a bad bishop’s diagonal. The same value missed a long forcing sacrifice on a corrected puzzle that Stockfish solved.

Where Stockfish is weaker. Classical Stockfish was the weaker judge in those two superfinals. Season 20 annotations of the neural Stockfish show both outcomes: a strategic pawn idea only Leela produced, a piece-for-pawns hold by Stockfish that Leela’s activity compensated, and an unsound pawn gift by Leela. A 2021 description says the neural net was trained to predict a classical evaluation at moderate depth. Whether that is still the training target was not checked, because the project’s own announcement did not load.

Ideas. Piece credit before a compensation term is P1. Cross-wing binding is P2. The one-pawn cap is P3.

## Sources

https://lczero.org/dev/lc0/search/alphazero/
https://lczero.org/dev/lc0/search/lc3/overview
https://lczero.org/play/configuration/flags/
https://lczero.org/play/flags/
https://lczero.org/blog/2020/04/tcec-s17-super-final-report
https://lczero.org/blog/2020/03/lc0-v024-has-been-released/
https://arxiv.org/html/1712.01815v1
https://arxiv.org/html/2508.21380v4
https://training.lczero.org/training_runs
https://github.com/LeelaChessZero/lc0/pull/721
https://github.com/LeelaChessZero/lc0/issues/684
https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
https://tcec-chess.com/articles/Sufi_20_-_Sadler.pdf
https://en.wikipedia.org/wiki/Leela_Chess_Zero
https://github.com/official-stockfish/nnue-pytorch/wiki/Training-datasets
https://starcraft.ai/documents/260/alphazero_preprint.pdf
