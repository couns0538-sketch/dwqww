# Deduped ideas

Ideas only. Each item is written once. Departments that hit the same mechanism are named together. Breakthroughs are specified in [BREAKTHROUGHS.md](BREAKTHROUGHS.md) and only summarized here.

Importance is routine unless the item is marked breakthrough. “Where” is the kind of module. The Forge path map is not in yet.

## Breakthroughs

### B1. Fading board prior for quiet moves

Breakthrough. Leela policy ordering. Net. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

### B2. Stable-miss outcome residual

Breakthrough. Leela self-play value. Eval. The Stockfish long-term-sacrifice report’s game-result labels on quiet material deficits are a filter inside this residual, not a second model. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

### B3. Clock-gated reductions

Breakthrough. Stockfish short time controls. Search. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

### B4. Conflict-gated steep blend

Breakthrough. RubiChess eval tapering. Eval. E3 is a one-score stretch, not this two-opinion gate. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

### B5. Lesser-safe empty flights

Breakthrough. Ethereal mobility. Net. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

### B6. Matched-count exclusion bakeoff

Breakthrough. Koivisto training pipeline. Data. See [BREAKTHROUGHS.md](BREAKTHROUGHS.md).

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

- Sources: Stockfish fortress gap, Stockfish strategic-plans gap, and Leela WDL. The WDL report is the tighter specification: bin by pawn score and material first, and keep only the leftover draw rate. One head, two uses, and the leftover stays out of the pawn score. https://lczero.org/blog/2020/04/wdl-head/ https://lczero.org/blog/2023/07/the-lc0-v0.30.0-wdl-rescale/contempt-implementation https://github.com/official-stockfish/WDL_model https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html https://tcec-chess.com/articles/Sufi_17_-_Sadler.pdf https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
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

## Additions after the first snapshot

### S12. Locked-node shelf

- Sources: Stockfish closed-maneuvering gap. https://wiki.chessdom.org/TCEC_Season_16_Division_P_Game_64_%E2%80%93_Leela-Stockfish https://chessprogramming.org/Late_Move_Reductions
- Where: search (`alphabeta.inc`)
- What to add: Where both sides have very few pawn moves that change the structure, and the side to move is not in check, keep the normal search for the table move and captures. Also search at most two non-capturing piece moves that history already ranks highly, plus the one legal pawn break, with a smaller depth cut than other late quiets. Cap how often this runs.
- Why: The published games are a long piece improvement with a fixed structure, then a break. Reductions spend depth on moves that already look forcing.
- Risks: Closed openings become tactical after the break. History may not rank the preparatory move.
- Falsify if: On French, Stonewall, Hedgehog, and closed Ruy positions the root move matches the unpatched search, or a paired match on a normal book and on that closed book is both negative.

### S13. Credit the quiet move before the break

- Sources: Stockfish closed-maneuvering gap. Related to B1, but this is a history table, not a net head. https://lczero.org/blog/2020/04/tcec-s17-super-final-report/ https://tcec-chess.com/articles/Sufi_22_-_Sadler.pdf
- Where: search (`history.hpp`)
- What to add: A separate history for a non-capturing piece move that was followed, a few plies later with the structure unchanged, by a pawn move that raised the score. Use it only to order those piece moves and to shorten their reduction. Do not add it to the evaluation.
- Why: Cutoff history rewards the break, not the earlier regrouping.
- Risks: It can reward a piece move that merely happened before a good break. It overlaps continuation history.
- Falsify if: In locked positions this history does not agree with a much deeper search, or turning it on does not change root moves.

### S14. One quiet non-reduction before a table win

- Sources: Stockfish endgames beyond tablebases. https://official-stockfish.github.io/docs/stockfish-wiki/Advanced-topics.html https://lczero.org/blog/2018/08/tablebase-support-and-leela-weirdness/
- Where: search
- What to add: At a node with one more piece than the probe limit, look one ply past each quiet move for a single capture or pawn push. If that child is a table win and the distance fits the fifty-move budget, do not late-move-reduce that one quiet move. Do not extend it. Cap at one quiet move per node.
- Why: The published win signal is a line that enters the table. The moves that get dropped are the quiet moves before that entry.
- Risks: Many quiet moves sit one capture from a table win. The general-play value of seeing the table at all is now about zero to three Elo.
- Falsify if: At the same node count the best move is unchanged on a suite whose win is a quiet move followed by one table entry, or a long-control match loses Elo.

### S15. Full depth for the rook that meets the passer

