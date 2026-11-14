# Deduped ideas

Ideas only. Each item is written once. Departments that hit the same mechanism are named together. Breakthroughs are specified in [BREAKTHROUGHS.md](BREAKTHROUGHS.md) and only summarized here.

Importance is routine unless the item is marked breakthrough. “Where” is the kind of module. The Forge path map is not in yet.

## Breakthroughs

### B1. Fading board prior for quiet moves

Breakthrough. Leela policy ordering. Net. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

### B2. Stable-miss outcome residual

Breakthrough. Leela self-play value. Eval. The Stockfish long-term-sacrifice report’s game-result labels on quiet material deficits are a filter inside this residual, not a second model. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

## Search allocation

### S1. Long-clock live set

- Sources: Leela selective search. https://arxiv.org/html/1712.01815v1 https://lczero.org/blog/2020/04/tcec-s17-super-final-report https://lczero.org/play/configuration/flags/
- Where: search
- What to add: One shallow pass over every legal root move, then spend the rest of a long clock only on root moves the remaining time could still promote. Widen the band as nodes grow. Drop a move the clock cannot catch. Log selective depth, average depth, and dropped moves.
- Why: Extra time is where selective search pulled ahead of the 2017-era full-width engine, and the published wins were long positional games.
- Risks: A quiet move can jump after it is dropped. A thin floor loses short tactics.
- Falsify if: At a long time control the match does not beat the unchanged engine, or the eventual best move was dropped before the last look more than rarely. Also drop it if a tactical suite at the same node budget loses more than the long games gain.

### S2. Zero-visit interior

- Sources: Leela selective search. https://lczero.org/dev/lc0/search/alphazero https://lczero.org/dev/lc0/search/lc3/overview https://lczero.org/blog/2020/03/lc0-v024-has-been-released/
- Where: search
- What to add: Keep the root on the full-width floor in S1. Below the root, give an unsearched quiet move a placeholder equal to the parent score minus a penalty that rises with siblings already searched. Give it no nodes while that placeholder cannot raise alpha. If the parent’s visit count later clears alpha, search it then. Checks and captures stay on the normal path.
- Why: The saved nodes go into the trunk, which is the gap between average depth and selective depth.
- Risks: The parent score is a bad stand-in in zugzwang and only-move positions. A quiet move that starts a tactic is the known failure of a thin tree.
- Falsify if: On a quiet-tactic set, zero-visit moves include the move that would have changed the root choice more often than in the unchanged engine, or fixed-node matches lose.

### S3. Plausible-reply band

- Sources: Komodo Dragon hybrid search. https://www.chessdom.com/komodo-mcts-monte-carlo-tree-search-is-the-new-star-of-tcec/ https://komodochess.com/store/pages.php?cmsid=14 https://en.chessbase.com/post/komodo-dragon-2-is-here
- Where: search
- What to add: On the first few plies only, score legal replies with a very short search and treat that score as a chance. Replies close to the leader keep a full-depth search. Replies that fall clearly behind take a harder reduction. Shrink the band once the leader’s chance stops moving. On many threads, keep some threads off the single hottest line, and cap work on weak replies. The main search still chooses the move.
- Why: The published hybrid looked widely, then narrowed, and was about seventy Elo behind its own alpha-beta in engine matches. The band tries to buy the allocation only where the top replies are still close.
- Risks: A wide band burns depth. Too much work on bad lines loses strength. A short probe is weakest in tactics.
- Falsify if: At equal time the match score is flat or negative, or a tactical set loses solutions while reported depth falls.

### S4. One root record for several lines

- Sources: Komodo Dragon hybrid search. https://komodochess.com/store/pages.php?cmsid=14 https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html https://komodochess.com/dragon-3.3.htm
- Where: search
- What to add: Store an outcome chance for every root move inside the search that is already choosing the best move. When several lines are requested, read them from that record. Feed a second root move only while its chance stays close to the leader.
- Why: Published Stockfish 15.1 figures put four lines far behind one line at 60 seconds plus 0.6. The Dragon claim is that the extra lines are already in the tree. That claim is backed by an older MultiPV match, not by a current one.
- Risks: Diverting nodes after the gap is clear can worsen the best move. A gain at four lines can coexist with a loss at one line.
- Falsify if: At four lines and equal time, the move named best matches a long one-line search no more often than a split-budget search, or one-line match Elo drops.

### S5. Nothing-to-play ordering

- Sources: Komodo Dragon positional patience. https://journals.sagepub.com/doi/pdf/10.3233/ICG-2014-37116?download=true https://talkchess.com/forum/viewtopic.php?t=56895
- Where: search
- What to add: If a shallow search of only captures and checks agrees with the quiet evaluation within a small margin, search quiet piece moves that raise the side-to-move evaluation before pawn breaks and sacrifices, and reduce those piece moves less than usual for that one node. Leave the break in the list. Change order and reduction only.
- Why: The published picture of patience is a break prepared after a stretch with nothing to play, inside the search that holds up against engines.
- Risks: The break may already be right. A lost position looks like “nothing to play.” A wide margin becomes a refusal to force the opponent’s best move.
- Falsify if: On a fixed set of quiet middlegames the patched search matches a deep reference less often, or a balanced match loses Elo.

