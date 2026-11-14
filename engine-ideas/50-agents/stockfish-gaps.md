# Stockfish gaps

Ideas only. All seven departments are in as of 11:47 UTC.

## Long-term sacrifices and material imbalance

Importance of the department: routine. The published gap is against Stockfish before the neural evaluation, not a measured gap against current Stockfish.

What others do. A value trained from the finished game can call a quiet material deficit a win if the extra piece never gets a job. In the 2018 evaluation that search looked at far fewer positions than Stockfish and still won a long match, including games that gave pieces for a long-term advantage. An older published scale says the exchange is cheaper while minor pieces remain and cheaper again with the bishop pair, and dearer once queens, rooks, and pawns are gone.

Where Stockfish is weaker. The 2017 account of Stockfish is a weighted sum applied after checks and captures are resolved. Annotated games from that era show piece sacrifices whose compensation was still unclear more than a dozen moves later. After the neural evaluation, Stockfish has won the superfinals the opened pages list, and the training target is still a moderate-depth search score. A label taken from that search only knows a sacrifice is good if the search already saw the payoff. No page opened here is a post-2021 match that measures current Stockfish as behind on this department.

Ideas. The game-result target on quiet deficits is folded into breakthrough B2 as a filter, not a second net. The extension while extra material is idle is S9. The context table used only as a disagreement flag is V5.

## Opening variety

Importance of the department: routine.

What others do. A book gives near-equal moves probabilities from past results. A personality changes the evaluation so a different move becomes best, and the published note says that costs about a skill level against computers. A standing contempt shift changes the score and cuts the draw rate, and the strongest published setting is no shift.

Where Stockfish is weaker. Same position, same time, one thread: the same move. That is the best-move policy. A developer’s 100-game test with only 1.e4 and 1.d4 produced 11 distinct lines through ply 7 on one thread, and one repeated line at a faster control. The reply was that an external book already supplies the variety, and that randomizing the first moves inside an eval margin was a leap of faith. Public counts do not show current Stockfish as easier to prepare against than the other top engines. One Berlin line was best play for Stockfish, Dragon, and Koivisto in a 2022 look. A variety mechanism that gains a large Elo for current Stockfish was not opened. The opened strength statements go the other way.

Ideas. Near-tie choice, including a result-weighted table, is O1, shared with Leela and Dragon. The opening-only structure tilt is O2. The one-time exit from a repeated opponent line is O3.

## Fortress and draw detection

Importance of the department: routine. The mislabel shows up in public games. No opened source measures a large rating cost.

What others do. A position-specific outcome head can call a dead draw and a sharp equal position different even when the expected score is similar. In one superfinal the score sat at 0.0 from move 22 while the outcome head still gave both sides winning chances until move 50. In another game the defender’s engine saw no danger while the attacker’s score said a clear or winning advantage. The error is not one-sided: published positions exist where each engine is the one that misses the fortress.

Where Stockfish is weaker. The published win-draw-loss display is a curve of the pawn score, shifted by material. Two positions with the same score and the same material get the same draw chance. The net is trained to agree with a teacher score, and a 2024 recipe increased the loss when the net looked more drawish than that score. A 2020 change consulted the net more often when a high score only shuffled in a quiet imbalance. The hand-made eval that change could fall back on was removed later. Tablebases do not cover the positions this department is about. Engines claim a winning advantage in fortresses unless a tablebase says otherwise. A blocked study still scored as a large loss after the drawing sequence.

Ideas. The outcome head that is allowed to disagree with the pawn score is V1, shared with the strategic-plans report. Mining high-score draws is V2. The shuffle probe is S10.

## Strategic plans over raw eval

Importance of the department: routine. The clearest published miss is pre-neural-evaluation. Later superfinals went the other way.

What others do. Rank a quiet plan by expected game result when every pawn score is level, instead of by a deeper sample of the same pawn score.

Where Stockfish is weaker. Futility and late-move pruning drop quiet moves whose static score sits a margin below alpha. In superfinal game 61 the engines split on a pawn move. After the structure closed, one score was positive and the other was negative. The reason given is a plan: the kingside pawns are fixed, pieces tied to a loose pawn are missing from the other wing. A larger kibitzing Stockfish was still on the positive side of zero. More of the same evaluation had not crossed over. A later note shows a pawn score of 0.0 on every move of a draw while separate win and loss chances stayed alive. Weeks, citing Sadler and Regan, reports AlphaZero-match positions where several alpha-beta lines were all 0.00.