- Sources: Stockfish endgames beyond tablebases. https://github.com/official-stockfish/Stockfish/issues/2288#issuecomment-599162276
- Where: search
- What to add: In rook endings with eight or more pieces and a passed pawn, if the rook reaches the passer’s file in no more moves than the pawn needs for its next step, search that rook move at full depth. Do not extend it and do not add an eval term.
- Why: The win and the draw in that family were described as the rook being one tempo late. Rook and three pawns versus rook and two was the most common eight-piece material in the cited sample.
- Risks: The net may already rank that rook move first. Unreducing a class of rook moves inflates the tree.
- Falsify if: The unreduced swing changes the best move on none of a suite where the rook is one tempo short, or a long-control match loses Elo.

### S16. Quiet lever, no candidate bonus

- Sources: Ethereal passed pawns. https://github.com/AndyGrant/Ethereal/blob/0e47e9b67f345c75eb965d9fb3e2493b6a11d09a/src/evaluate.c https://github.com/official-stockfish/Stockfish/pull/2613
- Where: search
- What to add: Detect a pawn whose every stopper is a lever, with at least as many helpers as attackers on the push square. Give the quiet or non-losing capture that clears the last stopper a higher order and a milder reduction. Add no static bonus.
- Why: The passer does not exist until the lever is played. A discounted eval bonus was the tool a published test rejected.
- Risks: Common in closed positions. A reduction change can weaken pruning around bad breaks.
- Falsify if: The baseline already searches that lever within the first few moves, or a match shows no gain and a clear node increase.

### S17. Commit gate

- Sources: Ethereal search structure. https://raw.githubusercontent.com/AndyGrant/Ethereal/master/src/search.c
- Where: search
- What to add: A node answers its parent only through one final phase. Earlier phases fill a result record. The final phase applies mate distance, then any tablebase floor and ceiling, then the table write, then ordering-memory training from moves actually dispatched. A table cutoff that must skip the tablebase window marks that exception. The time abort stays outside the gate.
- Why: Late phases protect mate distance, tablebase bounds, and the ordering update. Early answers never reach them, so a new preface experiment can publish a score the epilogue never sees.
- Risks: Clamping table cutoffs to a tablebase window would change scores. The exception has to stay explicit.
- Falsify if: With the table exception preserved, the chosen move changes on a fixed suite, or a new preface can still answer the parent without passing the gate.

### S18. Verification verdict

- Sources: Ethereal search structure. Koivisto’s null-move verification is a different probe. https://raw.githubusercontent.com/AndyGrant/Ethereal/master/src/search.c
- Where: search
- What to add: Singular verification is its own node class. It returns only whether the move is unique, ordinary, or whether several moves beat the raised window. The parent turns that verdict into an extension, a normal search, or a multi-cut. The child does not mark the parent’s move generator finished.
- Why: A verification that reuses the parent’s generator can end the parent as a side effect.
- Risks: A second cursor repeats generation. Dropping the “several moves” verdict removes multi-cut.
- Falsify if: After a non-singular verification the parent’s next move differs on a fixed suite, or node counts rise and results fall by that cost alone.

### S19. Frozen preface

- Sources: Ethereal search structure. https://raw.githubusercontent.com/AndyGrant/Ethereal/master/src/search.c
- Where: search
- What to add: Choose the node class once at entry. The preface freezes depth, eval, improving, the table move, and whether quiet stages are allowed. The move phase may attach a depth budget to a child edge. It may not rewrite the node’s own depth or turn quiet stages back on. A quiet leaf is entered only when the king is not attacked.
- Why: A preface that edits the node depth makes every later move inherit an experiment aimed at one condition.
- Risks: That depth edit is intentional. Moving it onto edges can lose strength. An in-check node must not go to a quiet leaf that assumes a stand-pat eval.
- Falsify if: Edge budgets are move-identical to the current depth edit, or they diverge and the divergent side loses.

### S20. Two-regime probcut witness

- Sources: RubiChess probcut. https://raw.githubusercontent.com/Matthies/RubiChess/master/src/search.cpp https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/search.cpp
- Where: search. ProbCut is already present.
- What to add: Keep Forge’s own margin and split the proof. If static eval already clears beta by the full margin, confirm with one non-losing tactical move searched more than one ply. Quiescence may reject the try. It may not cut by itself. If static eval is short of the raised bound, try a tactical move only when its exchange value covers the whole gap, with the same real-search requirement. Stay off principal-variation nodes and skip the search proof while in check.
- Why: One implementation always uses a real reduced search. Another lets the witness depth collapse to quiescence exactly when eval is already high. The local proof demands that eval already clear the cushion, so a capture cannot close a shortfall.
- Risks: The surplus regime can pile onto standing-pat pruning. The gap regime can miss a quiet move that was the real reason the position holds.
- Falsify if: The surplus regime mostly fires on nodes standing-pat would already have taken, or the gap regime raises the cutoff count while a fixed-node match or a tactical suite loses.

