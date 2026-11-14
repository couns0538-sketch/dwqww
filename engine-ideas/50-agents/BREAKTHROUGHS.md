# Breakthroughs

Idea reports only. Nothing here is an engine change.

Two department reports flagged a possible large strength gain. Both are Leela principles restated for Forge. Neither copies a network, a weight, or a search implementation.

Snapshot: 2026-11-14T11:42Z. Sources are the public pages named under each idea.

## B1. Fading board prior for quiet moves

- Importance: breakthrough
- Engine / department: Leela Chess Zero / policy-guided move ordering
- Also considered: no second agent wrote this mechanism. Visit-count confidence and selective search are related but they spend nodes. This idea only reorders quiet moves.
- Where it would live: the network, as an ordering head beside the value net. The search only reads the score inside the quiet-move group.

What to add. Train a small ordering head while the value net stays frozen. The target is the quiet move a deeper search of the same position preferred: the quiet that caused a cutoff, or the first quiet on the final line. At move-ordering time, add that score only among quiet moves, after hash moves, captures, and killer moves already have their places. Scale the bonus down as this search writes history for that move. A cold node follows the prior. A warm node follows cutoff evidence. Every legal move stays in the list.

Why it might help. A policy prior is a guess, from the piece placement, about where search effort will go. It matters most before any cutoff has been seen. Quiet-move history cannot rank a new idea until something has already cut off. In alpha-beta the first quiet tried decides how often the rest of the list is searched more shallowly. A cheap prior that is right on cold nodes changes that rate across the tree. The fade is the same handoff a visit-based search gets when backed-up results overtake the prior. This is a large gain only if the head is accurate and cheap. It is a small gain if history is already right by the time most nodes are ordered.

Risks. A head that costs a full extra evaluation per node spends the Elo it earns. A prior that never fades fights history after the search has real evidence. Threads that deliberately try different root quiets will collapse onto one favorite if they share an unfaded prior. A head trained on shallow searches copies shallow mistakes. A static piece-square bonus does not test this idea.

What would falsify it. At a fixed node budget, the share of nodes whose first quiet is the move that later cuts off does not rise. Or fixed-time games lose once the head’s cost is included. Or a version that never fades beats the fading version.

Sources:

- https://lczero.org/dev/lc0/search/alphazero/
- https://arxiv.org/html/2508.21380v4
- https://gwern.net/doc/reinforcement-learning/model/alphago/2018-silver.pdf
- https://www.chessprogramming.org/Move_Ordering

## B2. Stable-miss outcome residual

- Importance: breakthrough
- Engine / department: Leela Chess Zero / value networks from self-play
- Also considered: the Stockfish long-term-sacrifice report’s “game-result target on quiet deficits” is the same family, narrower. It upweights quiet positions that stay materially down and then disagree with the material count. Keep that slice as a filter inside this residual, not as a second net. Sources for the narrower slice are listed below.
- Where it would live: evaluation, as a small additive correction on a frozen net.

What to add. Freeze the current net. Play Forge games to a real finish. Keep a position only when the frozen evaluation and the game result disagree in sign for several moves in a row, and a one-move material swing does not explain the disagreement. Train a small additive correction on that set alone. The game result is the only target. At evaluation time, add the correction only when it is large. Every other position stays on the frozen net.

Why it might help. A value trained from finished games can call a position good when no teacher score did, including a sacrifice whose payoff sits past a quiet stretch. Published Stockfish training notes describe the game result as the smaller share of the target, and describe Leela-derived positional labels as strong enough to beat a then-current master net only after a net had first been trained on ordinary search scores. A from-scratch outcome net fights that evidence. A frozen sharp net plus a result-trained correction, used only where the sharp net is stably wrong, is that shape with Forge’s own games. It is a large gain if those stable misses are systematic and a shallow search does not already overturn them.

Risks. A long wrong streak can be a chain of blunders, so the correction learns bad play. The kept set may be small and odd. A large correction can fight the main net and scramble transposition scores. If the main net was already fit partly to results, the correction double-counts them.

What would falsify it. Against the frozen net, the corrected eval does not win a match. Or a shallow search already flips the score on most of the kept positions.