### S6. Idle-piece reduction

- Sources: Komodo Dragon positional patience. https://en.chessbase.com/post/the-komodo-files-working-with-a-chess-engine https://komodochess.com/dragon-3.3.htm
- Where: search
- What to add: Only in a position already judged quiet by S5, drop each friendly piece once from a copy of the position and read how far the network evaluation falls. For one iteration, do not apply the usual late-move reduction to quiet non-capturing moves of the piece whose removal changes the evaluation least.
- Why: The published aim is to improve the piece that is doing nothing before the break, read from the trained evaluation rather than from a new activity term.
- Risks: A piece can be cheap to remove because it is spare. Probing every piece costs time.
- Falsify if: Moves that escape reduction are no more often the deep-search best move than quiet moves of the other pieces, or the probe’s time cost exceeds the nodes it saves.

### S7. One extra ply for a quiet move inside a tied band

- Sources: Stockfish strategic-plans gap. Related to S1 and S2, but this one only disables futility and late-move pruning for one ply. https://official-stockfish.github.io/docs/stockfish-wiki/Terminology.html https://chessprogramming.org/Futility_Pruning https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
- Where: search
- What to add: If a quiet move’s static score is inside a narrow band of the best score so far, skip those two prunes for that move and search it one ply deeper. Keep both prunes outside the band, and for captures, checks, and moves that drop material.
- Why: Those prunes assume a quiet move will not raise a static score that is already behind. That is the condition under which a plan is invisible.
- Risks: A loose band searches quiet moves in general and gives away tactical speed. One ply is a short gift next to a lag that lasted many moves in the published game.
- Falsify if: Logs show the exception almost never changes the root move, or the moves it changes are tactical shots the next ordinary iteration also finds.

### S8. Delayed score inside a tied root cluster

- Sources: Stockfish strategic-plans gap. Distinct from S7: this spends extra plies on a cluster that has stayed tied across iterations, with quiet pruning off. https://wiki.chessdom.org/TCEC_Season_15_Superfinal_Game_61_%E2%80%93_Stockfish-Leela https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
- Where: search
- What to add: When the leading root moves stay inside a narrow static-score band for more than one iteration, search only that band for a few extra plies with quiet-move pruning off. Play the move whose score leaves the band.
- Why: A cheap test of whether the miss is only depth. In the published game the structure was already the story while one engine’s score stayed at 0.00.
- Risks: The band is common in equal positions. More of the same evaluation can stay on the wrong side of zero, as the larger kibitzing engine did in that game.
- Falsify if: On that structure and on other published flat-score plans, the deeper unreduced score selects the same root move, or a match with the rule on scores worse whenever it changes a move.

### S9. Extra plies while the extra material is idle

- Sources: Stockfish long-term sacrifices. https://arxiv.org/html/1712.01815 https://www.chess.com/terms/alphazero-chess-engine https://www.chess.com/news/view/13th-computer-chess-championship-leela-chess-zero-stockfish
- Where: search
- What to add: After checks and captures are resolved, if the side to move is down an exchange or a piece and the opponent’s idle force is large, extend that line by a small fixed number of plies, or reserve a fixed fraction of root time. End the extension when the material comes back or the activity gap closes.
- Why: A piece-for-pawns position can be quiet for a long time while the extra piece stands off the game. The extension spends nodes on that shape alone.
- Risks: A raw mobility count fires in many lost positions. The horizon can move by the length of the extension.
- Falsify if: The extension changes the chosen move on only a negligible share of a curated sacrifice set, or a fixed-time match loses more in balanced positions than it gains on that set.

### S10. Shrink a score that only shuffles

- Sources: Stockfish fortress gap. https://github.com/official-stockfish/Stockfish/commit/cd0b8b4cf28208fffef931322749205a0ddc6066 https://chess.stackexchange.com/questions/24867/bad-stockfish-evaluation
- Where: search
- What to add: In quiet nodes where the pawn score has stayed large and almost flat while both sides only shuffle, run a short probe that forbids pawn moves and captures for the side that is supposed to be winning. If that probe cannot change the score, and the defender has a shuffle or a repetition, shrink the node toward equality. No second evaluation function and no list of fortress shapes.
- Why: A high score that only shuffles was already treated as suspicious in a 2020 author change. The hand-made eval that change consulted is gone, so the check has to be a search probe.
- Risks: Many real wins are quiet before one pawn break. An unconditional probe should be expected to lose strength.
- Falsify if: The probe fires about as often on known slow wins as on known blocked draws, or a match loses more in long conversions than it saves in stuck scores.