### S21. Honest proof in the table

- Sources: RubiChess probcut. https://github.com/official-stockfish/Stockfish/commit/e18619d07802882136b583a01e56791b61abede6
- Where: search
- What to add: On a successful witness, store a lower bound equal to the stripped value the parent was given, tagged with the witness depth. If the table already has a bound at least that deep that misses the raised window, skip the attempt.
- Why: Storing the raw witness and returning a stripped value lets a later probe cut on a stronger score than the proof allowed.
- Risks: A shallow stored bound can prune a later iteration.
- Falsify if: A tactical suite drops while node count falls, or the skip almost never happens.

### S22. One-ply tactical cooldown

- Sources: RubiChess probcut. https://chessprogramming.org/ProbCut
- Where: search
- What to add: Refuse the shallow proof for one ply after a capture or a check, including when the side to move is no longer in check. Leave the margin unchanged.
- Why: Shallow and deep scores diverge most right after a forcing move.
- Risks: Recaptures are often the witnesses that make the prune pay.
- Falsify if: Most successful witnesses are recaptures or replies to check, and disabling them loses the node reduction without improving tactical accuracy.

### T9. Spend the clock on equal positions that are still alive

- Sources: Leela WDL. Depends on the leftover in V1. https://lczero.org/blog/2020/04/wdl-head
- Where: time (`timeman.hpp`)
- What to add: When the pawn score is near zero, allow more time if the draw leftover is low, and less if the leftover says the position is a dead draw. Leave eval and move order unchanged. Cap the shift.
- Why: A dead draw and a sharp equal position can share a zero score. Move choice stays with the pawn score.
- Risks: A false dead draw saves time and then loses. A clock rule on a raw label at very few nodes chases noise.
- Falsify if: Paired games with the same total time are unchanged, or the positions that receive extra time are ones where a longer search leaves the chosen move unchanged.

### T10. Reserved short-clock allocation

- Sources: Stockfish short time controls. https://github.com/official-stockfish/Stockfish/pull/4472
- Where: time
- What to add: Keep a root-complexity adjustment to thinking time. At bullet, cap it so one unstable move cannot take more than a fixed share of the remaining clock, and hold back a reserve.
- Why: A merged change that scaled time from root complexity was described as especially effective at short controls. At 1+1 an uncapped extension spends the increment on one position.
- Risks: The cap can cut the one move that needed the time.
- Falsify if: Bullet score does not rise, the engine loses on time more often, or long games lose because the cap is still active.

### D10. Label the extra-pawn parent from real captures only

- Sources: Stockfish endgames beyond tablebases. https://en.chessbase.com/post/study-of-the-month-endgame-studies-endgame-theory https://github.com/official-stockfish/Stockfish/issues/2288 https://github.com/official-stockfish/Stockfish/pull/4143
- Where: data
- What to add: Sample eight-piece positions with at least one pair of opposing pawns on the same file. Probe only legal captures that remove one of those pawns and land in a table already available. Label the parent when every such capture is a draw or a loss for the side to move. If any capture is a win, keep the ordinary search label. Mix a small share into the existing Syzygy rescore path. Keep a single net.
- Why: The common eight-piece ending in the cited sample is one pawn above a seven-piece table. A label from a legal capture avoids a deletion probe that was about 5 Elo weaker.
- Risks: A drawn capture-child can hide a win played by a quiet move first. The modern match value of perfect six-piece knowledge is about zero to three Elo.
- Falsify if: On held-out eight-piece rook endings with a blocked opposing pair, a deep search allowed to use seven-piece tables disagrees with the all-captures-draw label on more than a small fraction, or a long-control match with the mix loses Elo.

### D5. Deep targets only where a locked search drifts

- Sources: Stockfish closed maneuvering. Related to D1. The trigger here is a score gap with the structure unchanged, not a result that followed a quiet move. https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
- Where: data
- What to add: Keep locked middlegames. Store a shallow score and a much deeper score. Add a thin training slice only where those scores disagree by a wide margin while material and the pawn structure stay the same. Use the deeper score as the target.
- Why: If labels are the shallow view, the net learns the shrug and then tells search the quiet moves are not worth depth.
- Risks: Deep scores are expensive and can be wrong. A loose filter becomes a general “trust long search” relabel.
- Falsify if: In locked middlegames the shallow and deep scores already lie in a narrow band, or the slice loses more on a tactical book than it gains on the closed book.

