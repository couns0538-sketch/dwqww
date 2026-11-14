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

## B7. Bullet completed-iteration stop

- Importance: breakthrough
- Engine / department: Berserk / short-time-control strength
- Also considered: B3 changes reductions with the node budget. This one refuses to start an iteration the clock cannot finish. Test them separately. The bullet reserve in T10 is a cap on one move’s share, not this stop.
- Where it would live: time (`src/search/timeman.hpp` on the later tree).

What to add. Use this only when the starting clock is bullet-scale, about 8 seconds with an increment under a tenth. Do not start another iteration unless the time already used says that iteration can finish. Hold back at least one increment. Play the last finished iteration.

Why it might help. On the Computer Chess Index sheets dated 14 November 2026, Stockfish’s lead over Berserk 14 widens at 8.0+0.08 seconds (about 188 Elo on one sheet, 128 and 125 on the others) and is much smaller at 60 seconds and at 2m24s. An unfinished last iteration is a larger share of an 8-second game than of a two-minute game. The author’s 2022 point was that time which the strength does not earn back is a loss. Stockfish is still ahead at every short control opened. The candidate is the widening of that lead as the clock gets short, on the order of 100 Elo, not a claim that Berserk beats Stockfish at bullet.

Risks. Most of the gap may be strength per node. Pruning, the net, and move ordering are other departments. Stopping early misses a late change of move. A reserve that is too large makes every move too shallow.

What would falsify it. A paired 8.0+0.08s match does not gain, or the same policy gains a similar amount at 60+0.6 and at 2m24+1.12. Also falsify if forfeits are already near zero and completed depth does not rise.

Sources:

- https://raw.githubusercontent.com/computer-chess-index/cci/main/engines/Berserk.md
- https://raw.githubusercontent.com/computer-chess-index/cci/main/engines/Stockfish.md
- https://www.chessengeria.eu/post/interview-with-jay-honnold

## B8. Threat-role memory

- Importance: breakthrough
- Engine / department: Koivisto / history heuristics
- Also considered: Berserk’s four from-to buckets remember “any attack” versus none, then add a flat bonus. That cheaper-attacker class table is the routine companion S28, not this idea. Do not add a from-to table per threatened square.
- Where it would live: search (`include/forge/history.hpp`).

What to add. A small statistic indexed by threat kind (attacked piece type and attacker piece type) and by the quiet’s role: the attacked piece steps away, another piece blocks, the quiet attacks the attacker, the quiet creates a greater threat, or none of these. Update it when that quiet is the best move or fails high, and when the eval swing shows the threat was answered. In positions with this threat, add the statistic to ordering, pruning, and reductions, and remove the piece-value-sized bonus for merely stepping off the attacked square. When no such threat exists, ordinary continuation history stays in charge.

Why it might help. The published Koivisto advantage is remembering which quiet worked against the current threat, including a quiet by a piece that is not the one in danger. Its table splits that evidence across squares and learns only from cutoffs. Stockfish’s threat prior can outvote from-to history, pawn history, and one continuation entry for running with the attacked piece, and it never learns that a block or a counter was the defense that worked. A role index is small, fills early, and can correct that prior.

Risks. Running away is often right, so deleting the static bonus can lose more than the memory gains. Role labels will be wrong for discoveries and pins. If one role dominates, the statistic becomes a new constant bias.

What would falsify it. In positions with a lesser-piece attack on a greater piece, the first quiet searched is not a cutoff more often than with the static step-off bonus left in place. Also falsify if adding the role term on top of that bonus matches replacing the bonus.

Sources:

- https://raw.githubusercontent.com/Luecx/Koivisto/master/src_files/history.h
- https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/movepick.cpp
- https://chessprogramming.org/History_Heuristic

## B9. Surplus-thread root auditors

- Importance: breakthrough
- Engine / department: RubiChess / thread scaling
- Also considered: a high bar that lets one deeper helper override the main move is the weaker form of the same selection rule. It is not a second idea. Koivisto’s wider draw jitter and private correction tables stay routine.
- Where it would live: search (`src/search/searcher.inc`).

What to add. Keep ordinary lazy SMP for the first 16 threads, one per distinct depth schedule. Every thread beyond that is an auditor. Assign each auditor a root move that currently has a low share of nodes, and search that move with a wide window. An auditor may change the played move only when its result is as deep as the leader and several auditors agree. Widen the clock when auditors disagree with the leader, and shorten it when they agree. Leave the first 16 threads on the full root list.

Why it might help. Depth diversity aliases early: RubiChess repeats schedules from thread 17, and Stockfish’s aspiration offset repeats from thread 9. Extra threads then rewrite the same lines. Published Stockfish figures still show about half the nodes wasted at 64 threads on a long budget, and about 18 percent of the Elo of eightfold time missing at 8 threads. Spending the duplicate threads on neglected root moves attacks that waste. RubiChess times the move from the main thread alone, so a helper can become the played move after the time was already spent.