Ideas. The tie-break use of the outcome head is the second use of V1. The extra plies on a tied root cluster are S8. The one-ply exception for a quiet move inside the band is S7.

## Closed maneuvering positions

Importance: routine. The match evidence is from 2019–2020. After the neural evaluation, a 2022 superfinal report gives Stockfish maneuvering wins against Dragon. No opened 2023–2026 page isolates a current Elo gap.

What others do. A prior proposes a few quiet moves that continue a plan, and a small visit budget is spent on those moves. The published style is maximum activity for one’s own pieces and restricted activity for the opponent.

Where Stockfish is weaker. In equal blocked positions, not in every closed position. Game 61 of the 2019 superfinal still showed 0.00 at move 32 while a larger Stockfish showed 0.74, with pieces tied to a fragile pawn. A season 16 French kept Black’s structure fixed from move 20 to 52 while pieces improved. Late-move reduction searches the first moves fully and cuts later quiets harder than captures. A fifteen-move knight reroute does nothing on the ply it is played.

Ideas. The locked-node shelf is S12. History credit for the quiet move before the break is S13. Deep targets only where a locked search drifts are D5.

## Short time controls

Importance: breakthrough. See B3.

What the short budget wants. More depth when few nodes remain, and fewer blind spots when many remain. One 2020 trial passed the short test and was failing the long test. A later time-allocation change, scaling think time from root complexity, passed both tests and was described as especially effective at short controls.

Where Stockfish is weaker. Not in the 2025 standings. It has won the main events since 2020. The relative weakness is an older place drop, a modest 1+1 margin against the next CPU engine, and a reduction setting the authors already saw fail when it was left on for both clocks. CCC 24 bullet final was 567.5–432.5 over 1000 games. CCRL leads on the opened lists are a few Elo. A fixed-node curve puts the largest NNUE gain over an older Stockfish at short node counts, then a flatten because many positions become draws.

Ideas. Clock-gated reductions are B3. The bullet cap on complexity time is T10. The cheap eval on quiet non-PV nodes at bullet is N6.

## Endgames tablebases do not solve

Importance: routine. Six-piece tables in current top engines were measured near zero to a few Elo. The open hole is the parent the probe never sees.

What still works. Ordinary search until a line enters the table. Separate nets by piece count, and deleting a piece to probe the remainder, missed. A win/draw/loss label with no distance taught the outcome and skipped whether the entry was playable. About half of practical eight-piece endings were described as the blocked-opposing-pawn subset, and that subset is what has been generated, for small pawn counts only.

Where Stockfish is weaker. It already probes during search. On 2020 books drawn from its own long games, the eval overlapped table wins and table draws in a seven-piece rook ending, and the most common eight-piece material was rook and three pawns versus rook and two. Those figures are classical, bullet, and not a current match deficit. A 2026 description of eight-piece pawn races whose scores jump with depth has no game count.

Ideas. The capture-parent label is D10. The one quiet non-reduction before a table win is S14. The rook that meets the passer is S15.

## Sources

https://starcraft.ai/documents/260/alphazero_preprint.pdf
https://arxiv.org/html/1712.01815
https://danamackenzie.com/blog/?p=5072
https://www.chess.com/article/view/the-evaluation-of-material-imbalances-by-im-larry-kaufman
https://stockfishchess.org/blog/2020/introducing-nnue-evaluation
https://chessprogramming.org/Stockfish_NNUE
https://lczero.org/blog/2020/04/wdl-head
https://lczero.org/blog/2020/04/tcec-s17-super-final-report/
https://github.com/official-stockfish/Stockfish/issues/2721
https://official-stockfish.github.io/docs/stockfish-wiki/Stockfish-FAQ.html
https://matthewsadler.me.uk/engine-chess/stockfishs-opening-repertoire/
http://mytcecexperience.blogspot.com/2022/12/season-23-noomen-extra-bonus-opening.html
https://komodochess.com/store/pages.php?cmsid=14
https://github.com/official-stockfish/WDL_model
https://tcec-chess.com/articles/Sufi_17_-_Sadler.pdf
https://tcec-chess.com/articles/Sufi_15_-_Sadler.pdf
https://wiki.chessdom.org/TCEC_Season_15_Superfinal_Game_61_%E2%80%93_Stockfish-Leela
https://chessprogramming.org/Futility_Pruning
https://chess.stackexchange.com/questions/24867/bad-stockfish-evaluation
https://github.com/official-stockfish/Stockfish/commit/cd0b8b4cf28208fffef931322749205a0ddc6066