### D6. Label unequal draws before the position is small

- Sources: Komodo Dragon endgame technique. Related to V2, which mines high-score quiet draws. This slice is materially unequal endings and perpetuals that are still too big for a table. https://en.chessbase.com/post/gm-kaufman-speaks-about-his-pet-dragon
- Where: data
- What to add: Positions too large for a tablebase, where one trade leads to a materially unequal draw or to a win that exists only along one exact path, including perpetuals that material still calls lost. Label from the finished ending. Fine-tune so the defender wants the trade and the attacker refuses it. No fortress detector and no new tablebase probe.
- Why: The published claim is that recognizing those endings would gain Elo by seeking or avoiding them, while tablebases themselves add only a few Elo because the few-piece ending is already played well.
- Risks: Rare positions. Wrong labels teach the engine to hold a loss.
- Falsify if: The known drawn-but-ahead endings are already on the drawing side of the edge, and a fine-tune leaves self-play unchanged.

### D7. Replace blitz ending labels with a long search

- Sources: Komodo Dragon endgame technique. https://en.chessbase.com/post/komodo-dragon-2-is-here
- Where: data
- What to add: Take endgame positions from ultra-fast self-play and score them again with a much longer search. Fine-tune only where the two labels disagree on which side of the win/draw edge the position is on.
- Why: A net trained on ultra-fast games can memorize the wrong conversion. Endgame quality was described as depending on enough increment.
- Risks: A longer search can still be wrong in a fortress. If training is already on long games, the slice is empty.
- Falsify if: The blitz label and the long-search label agree on the side of the edge, or the fine-tune loses match score.

### D8. Host labels on foreign positions

- Sources: Koivisto training pipeline. https://github.com/Luecx/Koivisto/releases/tag/v9.0
- Where: data
- What to add: Three equal-size sets. Host-only games. Games whose moves come from a second mover, relabeled by the host search and the game result. The same foreign games with the second mover’s scores left on.
- Why: A published mix of two engines’ data was about 20 Elo at a short control and a long one. The note does not separate new positions from the other engine’s scores.
- Risks: A second mover fills the set with positions the host never meets. A shallow host relabel can be a worse teacher.
- Falsify if: The host-only net matches the relabeled foreign net, or the foreign scores beat the host relabel by a clear margin.

### D9. Disagreement-conditioned target

- Sources: Koivisto training pipeline. Same family as B2, different mechanism: a mix weight, not an additive residual. https://github.com/Luecx/Koivisto/releases/tag/v6.0
- Where: data
- What to add: Keep search score and game result. Where they agree, let the search score dominate. Where they disagree, let the result dominate. Compare with one global mix on the same positions.
- Why: A single mix treats a position the search already understands like a position it got wrong.
- Risks: Results are noisy. A global mix that moves across training can win without the split.
- Falsify if: One global mix matches the conditioned mix at the same position count.

### V6. Judge a trade by which side of the edge it lands on

- Sources: Komodo Dragon endgame technique. https://komodochess.com/dragon-3.3.htm https://new.uschess.org/news/inside-story-kaufman-what-your-computer-trying-tell-you
- Where: net
- What to add: A second value, used only when a move trades into a pawn ending, a rook ending, or a minor-piece ending. It answers whether that ending is on the winning side or the drawing side of the win/draw edge. A healthy extra pawn in a pawn ending should come out as a win. A materially better ending that is blocked or theoretically drawn should come out as a draw. Leave the displayed score alone. A monotone rescale does not change moves.
- Why: The same material converts differently by stage. A score anchored in the opening can mis-rank a trade whose result appears only after the pieces come off. This does not assume Stockfish is weak. Its published anchor is already a later move number.
- Risks: If the net already knows the phase, the extra value double-counts.
- Falsify if: The current score already predicts endgame win rate as well as opening win rate, or the edge rule picks the same trade as the uncalibrated engine.

### E2. Shuffle shrink at the node

- Sources: Berserk eval scaling. https://raw.githubusercontent.com/jhonnold/berserk/main/src/search.c https://raw.githubusercontent.com/official-stockfish/Stockfish/master/src/position.cpp
- Where: eval, applied when a static score is read, including from the transposition table.
- What to add: Store the phase-scaled static score with no fifty-move factor. At the node being searched, shrink that score from the counter on the board. Leave mate and tablebase scores unshrunk.
- Why: One placement can be reached with a short counter and a long one, and those nodes share a hash entry whose key ignores the counter.
- Risks: The improving signal compares static scores across plies. If the damped score is stored, a later probe damps it twice.
- Falsify if: Positions that differ only in the fifty-move counter still produce the same searched static score, or a paired match gains nothing against a version that forces the counter equal.