### S11. Probe margins from the net’s leftover error

- Sources: Komodo Dragon hybrid search. Not a Stockfish weakness on the pages opened. https://en.chessbase.com/post/komodo-dragon-2-is-here https://komodochess.com/store/pages.php?cmsid=14
- Where: search
- What to add: Measure how far the network score still moves after a quiet one-ply and a quiet two-ply search. Set the shallow prune margin and the late-move reduction from that leftover movement. If S3 exists, give the probe its own pair of margins. Leave the main-search margins unchanged until each pair has its own match.
- Why: A published search retune replaced margins that had been fit to an older eval. Worth doing only if Forge’s margins were fit to an older eval.
- Risks: A second fit on a book the search was already tuned on can lose Elo. Changing the probe and the main search in one patch makes a loss impossible to assign.
- Falsify if: The leftover error does not line up with positions where the current reductions miss a tactic, or the new margins lose a match to the current margins.

## Time

### T1. Stop from the visit slope

- Sources: Leela visit confidence. https://github.com/LeelaChessZero/lc0/pull/721 https://github.com/LeelaChessZero/lc0/blob/master/src/search/classic/search.cc
- Where: time
- What to add: Keep a short history of how root effort is arriving. Stop when, even with an optimistic boost to each challenger’s recent rate, none of them reaches the leader before the hard limit. Do not assume every remaining node lands on the runner-up. Refuse the stop until each contending move has been tried at least once.
- Why: A worst-case gap waits out a runner-up that is no longer receiving nodes. The slope ends that tail. The first-try floor is there because a buried move can sit at zero and then jump.
- Risks: A late tactical burst still loses if the floor is too weak. Optimism large enough to catch that burst recreates the wait.
- Falsify if: At the same average time, the slope stop plays a different move from a full-budget search more often than the worst-case gap stop does.

### T2. Bank time when the root distribution freezes

- Sources: Leela visit confidence. https://github.com/LeelaChessZero/lc0/issues/684 https://github.com/LeelaChessZero/lc0/pull/721
- Where: time
- What to add: On a fixed interval, compare root effort shares with the previous snapshot. If the shares barely move, end the move and store the unused time, even when the top two counts are close. If the shares are still moving, or the leader changed, draw that store up to the hard limit. Keep the game’s total budget matched to a flat per-move budget.
- Why: An early-stop that only fires when one move is far ahead never returns time from a stable tie.
- Risks: A frozen distribution can be frozen on the wrong move. An informal Elo figure mixed this idea with a higher ceiling on hard positions.
- Falsify if: With equal total effort per game, the adaptive schedule does not change results against a flat budget.

### T3. Hold the clock while the effort leader and the value leader differ

- Sources: Leela visit confidence. https://raw.githubusercontent.com/LeelaChessZero/lc0/master/src/search/classic/stoppers/smooth.cc https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp
- Where: time
- What to add: At the ordinary stop point, log the most-searched root move and the best-score root move, then continue to a much larger budget on the same position. Only if that log shows the split marks unfinished decisions, refuse the early stop while the two leaders differ.
- Why: A visit search can disagree with itself. A depth search’s best score and most-searched move are the same object, so it cannot see this split. Hold the clock only for the split.
- Risks: If the long search almost always stays with the early leader, the hold burns clock. A hard limit that is already tight steals time from later messy positions.
- Falsify if: Disagreement is rare at real budgets, or the longer search matches the early effort leader and the early value leader about equally.

### T4. Root hold while a near-equal rival is thin

- Sources: Leela opening variety. Distinct from T3: this one is about a thin node share inside a small score gap in the opening, not about two different leaders. https://lczero.org/play/flags/ https://training.lczero.org/training_runs
- Where: time
- What to add: In the opening, do not let a stable best move shorten the soft clock while another root move inside a small score gap still has only a thin share of root nodes. Give that rival a minimum share, then allow the normal stop. Keep the hard limit. Leave move ordering unchanged. Still play the best finished score.
- Why: A clock that stops as soon as one move owns most of the root nodes can freeze the opening on the first move that looked good.
- Risks: The hold spends the opening budget on moves that never catch up.
- Falsify if: At a short time control on a fixed opening suite, the played move and its score do not change, or they change and a paired test is lost.

### T5. Zero-increment pace

- Sources: Komodo Dragon time management. https://www.talkchess.com/forum3/viewtopic.php?t=56171 https://komodochess.com/store/pages.php?cmsid=14
- Where: time
- What to add: Keep the current plan when there is an increment. Use a separate, slower fraction only when the increment is zero. Tune it at game-in-one-minute and at one long sudden-death control. Count forfeits apart from the game score.
- Why: An increment-tuned schedule that forfeited in sudden death was slowed toward a rival’s pace and gained from fewer forfeits, with a small residual gain even when forfeits were ignored.
- Risks: Less time means less depth. The published spread was wide, so some setups barely moved.
- Falsify if: Forfeits are already rare, and the slower fraction loses Elo at both zero-increment controls.