Sources:

- https://raw.githubusercontent.com/LeelaChessZero/lc0/master/src/trainingdata/trainingdata.cc
- https://raw.githubusercontent.com/LeelaChessZero/lczero-training/master/tf/tfprocess.py
- https://github.com/official-stockfish/nnue-pytorch/wiki/Training-datasets
- https://github.com/official-stockfish/Stockfish/commit/c079acc26f93acc2eda08c7218c60559854f52f0
- Narrower material-deficit slice: https://starcraft.ai/documents/260/alphazero_preprint.pdf
- https://stockfishchess.org/blog/2020/introducing-nnue-evaluation
- https://danamackenzie.com/blog/?p=5072

## B3. Clock-gated reductions

- Importance: breakthrough
- Engine / department: Stockfish gaps / short time controls
- Also considered: not the same as a always-on deeper search, and not the same as the bullet clock reserve (that one stays routine). Berserk’s short-time department has not been merged in yet.
- Where it would live: search, in late-move reductions. On the later Forge tree that is `src/search/alphabeta.inc`. The node budget comes from `src/search/timeman.hpp`.

What to add. Before each move, estimate the nodes this clock and the recent search speed will allow. Under a bullet-sized budget, increase late-move reductions so the root can finish another iteration. Above a rapid-sized budget, ease those reductions so the extra nodes look at moves the short search would have cut. When the budget is large, leave the long-control reductions as they are.

Why it might help. A 2020 Stockfish discussion proposed pruning more when few nodes remain and less when many remain. One trial passed the short test and was failing the long test. The same reduction setting is the wrong setting at both clocks. A 1+1 final in CCC 24 was 567.5–432.5 over 1000 games against a near peer, so a policy that only changes the short budget has a match of that size to move. An always-on deeper search is the version that already failed the long test. Stockfish is still the winner at modern short controls. The gap is the search shape, not a missing bullet title.

Risks. The short-test pass has no Elo figure on the issue page. A 10-second game may never reach the “relax the cuts” side, so a bad threshold either never switches or over-prunes a tactic. A deeper tree of worse moves can lose to a shallower sound tree.

What would falsify it. Bullet games, around 1+0.1 or 1+1, do not improve against a fixed opponent and book, or long games, around 60+0.6 or 10+3, get worse while the gate should be off.

Sources:

- https://github.com/official-stockfish/Stockfish/issues/2758
- https://liquipedia.net/chess/Computer_Chess_Championship/24/Bullet

## B4. Conflict-gated steep blend

- Importance: breakthrough
- Engine / department: RubiChess / eval tapering
- Also considered: Koivisto’s pawn-counted phase multiplier and Berserk’s heavy-piece stretch are one-score rescales. This idea needs two opinions that can disagree. Stockfish’s material-agreement scale asks a different question.
- Where it would live: eval. On the later Forge tree, `src/eval.cpp` already keeps a middlegame/endgame pair and a phase taper.

What to add. Keep a middlegame opinion and an endgame opinion. If they agree in sign and are close in size, emit a phase-flat combination so a capture barely moves the blend. If they disagree, give phase a steep vote: stay near one opinion until a short band, then move quickly to the other, so search is not handed the average of two plans. Apply any drawish shrink to the opinion that is about to be abandoned. Leave a passed-pawn term that both opinions like at full size.

Why it might help. A linear mix is harmless when both opinions agree, and it is worst when they conflict. Those positions are the long attacks that lose the ending, and the ugly middlegames that are already a won pawn ending. A compromise score recommends a plan that neither opinion believes. RubiChess always mixes in proportion to one piece weight. The classical blend was removed from Stockfish, which now rescales one network score. A steep, agreement-gated blend changes the move only in the conflict, which is where a large gain would have to come from.

Risks. A steep switch can reintroduce the eval jumps that tapering was meant to remove, thrash the transposition table, and make the search change plans when one piece falls. If the two opinions are noisy, the gate will flip on noise. `NetScale`, the phase taper, and `scale_factor` already rescale the same score. Stacking this on top of those moves every pruning margin.