Risks. Auditors can pollute the shared table with shallow bounds. Below 16 threads the rule should stay off. A wide-window side move costs as much as a main-line search and can lose Elo at short controls.

What would falsify it. On 32-thread and 64-thread self-play, nodes on the eventual best root move are already spread across threads, or the auditor version does not beat plain lazy SMP by more than the error bar. Also falsify if an 8-thread run, with auditors disabled, changes strength at all.

Sources:

- https://raw.githubusercontent.com/Matthies/RubiChess/master/src/search.cpp
- https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/search.cpp
- https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html
- https://anemato.de/blog/nuca

## B10. Depth-normalized effort repayment

- Importance: breakthrough
- Engine / department: Koivisto / singular-extension style
- Also considered: Koivisto’s “half the nodes, one extra ply” fail-low mark is the crude version of this signal. Do not ship that flag and this repayment together. Singular verification that returns a verdict without touching the parent generator stays S18.
- Where it would live: search (`alphabeta.inc`). Singular extensions are already there.

What to add. When a node finishes, score each move by nodes spent divided by the depth that move was actually given. If one move’s rate clearly beats the next, remember it as critical even when the node failed low. On the next visit, give that move back depth that reductions had withheld, in proportion to how dominant the rate was, with a hard cap on repaid depth from the root. Do not treat raw node share as the signal. The first move is searched deeper than the rest, so it will look dominant even when it is ordinary.

Why it might help. Both engines mostly detect an only-move from a score gap. The moves that still get missed are the ones reduced before anyone notices they are the only try, including defenses that fail low but are expensive to refute. Koivisto stores a half-the-nodes flag and adds one ply off the PV. Stockfish never stores effort dominance. Paying back withheld depth, normalized so the first move does not win by default, is the hole neither closes.

Risks. The flag can still collapse to “extend the first move.” Repaid depth can chain. Fail-lows in lost positions will attract the same extra depth as real hidden defenses.

What would falsify it. After dividing by depth searched, the flag almost never fires, or it fires on the same moves as raw node share. Or, at a fixed node budget, tactical suites and match score do not improve while average path depth grows.

Sources:

- https://github.com/Luecx/Koivisto/blob/master/src_files/search.cpp
- https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp
- https://www.chessprogramming.org/Singular_Extensions

## B11. Surplus-scaled verification depth

- Importance: breakthrough
- Engine / department: Berserk / search reductions
- Also considered: RubiChess restores the entire omitted depth whenever a shallow score beats alpha. That full restore is one arm of this test, not a separate idea. The one-ply hindsight shave stays routine.
- Where it would live: search (`alphabeta.inc`).

What to add. When a reduced zero-window search beats alpha and its depth is below full depth, always verify that same move. Start the verification one ply above the reduced depth. Give back more of the withheld plies as the reduced score rises further above the current best score, and give all of them back once the surplus is large. Cap the verification at ordinary full depth, plus at most the single extra ply both engines already allow for a clearly high reduced score. Leave the PV’s first move on a full-window search.

Why it might help. Both engines pay for a near-full second search and only nudge it by one ply, so the size of the surprise is discarded. A barely-high reduced score is the expensive, low-confidence case. A clearly-high score is the case that deserved the depth the reduction withheld. The second search is a large enough part of late-move reduction that a better split could matter more than another one-ply constant.

Risks. A tactic whose reduced score only just clears alpha stays shallow for that iteration. Stacking this with a one-ply shave can leave a recovering quiet without enough depth. Neighboring verification depths will alias into the same transposition entry.

What would falsify it. A fixed one-ply step matches the scaled rule on a long time control, or the scaled rule loses the winning move in quiet tactical positions where that move’s reduced score only barely beats alpha.

Sources:

- https://raw.githubusercontent.com/jhonnold/berserk/main/src/search.c
- https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/search.cpp

## B12. Miss-weighted on-policy refresh

- Importance: breakthrough
- Engine / department: Berserk / data generation for nets
- Also considered: B6 freezes one pool and compares filters. B2 trains a residual where a frozen eval and the result disagree. D9 changes the mix weight where two labels disagree. This idea regenerates the games from the current engine and spends the deep label on disagreements. Do not run it as a second copy of B6.
- Where it would live: data (`src/datagen.cpp`, `tools/nnue/train_resid_v3b.py`).

What to add. Play the training games with the current Forge engine. Build each opening with a short random legal preamble of both parities, and reject it only when one finished search already shows a decisive score, several pawns rather than one. Choose the move with a modest search that is allowed to finish its iteration. Store a deeper finished search as the target, but keep a thin sample where the two scores agree and a much larger share where they disagree. On the next net, retire positions the new engine no longer reaches. Leave captures, checks, and the early middlegame in the set. Thin early plies only enough that one game cannot fill the batch.