### T6. Spend the surplus while the result is still open

- Sources: Komodo Dragon time management. https://talkchess.com/forum3/viewtopic.php?t=52464 https://komodochess.com/store/pages.php?cmsid=14
- Where: time
- What to add: When the score has stayed beyond a wide decisive band for more than one completed iteration, cut this move’s soft target and hold the unused time for a later move whose score is still near equality. If the score falls out of the band, restore the normal target up to the hard cap. Leave the endgame and the first move out of book on the normal plan.
- Why: Extra time in positions that are already decided was called a poor use of the clock. A longer first post-book think failed a first test.
- Risks: A shallow score can look decided and then collapse.
- Falsify if: Positions that reach the band are drawn or lost more often with the cap, or the time saved is still on the clock when the game ends.

### T7. Lag margin apart from speed

- Sources: Komodo Dragon time management. https://komodochess.com/store/pages.php?cmsid=14 https://www.talkchess.com/forum3/viewtopic.php?t=73124
- Where: time
- What to add: Measure the delay between deciding a move and the clock actually stopping, and set the safety margin from that measurement. Leave the usage fraction unchanged. On a repeating control, log time used on the move before the control and on the first move after it resets.
- Why: Overhead and “how fast to play” were published as different controls. A long-lived bug in repeating controls was called out as its own item.
- Risks: A margin larger than the real delay shortens every think.
- Falsify if: Matching the margin to measured delay leaves the forfeit rate unchanged, and the repeating-control log shows no pile-up at the boundary.

### T8. Unscored in-flight visits

- Sources: Leela selective search. https://lczero.org/dev/lc0/search/alphazero https://lczero.org/dev/lc0/search/lc3/overview
- Where: search, for how workers share one position. Listed with time because it is about parallel effort, not about the clock.
- What to add: When several workers search one position, count a node that is being searched as already visited and leave its score unchanged until the result returns. The target is a few moves holding most of the nodes.
- Why: Treating an in-flight visit as a loss scatters workers onto lines the selective rule had already ranked lower.
- Risks: Workers pile onto one line and the extra cores add little finished work.
- Falsify if: With several workers, finished new positions fall enough that the match score drops, or the root distribution flattens to equal effort per legal move.

## Openings and style

### O1. Near-tie opening choice

- Sources: Leela opening variety, Stockfish opening-variety gap, Komodo Dragon variety and personalities. Written once. https://starcraft.ai/documents/260/alphazero_preprint.pdf https://lczero.org/play/flags/ https://github.com/official-stockfish/Stockfish/issues/2721 https://komodochess.com/store/pages.php?cmsid=14 https://github.com/official-stockfish/Stockfish/pull/3575
- Where: search at the root, optionally fed by a book table.
- What to add: After a finished search, and only for the first few dozen plies, choose among root moves whose finished score is inside a narrow band of the best. A clear leader is always played. Optional: weight the near-ties by how each move has scored in Forge’s own games, starting from a flat table, with one seed per game so the game can be replayed. Optional style directions inside the same band: keep the attack and the queen, prefer an open position and decline a level trade, or prefer a closed solid move. Default is the best move. Do not write a sampled move back as the search’s best score.
- Why: A fixed position and one thread repeat the same move. Published randomization that is allowed to pick a worse move exists to weaken play. Personalities that leave the network were published as costing about a skill level. A band the search already refused to separate is the narrower experiment.
- Risks: A band wide enough to create real branches loses Elo. Weights from a small match follow noise. On many threads the knob can add little beyond thread noise.
- Falsify if: From the start, at a long time control, the banded version scores clearly worse, or 100 games still produce about as few distinct lines as always playing the top move. Also drop a style direction that loses more Elo than a budget fixed before the match, or that fails to move the matching counts (queen trades, captures, repetitions, openness).

### O2. Opening-only structure tilt

- Sources: Stockfish opening-variety gap. Distinct from O1: this changes the evaluation, not the choice among tied moves. https://komodochess.com/store/pages.php?cmsid=14 https://www.cruxis.com/chess/manual/game_play.htm https://matthewsadler.me.uk/engine-chess/stockfishs-opening-repertoire/
- Where: eval
- What to add: One small constant tilt toward a single opening feature, such as keeping the central tension, applied only for the first 16 plies. Keep the network. Pick the size by a match against the untilted engine. Offer two signs so a match can be assigned one repertoire before move one.
- Why: A published style method changes the move by changing the evaluation. A tilt small enough to survive a match, and switched off once the opening is over, is a narrower version.
- Risks: A tilt large enough to change the opening may just be a worse eval. A tilt that is too small leaves the repertoire unchanged.
- Falsify if: The tilted engine loses a clear Elo margin to the untilted engine, or the two signs still produce the same opening through ply 10 in a 100-game bookless run.