### E3. Heavy-piece residual at a fixed piece count

- Sources: Berserk eval scaling and Koivisto’s pawn-counted multiplier. Written once. The Koivisto form is a 1.5-to-1.15 multiplier that counts pawns and weights a knight slightly above a bishop. The Berserk form stretches by non-pawn piece type and leaves a pawn ending on the raw scale. Test them as two arms, not as a stack on B4. https://github.com/official-stockfish/Stockfish/commit/1dbd2a1ad548b3ca676f7da949e1a998c64b836b https://github.com/Luecx/Koivisto/blob/master/src_files/board.cpp
- Where: eval. `NetScale`, the phase taper, and `scale_factor` already touch this score. Retune margins in a separate match.
- What to add: At the same piece count, stretch the score when the remaining pieces are heavy and leave a pawn ending closer to the network’s own scale. A second arm counts pawns in the phase. Keep the material-agreement adjustment out of this patch.
- Why: A queen ending and a minor-piece ending can share a head and still need different scores. A 2020 stretch of this family passed a short test and a long test.
- Risks: A louder middlegame changes pruning even when the ranking is unchanged. Over-weighting queens refuses sound trades.
- Falsify if: A multiplier that depends only on piece count matches the heavy-piece residual, or the residual wins and then loses once margins are adjusted so one pawn is the same threshold in the opening and the ending.

### P7. Lever-resolved pawn class

- Sources: Ethereal pawn structure. Distinct from P5, which splits doubled pawns into structures. This one is the gap between the class now and the class after a pawn capture. https://raw.githubusercontent.com/AndyGrant/Ethereal/master/src/evaluate.c
- Where: eval, cached with the pawn key.
- What to add: Score the gap between isolated, stacked, backward, or connected now and after each side’s pawn captures. A capture can remove isolation. A side-by-side pawn is not connected when the step forward is attacked and nothing stands behind. Fit the size on Forge’s games. Do not import another engine’s numbers.
- Why: The label on the diagram is wrong when one pawn capture changes it. The capture is not the move being searched at most nodes.
- Risks: Captures are already searched early. The residual can double-count the net.
- Falsify if: A paired test shows no gain, or the gain disappears when the residual is limited to captures quiescence already tries.

### P8. Healthy wing majority

- Sources: Ethereal pawn structure. Ethereal has neither a majority term nor an island term. https://raw.githubusercontent.com/AndyGrant/Ethereal/master/src/evaluate.c
- Where: eval
- What to add: Credit an extra pawn on one wing only when it is not stacked and the wing contains a lever that can trade an isolated pawn or join a neighbor. An island penalty applies only to a group with no lever into the next group.
- Why: Pair features stop at the next file. A majority is a count across the wing. Restricting it to a mobile extra pawn avoids paying for a doubled or locked majority.
- Risks: Isolated and stacked penalties may already contain the Elo. The term can leak into passed-pawn value.
- Falsify if: The feature does not change results once stacked and leverless majorities are removed, or a match shows no gain.

### P9. Pawn-only correction head

- Sources: Ethereal pawn structure. https://github.com/AndyGrant/Ethereal/commit/513a93c23219f2a71b70085c3f88def359399567
- Where: net, cached by the pawn key.
- What to add: A small net on pawn squares only, trained to predict the main net’s error, added as a residual. No king and no pieces. Do not reuse another engine’s weights.
- Why: A measured gain came from a small location net trained as a correction and cached so piece moves do not redo it. Stripping the kings keeps this out of king safety. The old result included kings and a hand-written eval, so a pawn-only head against a modern net should be smaller.
- Risks: A net that already sees every pawn square can make the head redundant.
- Falsify if: The head fails a paired test against the main net alone, or its gain is explained by positions where only the kings differ.

### P10. Passer path when material and the net disagree

- Sources: Ethereal passed pawns. https://github.com/official-stockfish/Stockfish/blob/1e7e6bdeb97669a950b8e4c063770d135f54f55b/src/evaluate.cpp
- Where: eval
- What to add: Classify each leading passer: next square occupied, empty but attacked, empty and safe, or the promotion file clear. When the net prefers the side that is materially behind and that side has an empty-and-safe or clear passer, skip a material-disagreement shrink if one exists. Otherwise fit one small term per leading passer. Do not add a second king-distance term unless the fit shows the net still misses it.
- Why: A clear passer is a concrete reason to be ahead while down material. A disagreement shrink pulls that score back.
- Risks: The shrink exists because messy compensation is drawish. Exempting passers can overvalue a passer that is still stopped.
- Falsify if: The exemption changes the eval by noise, or a match loses strength.