Why it might help. A net inside search is asked to score the leaves that search reaches. The published Berserk habit is to train on its own just-played games and later drop another engine’s games. A 2026 Stockfish recipe refreshes labels on a large, largely foreign set, then drops captures, checks, and almost all of the early game. Those deleted positions are where a shallow look and a deep look disagree. For an engine that does not already own tens of billions of historical positions, matching the live search should matter more than inheriting old games. This is a large gain only if that match beats both a relabeled foreign pack and a uniform skip of the same games.

Risks. Published notes say Leela-derived sets beat Stockfish self-play, and that a cleaner label can be harder to learn. A small on-policy set with a shallow teacher can lose to a large off-policy set. Disagreement weighting can flood the batch with tactics quiescence should resolve. One Berserk release credited the trainer, not the data.

What would falsify it. At equal position count, with the same trainer and the same net shape, this set fails to beat both a relabeled off-policy pack and the same on-policy games kept uniformly under a late-ply skip schedule.

Sources:

- https://wiki.chessdom.org/Berserk_questionnaire_20251013
- https://github.com/jhonnold/berserk/releases/tag/8
- https://github.com/official-stockfish/nnue-pytorch/wiki/Training-datasets

## B13. Sibling-backed quiet extinction

- Importance: breakthrough
- Engine / department: Berserk / aggressive pruning
- Also considered: a fixed tight futility cushion is the version this idea refuses. History drops that remove one move stay a different experiment.
- Where it would live: search (`alphabeta.inc`).

What to add. After a quiet has actually been searched and missed alpha by a wide margin, drop every remaining quiet in that node, including on non-root PV nodes. Until a searched quiet has missed widely, keep a wide cushion and judge each quiet on its own. Once one or two quiets have missed widely, switch to a cushion on the order of one pawn at one ply and under three pawns at five, and end the quiet list. Keep captures and queen promotions. Keep the tail while the best score is still a mate-scale loss, and keep it in pure king-and-pawn positions. Leave killers and the countermove exempt.

Why it might help. Quiet moves are most of the tree. A published engine already lives with a tight cushion and a list that dies early, including on PV nodes, while Stockfish uses a much wider per-move cushion and refuses that drop while following the PV. A fixed tight cushion will cut a late quiet that is the only good one. Switching on the misses already seen uses search evidence, so the tight rule fires when the node is behaving like an all-node.

Risks. A good quiet ordered late is never searched. PV lines move around more. Stacking this with history drops and exchange drops can over-prune. The pawn-ending exemption gives nodes back where the net is already reliable.

What would falsify it. At the same node count the new search loses on quiet tactical positions, or losses cluster where the only holding quiet was later than the second quiet tried. Also falsify if the node count barely changes, which means the wide-miss switch almost never fires.

Sources:

- https://github.com/jhonnold/berserk/blob/main/src/search.c
- https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/search.cpp

## B14. Searched endgame calibration

- Importance: breakthrough
- Engine / department: Koivisto / endgame eval
- Also considered: E3 is a phase multiplier on the whole game. V6 judges a trade by which side of the edge the resulting ending is on. This idea only rescales positions whose material count is already below the display curve’s floor. Do not stack it on E3.
- Where it would live: eval (`src/eval.cpp` and the scale in `src/search/evaluation.inc`).

What to add. When a 1/3/3/5/9 material count is below 17, drop the agreement boost. Rescale the value search compares so its magnitude matches tablebase win rate for that remaining material. The scale’s inputs are the five piece counts, which side holds the last rook, which side holds the last bishop, and one bit for whether a lone bishop shares the pawn’s color. Fit those on 5-man to 7-man win, draw, and loss. Leave the network alone.

Why it might help. A piece-typed scale that stays inside the searched score keeps moving after the heavy pieces are gone. The outcome-fitted curve used for display stops at material 17 and does not enter search. The scale that does enter search grows a score that already agrees with material. On a drawn bishop-and-pawn ending that is the wrong direction. A December 2025 dev note showed depth-1 scores near −550 centipawns on tablebase draws of that family, and said the class of mistake should generally be fixed by a better network, and also that a map of which static scores are wrong would be useful. Those nets are not the current master. If the current scale still does this, search will trade material and refuse draws for a result that is drawn.

Risks. Pruning margins and the fifty-move fade assume today’s magnitude. A change that only fixes the printed centipawn will not change games. A material class that is usually drawn still contains wins. This becomes a fortress search if it starts scoring piece placement beyond material and the bishop-color bit.

What would falsify it. On current master, a sample of 5-man to 7-man tablebase draws below material 17 is already near zero after the existing scale, or a match of the new scale against the unchanged scale stays inside noise. Also drop it if the gain vanishes while the fifty-move fade is left untouched.

Sources:

- https://raw.githubusercontent.com/Luecx/Koivisto/master/src_files/board.cpp
- https://github.com/official-stockfish/Stockfish/blob/master/src/evaluate.cpp
- https://github.com/official-stockfish/Stockfish/issues/6481