### O3. Prepared-line exit

- Sources: Stockfish opening-variety gap. http://mytcecexperience.blogspot.com/2022/12/season-23-noomen-extra-bonus-opening.html https://matthewsadler.me.uk/engine-chess/stockfishs-opening-repertoire/
- Where: data, consulted at the root.
- What to add: Keep a short list of lines opponents have already played. When the game is still inside one of those lines and the root has a second move inside the O1 band, play that second move once, then return to the best move. At most once per game, and only in the opening.
- Why: A published count recorded a long repeat in two games of one booked opening. A one-time exit aimed at a line already seen attacks that repetition.
- Risks: The second move can be the mistake. An opponent can walk the stored line to force the exit.
- Falsify if: Against an opponent that always plays the stored reply, the exit does not score better than the first move, or against an opponent that leaves the line immediately, the exit scores worse.

### O4. Book-exit games, best-score labels

- Sources: Leela opening variety. Training only, not match play. https://training.lczero.org/training_runs https://lczero.org/blog/2021/04/joking-ftw-seriously/ https://ar5iv.labs.arxiv.org/html/1712.01815
- Where: data
- What to add: For the next net only, start self-play from a book of distinct positions. After the book exit, allow the O1 sample. Record the search’s best score on those early positions, and down-weight game-result labels for about the first 50 plies. Rated play stays greedy and bookless.
- Why: Wide opening coverage in the public training schedule came from sampled, often book-started games, while the searched best move was stored separately from the move that was played.
- Risks: A book can imprint a narrow style. Discounting early plies throws away real opening-result signal. The published check was small and not exhaustive.
- Falsify if: A net trained this way does not beat a same-architecture net trained on the same number of positions from the current mix, in a paired short-time test, and its greedy move from the start is no more varied across repeated games.

### O5. Must-win choice near the draw

- Sources: Komodo Dragon playing style. https://komodochess.com/store/pages.php?cmsid=14 https://github.com/official-stockfish/Stockfish/pull/3575
- Where: search
- What to add: A must-win or must-draw root switch. Near the draw boundary, prefer a searched root move that complicates when this side must win, or that simplifies when a draw is enough. A clear win or a clear loss keeps the objective move. The clock and the training set stay unchanged.
- Why: A published Armageddon rule treats repetitions, fifty-move draws, stalemate, and bare-king trades as losses for the must-win side. A contempt adjustment for a neural net was tried and removed. Restricting the choice to positions the net already calls drawish is a small test. Rescoring a net for Armageddon is a different experiment.
- Risks: The side can refuse its only drawing repetition, or simplify into a loss.
- Falsify if: When a draw counts as a loss for the switched side, its result against the default engine is no better, or it refuses a simplifying conversion from a clear win.

## Value and drawishness

### V1. Outcome head that may contradict the pawn score

- Sources: Stockfish fortress gap and Stockfish strategic-plans gap. One head, two uses. https://lczero.org/blog/2020/04/wdl-head/ https://github.com/official-stockfish/WDL_model https://official-stockfish.github.io/docs/stockfish-wiki/Stockfish-FAQ.html https://tcec-chess.com/articles/Sufi_17_-_Sadler.pdf https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
- Where: net
- What to add: A small head that predicts win, draw, and loss from how games end, not from the pawn score. Leave the pawn score as the search value. Two uses, tested separately. Fortress use: if the position is quiet, the pawn score is large, and this head says the game is very likely drawn, pull that leaf toward equality. Plan use: when root pawn scores lie in one narrow band, break the tie toward the move that most raises win chance relative to loss chance. Keep the fortress discount off in checks, captures, and lines where the score is still swinging.
- Why: A single pawn score folds a draw in as half a win, and a published display curve gives the same draw chance to two positions with the same score and the same material. A dead draw and a sharp equal position are not the same. A published superfinal game sat on 0.0 while the other engine still gave both sides winning chances.
- Risks: A head trained to copy the pawn net never changes a move. A global discount draws slow wins. The post-NNUE match record says this was not championship-sized.
- Falsify if: On quiet positions that stayed high-score and then drew, the head does not give a higher draw chance than the material-adjusted curve. Or a match restricted to positions where the head disagrees scores worse than always playing the pawn-score move.

### V2. Mine high-score draws