### P11. Two safe adjacent passers

- Sources: Ethereal passed pawns. https://github.com/AndyGrant/Ethereal/blob/0e47e9b67f345c75eb965d9fb3e2493b6a11d09a/src/evaluate.c
- Where: eval
- What to add: When two passers stand on adjacent files and both next squares are empty and safe, add a pair term that is zero if either next square is occupied or attacked. Fit it on Forge endgame games. Keep it off for a connected pawn that is not passed.
- Why: One piece can blockade one passer. Two passers that can both step safely make that blockade fail. A per-file passer score never sees the pair.
- Risks: A king-piece net may already score a phalanx on the sixth rank.
- Falsify if: The pair term does not change the chosen move when one passer is removed, or a match is flat.

### P12. Battery reach apart from real moves

- Sources: Ethereal mobility. https://raw.githubusercontent.com/AndyGrant/Ethereal/0e47e9b67f345c75eb965d9fb3e2493b6a11d09a/src/evaluate.c
- Where: eval
- What to add: Score the squares a bishop or rook attacks on the real board apart from the extra squares it sees only through our own bishop, rook, or queen. Keep the pawn-safe area. Give the latent squares a much smaller signal.
- Why: Folding battery sight into the same curve as immediate reach makes a bishop behind our queen look as free as a bishop with an open diagonal.
- Risks: A battery really does increase scope after one trade. The split overlaps B5 if both ship together.
- Falsify if: The split loses to one combined pawn-safe count on the same positions.

### P13. Restrict only the piece that cannot leave

- Sources: Ethereal mobility. Uses the flight definition in B5. Do not also add a large negative eval on the same mark. https://raw.githubusercontent.com/AndyGrant/Ethereal/0e47e9b67f345c75eb965d9fb3e2493b6a11d09a/src/evaluate.c
- Where: eval
- What to add: Charge a friendly piece only when the enemy attacks its square more times than we do, our pawns do not defend it, and the piece has no lesser-safe empty flight or only one. Drop the penalty on empty contested squares.
- Why: A square-count restriction punishes a piece with many real flights for standing on one awkward square.
- Risks: The square count may be doing useful work about attacks that bite on granite. It double-counts B5 if both are large negative terms.
- Falsify if: The piece-gated penalty loses to the square count when both use the same flight definition.

### P14. Shrink the positional surplus when material disagrees

- Sources: Koivisto leftover eval, describing a signal Stockfish still uses and Koivisto does not. Not a copied formula. https://github.com/official-stockfish/Stockfish/blob/master/src/evaluate.cpp
- Where: eval
- What to add: From the piece values Forge already uses, compute a material-only score. When that score and the full eval disagree in sign, move the full eval halfway toward the material score. When they agree, leave the eval alone. No optimism term.
- Why: Mobility, shelter, and file terms can outvote material. This tests whether that surplus is overconfident exactly where a net would later be trusted instead.
- Risks: Some real compensation is exactly a positional surplus against material.
- Falsify if: The shrunk eval loses a paired match, or the lost games are mostly ones where shelter, an open file, or the bishop pair was the true advantage.

### P15. Knock out one classical family at a time

- Sources: Koivisto leftover eval. https://github.com/Luecx/Koivisto/wiki/Evaluation
- Where: eval (`tools/tune/texel.cpp` already traces the terms)
- What to add: Six matches. In each, zero exactly one family: mobility, doubled and isolated pawns, rook files, king shelter, the bishop pair, or the flat tempo. Leave passers alone. A family stays only when its removal loses. A family whose removal is noise is deleted so it is not carried beside a future net.
- Why: The published result of this department is that those families no longer exist as their own score. The knockout asks which of Forge’s terms are still doing work.
- Risks: One-family matches hide terms that matter only together. A short match calls a real small term noise.
- Falsify if: Removal loses beyond paired-match noise: that family stays. Call a family dead only when two opening sets both tie.

### P16. Pawn-counted phase multiplier

Merged into E3. Not counted separately.

### P17. Separate attacker clock and pawn clock

