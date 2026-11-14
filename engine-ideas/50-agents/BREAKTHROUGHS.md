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