- Sources: Stockfish fortress gap. Distinct from B2: this fine-tunes the main target on one slice, instead of adding a frozen-net residual. https://stockfishchess.org/blog/2020/introducing-nnue-evaluation https://github.com/official-stockfish/Stockfish/commit/6deb88728fb141e853243c2873ad0cda4dd19320
- Where: data
- What to add: From self-play, keep only positions where the search score stayed above a winning threshold for a long quiet stretch and the game still drawn. Fine-tune on that slice with the game result as the target. Leave sharp positions on the ordinary teacher-score target.
- Why: The published trainer mixes a teacher score with a result, and the score dominates. Fortress rows are where the teacher says win and the result says draw.
- Risks: The slice contains games drawn by later mistakes. A small slice can be memorized.
- Falsify if: Evaluations on the mined quiet draws do not move toward equality, or evaluations on a held-out set of sharp wins drop by a similar amount.

### V3. Piece-count outcome weight

- Sources: Leela self-play value. https://raw.githubusercontent.com/official-stockfish/nnue-pytorch/master/docs/nnue.md https://github.com/official-stockfish/Stockfish/commit/c079acc26f93acc2eda08c7218c60559854f52f0
- Where: net
- What to add: Keep the stored evaluation as the target in the output buckets for crowded boards. In the buckets for few pieces, put most of the target weight on the game result. One schedule per bucket, not one schedule for the whole net.
- Why: A finished-game label is a weak hint early and a strong one late. A single mix that never lets the result dominate leaves the endgame buckets on the evaluation.
- Risks: Late buckets can memorize mishandled endings. The two targets can disagree at the bucket boundary.
- Falsify if: On held-out endgame positions, outcome error does not fall, or an endgame match against the unchanged net does not gain.

### V4. Suffix outcome only

- Sources: Leela self-play value. https://github.com/LeelaChessZero/lc0/issues/1308 https://github.com/LeelaChessZero/lczero-training/issues/197
- Where: data
- What to add: Walk each finished game backward from the result. Stop the outcome label at the last move that was clearly worse than the engine’s best move at the time. Positions before that keep the teacher evaluation and get no outcome term. Do not fill that prefix with a search value.
- Why: Replacing the prefix with a search value protects the opening from one bad move and also puts a search score back in as a stand-in result. Dropping the prefix outcome is the narrower job.
- Risks: The labeled tail can be short and trivial. Judging “clearly worse” with a net that is also being trained is circular unless that net is frozen.
- Falsify if: A whole-game outcome label predicts held-out results as well as the suffix label, and the suffix-trained net does not win a match against the whole-game version.

### V5. Context scale as a disagreement flag

- Sources: Stockfish long-term sacrifices, from published material-imbalance counts, not from a copied table. https://www.chess.com/article/view/the-evaluation-of-material-imbalances-by-im-larry-kaufman https://chessprogramming.org/Stockfish_NNUE https://lczero.org/blog/2020/04/tcec-s17-super-final-report/
- Where: eval
- What to add: A tiny table, outside the net, that restates when an exchange or a piece-for-pawns case is cheaper or dearer from the position around it. The exchange is cheaper with queens and a full pawn rank still on, and cheaper again with the bishop pair. When this table and the net disagree by more than a small margin, the search confirms the net’s intended trade to a greater depth before it is allowed to “fix” the material. The table does not outvote the net.
- Why: A fixed exchange rate refuses sacrifices that are materially fair in context and accepts ones that are not once the majors leave. Used only as a disagreement flag, it forces a deeper look.
- Risks: The net may already encode the same terms. The table misses king safety and a trapped piece.
- Falsify if: Switching the flag off leaves move choice unchanged on exchange and piece-for-pawns positions the tuner never saw, or the deeper search always returns the net’s move.

## Sacrifices and piece quality

### P1. Piece credit before any compensation term

- Sources: Leela positional sacrifices. https://arxiv.org/html/2510.25775v1 https://tcec-chess.com/articles/Sufi_20_-_Sadler.pdf
- Where: data
- What to add: Attribute the leaf eval to individual pieces on a small published set (a rook that looks active beside a queen that is doing the same job, a bishop shut on the back rank, a knight that has lost its square). Keep a later eval change only when the gap is the nominal value of the sacrificed or restricted piece. The allowed change is a lower credit for a piece with almost no legal squares, or for a bishop shut behind its own pawn chain.
- Why: Two engines can agree who stands better and still disagree which piece carries the advantage. That disagreement is the positional sacrifice.
- Risks: One diagram can be a special case. Matching another engine’s piece credits can be the wrong target.
- Falsify if: The attributions differ because of king safety or passed pawns, or copying those credits makes ordinary material-up endings lose.

### P2. Cross-wing binding

- Sources: Leela positional sacrifices. https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
- Where: eval
- What to add: A leaf term that treats a fragile wing as tying pieces down. Pawns that cannot be left undefended reduce the activity those pieces may count on the other wing. Score one published blocked-kingside position before trusting the term, and score it again after the pawn return that opened a diagonal.
- Why: The published account is a whole-board bind: a weak pawn on one wing changes what the pieces can do on the other.
- Risks: A current net may already mix the wings. The term can invent compensation in any closed position.
- Falsify if: The current leaf eval already prefers the bound side by a margin that agrees with a deep search, or a paired match loses because the term gives away pawns in structures that are only closed.