- Sources: RubiChess eval tapering. Distinct from B4, which is one blend that gets steep when two opinions conflict. https://raw.githubusercontent.com/Matthies/RubiChess/master/src/eval.cpp
- Where: eval
- What to add: Mix king-safety and pawn-storm terms from the opponent’s remaining attackers that can reach that king’s flank. Mix passed pawns and king activity from the pawn map: a full wall keeps the middlegame opinion, and open files plus missing stoppers move toward the endgame opinion.
- Why: One global weight cannot say that one king is still under attack while the other king should already centralize.
- Risks: The two clocks can double-count the same pieces. Imbalanced positions are a minority of a normal book.
- Falsify if: A single clock matches the split on a set stratified by material imbalance, including queen versus two rooks and opposite-side pawn majorities.

### P18. Pawn-lock phase shift

- Sources: RubiChess eval tapering. https://raw.githubusercontent.com/Matthies/RubiChess/master/src/eval.cpp https://www.chessprogramming.org/Tapered_Eval
- Where: eval
- What to add: When the pawn skeleton has almost no legal pawn captures and almost no pawn pushes that change the structure, move pawn-break and king-centralization terms toward the endgame opinion even while queens remain. Keep king-attack terms on a blend that still depends on whether heavy pieces are on the board.
- Why: Both a non-pawn phase and a material total move only when material changes. A locked center with queens on is already an endgame of pawn breaks.
- Risks: Early closed openings can be misread as endgames.
- Falsify if: Closed-center games show no gain against a material-only blend, or the shift loses development in locked openings.

### N3. Product collapse against a residual wide path

- Sources: Berserk net structure. https://github.com/jhonnold/berserk https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html
- Where: net
- What to add: Two nets with the same feature families and the same first-map width. One multiplies paired channels so the tower stays one perspective wide, then scores through a narrow summary. The other concatenates the perspectives with side to move first and keeps a residual path from the wide values into the score. Compare at equal nodes.
- Why: Collapsing width buys a later tower and can erase a signal that is strong for only one side. The open question is whether the product still wins once speed is taken out.
- Risks: A hard summary drops tactics the wide map already represented. The residual path spends the speed the product was meant to save.
- Falsify if: At equal nodes the product loses to the residual concatenation, or the win vanishes once nodes are equalized.

### N4. Placement and attacks meet after the nonlinearity

- Sources: Berserk net structure. https://github.com/official-stockfish/Stockfish/commit/f4bcd40409f94bd397a083c5d6243bac6dcc6d85
- Where: net
- What to add: Give king-region placement, attack relations, and adjacent-file pawn geometry their own first maps. Activate each, then let the tower read them together. Hold total width and eval time against one fused map.
- Why: Those families change on different moves and do not all need the king’s bucket as their frame. A fused map mixes them before the nonlinearity.
- Risks: Early mixing is where a hanging piece becomes a cheap feature. A split can lose that pattern.
- Falsify if: The fused map matches the split at the same eval time, or the split wins only while it is allowed to be slower.

### N5. A joint expert when the heavy pieces are gone

- Sources: Berserk net structure. https://github.com/official-stockfish/Stockfish/commit/5c4cef0bfe61fb3249178b2bcf21f5673557efe7
- Where: net
- What to add: For positions with no rook or queen, change the placement frame and the small tower together. Compare that with a new output head on the ordinary features, and with a new feature block on the ordinary tower. Drop combinations that almost never occur.
- Why: A published ablation said each single addition failed against the combination, with a head-only variant only the closest. A phase head may pay only when the inputs are specialized for that phase.
- Risks: Rare experts starve. A joint expert also refreshes when the condition flips.
- Falsify if: The head-only split matches the joint expert at the same speed, or the joint expert loses to the unchanged net.

### N6. Low-budget eval lane

- Sources: Stockfish short time controls. https://talkchess.com/viewtopic.php?t=85854
- Where: net
- What to add: When the projected nodes are in the bullet range, score quiet non-PV nodes with a cheaper evaluation and keep the full network on the principal line and on tactical nodes. At long controls, use the full network on every node.
- Why: At bullet, a slightly finer score that costs an iteration is the expensive purchase. At long controls the full score is what produces the draws.
- Risks: A cheap score misses tactics. If the speedup is too small to finish another iteration, the lane only adds error.
- Falsify if: Bullet results fall, the cheap path stays on in long games and those games fall, or nodes per second do not rise enough to complete another iteration.

### U1. Commit-point accumulator