What would falsify it. On a balanced suite, a proportional mix of the same two opinions scores equal or better, and the steep blend’s extra wins are limited to positions where the two opinions already share a sign.

Sources:

- https://raw.githubusercontent.com/Matthies/RubiChess/master/src/eval.cpp
- https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/evaluate.cpp
- https://www.chessprogramming.org/Tapered_Eval

## B5. Lesser-safe empty flights

- Importance: breakthrough
- Engine / department: Ethereal / mobility
- Also considered: the idle-piece reduction (S6) asks which piece to search. This idea is a training feature for a piece that has nowhere quiet to step. Do not ship both as large negative eval terms.
- Where it would live: the network, as a small extra input. On the later Forge tree that is `src/nnue.cpp` / `include/forge/nnue.hpp`.

What to add. For each knight, bishop, rook, and queen, count empty destination squares that an enemy pawn does not attack and a strictly lesser enemy piece does not attack. Knights care about pawns. Bishops care about pawns and knights. Rooks care about pawns, knights, and bishops. Queens care about pawns, knights, and bishops. Leave out captures, friendly squares, and squares seen only through our own pieces. Give each piece one of three marks: no such flight, one flight, or more. Train those marks as a small extra input beside the existing piece-square or threat inputs. Do not import another engine’s curves or weights.

Why it might help. A trapped piece is a large local error. A single mobility count still calls a piece mobile when its “safe” squares are captures, friendly pieces, or squares a lesser enemy piece attacks. A threat-only net records who attacks whom and never records an empty flight. A piece with nowhere quiet to step never appears unless some other piece’s attack lands on a listed target. A two-bit mark states that fact directly.

Risks. A net that already sees blockers and threats may already approximate the mark, so the extra input can cost speed and add nothing. A square attacked by an equal or greater piece can still be a good move. Search already sees one-move traps once depth is high.

What would falsify it. A matched retrain with the marks fails to beat the same net without them, at equal nodes, on positions where some piece has no lesser-safe empty flight.

Sources:

- https://raw.githubusercontent.com/AndyGrant/Ethereal/0e47e9b67f345c75eb965d9fb3e2493b6a11d09a/src/evaluate.c
- https://github.com/official-stockfish/Stockfish/blob/1e7e6bdeb97669a950b8e4c063770d135f54f55b/src/nnue/features/full_threats.h

## B6. Matched-count exclusion bakeoff

- Importance: breakthrough
- Engine / department: Koivisto / net training pipeline
- Also considered: the stable-miss residual (B2) trains a correction on positions the eval got wrong. This idea does not change the target. It only changes which positions are kept, at a matched count. Stockfish’s capture filter is one arm of the bakeoff, not a separate idea.
- Where it would live: data. On the later Forge tree, `src/datagen.cpp` and `tools/nnue/train_resid_v3b.py`.

What to add. Freeze one pool of self-play games and the trainer. Build several position sets that differ only by which positions are kept, and train one net on each set at the same count. The arms: keep every legal non-terminal position; drop positions whose best move is a capture or promotion; drop only captures that do not lose material; drop positions where a fresh short search disagrees with the stored score. Play the nets against each other.

Why it might help. A published Koivisto account treats the exclusion rule as the difference between a modest net and a much stronger one on one tuner: about 40 Elo with the wrong filter, about 104 after the correction, about 150 on another engine’s positions. Those matches are against an old evaluation, so part of the jump is “a working net.” If Forge’s rule was inherited, this stage can move strength by tens of Elo with the trainer left alone. Stockfish already has a broader pipeline. The experiment is still worth running on Forge’s own pool, because good sets are still chosen empirically.

Risks. Different rules also change which kinds of positions remain, so a win can be coverage rather than the filter. Quiescence already asks the net about quiet positions, so keeping tactical ones can spend capacity on states search rarely scores. The published jump is not a paired filter test.

What would falsify it. At matched counts the nets are within noise, or the set that keeps every legal position is strongest.

Sources:

- https://github.com/Luecx/Koivisto/releases/tag/v5.0
- https://github.com/official-stockfish/Stockfish/pull/4324
- https://github.com/official-stockfish/Stockfish/pull/5090