### P3. Capped one-pawn compensation residual

- Sources: Leela positional sacrifices. Related to B2 and V5. This one is a capped eval residual on a fixed test set, not a training correction. https://lczero.org/blog/2020/04/tcec-s17-super-final-report https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf https://tcec-chess.com/articles/Sufi_20_-_Sadler.pdf
- Where: eval
- What to add: A fixed test set from the published sacrifice positions named in the Leela file. Split the eval into material and the remainder. Where the remainder rarely covers the material given, add a residual allowed to score only enemy pieces with very few legal squares, a bishop buried behind its own pawns, and doubled or isolated pawns just created. Cap it at one pawn. Leave the main net’s training target, move ordering, and reductions unchanged.
- Why: The sound published games are cases where activity or structure was worth about a pawn or a restricted piece. The cap is the lesson of a pawn gift that created the opponent’s majority.
- Risks: One pawn is still too much in many endings. A fit to a handful of games can be memory of those games.
- Falsify if: The present non-material eval already covers the material on the sound positions and rejects the unsound gift, or the residual passes the set and then loses a normal-book match.

### P4. Permanent bad-piece residual

- Sources: Komodo Dragon eval re-derivation, from a published material study, not from a shipped bonus. https://www.chess.com/article/view/the-evaluation-of-material-imbalances-by-im-larry-kaufman https://github.com/official-stockfish/Stockfish/pull/4674
- Where: data
- What to add: From quiet middlegames, label how many of a side’s pawns are fixed on the bishop’s color, whether that bishop can still be traded, and whether the opponent still has the other bishop. Also label the bishop pair against the pawn count, and knight-versus-rook quality against pawn count. Fit those labels to game results after subtracting the current network score. Keep a label only when it still predicts the result. Train on the surviving residual. Do not copy published pawn fractions into the weights.
- Why: Bishop versus knight is equal on average in the published study. The signal is the long-lived interaction of the bishop with its own pawns. A whole classical evaluation that already contained this family was later measured at about two Elo beside a trained network, so the experiment is the residual, not a shipped bonus.
- Risks: The network may already see the pawns and the bishop. A bonus on every “bad” bishop punishes bishops that are useful because they defend a fixed pawn.
- Falsify if: On held-out quiet middlegames, after the network score and the material count, the color-complex label does not predict the result.

### P5. Doubled pawns as separate structures

- Sources: Komodo Dragon eval re-derivation, using the public structure list because the 2005 article itself did not load. https://chessprogramming.org/Doubled_Pawn https://en.chessbase.com/post/komodo-8-about-the-authors
- Where: data
- What to add: Score doubled pawns as several labels: a double that is also backward, a double that has cost a candidate passed pawn, a double that has opened a file a major piece can use, and the edge-file case. Fit each label to results in the middlegame and again in the ending, after subtracting the network score.
- Why: A single penalty mixes the harmful cases with the cases where the opened file is the point of the capture.
- Risks: The families can miss a distinction the unread article draws. Doubled pawns correlate with open files and with the bishop pair.
- Falsify if: No family predicts held-out results after the network score, the open files, and the bishop pair are accounted for.

### P6. Durable square control against current mobility

- Sources: Komodo Dragon eval re-derivation. https://chessprogramming.org/Space https://help.chessbase.com/Komodo/15/Eng/000038.htm https://github.com/official-stockfish/Stockfish/pull/4674
- Where: data
- What to add: One slow feature, tested only where it disagrees with current legal-move mobility. Safe squares for minor pieces on the central files in one’s own half, especially squares behind one’s own pawns, weighed toward positions with more pieces and fewer open files. As a second label, mark a piece that sits on a square no enemy pawn can attack. In quiet positions where the slow feature and mobility point opposite ways, record which one matches the result many moves later. Add training positions only from the side the slow feature got right and the network got wrong.
- Why: Mobility counts moves that exist now. Square control tied to the pawn front can persist after the move count looks level. The hope is a small correction where they disagree, not a clone of a space term whose whole classical package was about two Elo.
- Risks: The outpost label can rediscover a protected piece that mobility already counts. King attacks leak in if the quiet filter is loose.
- Falsify if: In the disagreement set, mobility matches later results at least as well as the slow feature, or the network score already matches the slow feature.

## Training slices

### D1. Quiet-conversion labels