- Sources: RubiChess incremental updates. https://github.com/Matthies/RubiChess/blob/263f15d7960eb32b45ce1a06fbe64d750729803f/src/nnue.cpp
- Where: search, calling the accumulator in `src/nnue.cpp`
- What to add: Once a node has survived the early exits and will try moves, build its accumulator before the first child if it is still dirty and the dirty chain is already longer than one ply.
- Why: A reused static score skips the build, then every child repeats the walk. The v4 net on another branch rebuilds both accumulators every eval, so this idea applies to the incremental net, not to that rebuild.
- Risks: Nodes that fail on the first move pay for an accumulator nobody reuses.
- Falsify if: A fixed-depth bench shows no node-rate gain, or any position’s evaluation differs from a full rebuild.

### U2. Two-anchor fused chain

- Sources: RubiChess incremental updates. https://github.com/Matthies/RubiChess/blob/263f15d7960eb32b45ce1a06fbe64d750729803f/src/nnue.cpp
- Where: eval
- What to add: When a lazy chain is needed, build only the oldest missing ply and the ply being evaluated. Fold the plies between them into one add and subtract. Leave the middle plies dirty.
- Why: Writing every intermediate accumulator moves a wide vector for plies that are often never evaluated.
- Risks: A high-branching middle ply stays dirty, so each evaluated child repeats that ply’s change. A missed change corrupts every deeper evaluation.
- Falsify if: Node rate does not rise against a builder that writes every ply, or a from-scratch evaluator disagrees.

### U3. Cheaper of fused delta and king-square cache

- Sources: RubiChess incremental updates. https://github.com/official-stockfish/Stockfish/blob/1e7e6bdeb97669a950b8e4c063770d135f54f55b/src/nnue/nnue_accumulator.cpp
- Where: eval
- What to add: Count the feature columns in the fused dirty chain and the piece differences against the cached accumulator for that side and king square. Apply whichever set is smaller. A null move is an empty change, not a king change.
- Why: A long run of skipped evaluations can change more columns than a cache diff of the pieces on the board.
- Risks: The cache entry can itself be far from the position. Threat features missing from the piece cache must stay on the rebuild side.
- Falsify if: The chooser does not reduce columns applied per evaluation, or the two paths produce different scores.

### X1. Wrapper-aware joint step

- Sources: Ethereal tuning method. https://talkchess.com/viewtopic.php?t=74877 https://www.chessprogramming.org/Texel%27s_Tuning_Method
- Where: eval, via `tools/tune/texel.cpp`
- What to add: Fit every explicit term in one run, using the derivative of the evaluation search actually receives, including the phase blend and any later shrink. Compare with a fit that pretends each term is independent, and with the current weights. Accept a winner only from a match.
- Why: A gradient on linear terms misses a change that a later adjustment undoes. Reported gains from the coupled step were small, about +10, +3.4, and +2.3 Elo, and the joint fit was the smallest.
- Risks: The surrogate can reward a feature the engine should not play for. A short run can look like a null result.
- Falsify if: The coupled and uncoupled runs move the terms the same way, or the coupled weights lose the match.

### X2. Resolved quiet band with a second book

- Sources: Ethereal tuning method. https://github.com/AndyGrant/Ethereal/releases/tag/V12.50
- Where: data
- What to add: Quiet ends of depth-12 lines, one position from a game, only inside a modest score band. Fit explicit terms to the game result. Reject the fit unless error also falls on a second book, then play a match. Repeat with a set that keeps many positions from each game.
- Why: Stacking positions from one game was reported to lower dataset quality, and a band keeps solved positions from owning the scale.
- Risks: Dropping decided positions means the fit only moves the uncertain band. A second book can reject a real gain that is uneven across openings.
- Falsify if: The many-positions-per-game set wins the match, or neither set beats the current weights.

### X3. Game-result target against a search-score target

- Sources: Ethereal tuning method. This is for explicit terms, not for the net mix in D9. https://pdfhost.io/v/btdMpXUqt_Tuningpdf
- Where: data
- What to add: Freeze one position set and fit the same explicit terms twice. One target is the game result. The other is a deeper search score through the same curve. Play the two results against each other and against the current weights.
- Why: A result label and a search-score label teach different mistakes. The match, not the training error, chooses.
- Risks: A result label repeats one outcome across a game. A search-score label copies present mistakes.
- Falsify if: The two fits agree within a small tolerance, or neither beats the current weights.

## Counts in this snapshot

- Breakthroughs: 6 (B1–B6)
- Other unique ideas: 84
- Unique ideas in this snapshot: 90
- Not counted separately: P16 (merged into E3)
- Merged away, not counted twice: game-result labels on quiet material deficits (into B2); near-tie sampling, result-weighted book choice, and personality directions (into O1); fortress discount, plan tie-break, and the WDL leftover (into V1); capture-filter variants (into B6)