- Sources: Komodo Dragon positional patience. https://komodochess.com/dragon-3.3.htm https://komodochess.com/dragon-3.htm
- Where: data
- What to add: Keep a position as a patience example only when a shallow search wants a capture, a check, or an immediate pawn break, a much deeper search wants a quiet piece move instead, and the game that followed that quiet move later improved the result. Extra weight on the next network, plus an equal-sized set of ordinary tactical positions. No hand-written activity term.
- Why: If labels come from short searches, the forcing try gets the label before the piece improvement has paid off.
- Risks: Extra weight on quiet moves can hide a real tactic. The filter has to be “deep search disagrees with the shallow force,” not “quiet is better.”
- Falsify if: The reweighted network loses a quiet-position match to the same network without the extra weight, or its tactical score falls by more than its quiet-position score rises.

### D2. King-attack labels in the training target

- Sources: Komodo Dragon king safety. https://komodochess.com/store/pages.php?cmsid=14 https://komodochess.com/dragon-3.3.htm https://u.komodochess.com/settings.html
- Where: data
- What to add: Mix a king-attack score into the training target for a slice of positions, and sweep how heavy that mix is. Include a heavier attack weight in the sweep, because the published default of the live control moved upward across versions. Keep the played evaluation as the network. The live control was published as barely changing network play.
- Why: The strong evaluation is a network taught by a classical evaluation whose authors kept revising king safety. A network trained only on ordinary search scores can miss rare attack patterns that teacher was built to price.
- Risks: The isolated revision was never measured. A handcrafted attack label can double-count the search score or pay for unsound attacks. A personality that leaves the network was published as costing about a level.
- Falsify if: The same training run without the king-attack component matches it, or the games lost are ones where its own king is stripped.

### D3. Separate danger to our king from the attack on theirs

- Sources: Komodo Dragon king safety. https://komodochess.com/store/pages.php?cmsid=14 https://en.chessbase.com/post/gm-kaufman-speaks-about-his-pet-dragon
- Where: data
- What to add: Two king-safety weights in the training target. One prices danger to the side about to move. The other prices the attack on the other king.
- Why: Published styles already split “attack while ignoring our king” from “king safety first.” Opposite-side castling needs those signs separated.
- Risks: The ignore-our-king setting is one of the styles that costs strength. Two weights can overfit.
- Falsify if: One combined weight matches the two-weight mix, or the own-king weight only changes pawn endings.

### D4. Bishop and castled-king slice

- Sources: Komodo Dragon king safety. https://en.chessbase.com/post/introducing-komodo-11
- Where: data
- What to add: Oversample middlegames where a bishop’s diagonal meets a castled king: the shelter pawn on that color is missing or pushed, or that bishop is the main attacker of the castled wing.
- Why: A version note listed a better reading of bishops and castled kings apart from a general king-safety revision. Average positions contain few of these color-complex attacks.
- Risks: No opened page describes the actual term. Extra copies of one pattern can hurt the rest of the middlegame.
- Falsify if: The same number of extra ordinary middlegame positions produces the same match result.

## Ordering extras that ride on B1

### N1. Soft prior, heavier at the root

- Sources: Leela policy ordering. Depends on B1. https://lczero.org/play/configuration/flags/ https://lczero.org/dev/wiki/project-history/
- Where: search
- What to add: Two weights on the quiet prior. At the root, a larger weight through a temperature, so the best few quiets move up together. Deeper, a much smaller weight that only breaks ties between quiets whose history scores are already close. Hash moves, winning captures, and killers keep their slots.
- Why: The root choice has no parent cutoff to lean on. Deeper nodes already have killers and history.
- Risks: A large root weight undoes deliberate root variety. A temperature that flattens too far stops changing the order.
- Falsify if: One weight at every ply matches the root-versus-tree split in a fixed-node match.

### N2. Retire the prior when the cutoff disagrees

- Sources: Leela policy ordering. Depends on B1. https://lczero.org/dev/lc0/search/alphazero/ https://arxiv.org/html/2508.21380v4
- Where: search
- What to add: One weight for the quiet prior, for the current search. When a quiet cutoff is a move the prior ranked near the top, leave the weight. When the cutoff is a quiet the prior ranked poorly, cut the weight for every later node in that search. Reset at the next root move. Ignore cutoffs below a chosen depth.
- Why: If cutoff evidence contradicts the prior, a full prior bonus keeps pulling the same wrong quiet forward in sibling positions.
- Risks: One tactical cutoff can disable a prior that was right for the rest of the tree.
- Falsify if: The prior’s top quiet is already the cutoff so often that the rule almost never fires, or the rule scores lower than the fading prior with the rule off.

## Counts in this snapshot

- Breakthroughs: 2 (B1, B2)
- Other unique ideas: 41 (S1–S11, T1–T8, O1–O5, V1–V5, P1–P6, D1–D4, N1–N2)
- Unique ideas in this snapshot: 43
- Merged away, not counted twice: game-result labels on quiet material deficits (into B2), near-tie sampling, result-weighted book choice, and personality directions (into O1), fortress discount and plan tie-break (into V1)
