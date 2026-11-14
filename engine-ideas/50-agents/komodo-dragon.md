# Komodo Dragon

Ideas only. Closed-source engine: these notes use published articles and interviews. Endgame technique has not reported yet.

## Hybrid selective search

Importance: routine.

What Dragon does. A normal alpha-beta mode and a Monte Carlo mode. In the Monte Carlo mode each node gets a short alpha-beta search, the score is turned into a win chance and backed up, and node choice looks widely then narrows. Extra root lines are described as already stored. A shallow root score past about seven pawns either way leaves that mode and finishes with ordinary search, so a certain win still prefers the short win. The settings page puts Monte Carlo about seventy Elo behind normal Dragon, stronger when both show several lines, and recommended for review and sparring rather than engine matches. Dragon 2 retuned search from values stored in the network. The practical rule from handicap games: in a good position, assume the opponent finds the best move; in a bad position, spend effort on replies a strong opponent might miss.

Where Stockfish is weaker. Not in engine-match strength. The 2018 hope that the Monte Carlo mode would pass Stockfish is not repeated in the 2023 note, and a 2024 article places Stockfish first on the lists. Stockfish is weaker at the narrow job of ranking several lines in one search. Its own documentation says a MultiPV above 1 spends the budget on the other lines and worsens the best move, with large published Elo costs at 60 seconds plus 0.6. Dragon’s supporting matches are against Stockfish 12 and a remark about Stockfish 13. Neither is current.

Ideas. The plausible-reply band is S3. The shared root record is S4. Margins taken from the net’s leftover error are S11, and the report says that one is not a Stockfish weakness.

## King safety

Importance: routine. No opened page measures Dragon against Stockfish on king safety.

What Dragon does. The strong behavior is in the network, trained on Komodo’s games and evaluation. The teacher’s king safety was revised across versions. A live King Safety control defaults higher than in older versions and is described as having minimal effect unless the non-network evaluation is chosen. Personalities that attack with no concern for their own king, or that put safety first, leave the network and cost about a skill level against computers.

Where Stockfish is weaker. Not shown. A 2017 interview, before Dragon, claimed Komodo was ahead in most things and behind in search depth. A 2021 interview illustrates pattern recognition with a piece jump, not with king safety.

Ideas. King-attack labels in the training target are D2. Separate own-king danger from the attack is D3. The bishop-and-castled-king slice is D4.

## Positional patience

Importance: routine. No opened page measures a current Elo gap in quiet positions.

What Dragon does. Patience is an evaluation habit, not a style switch. A published obituary records the description: lean on evaluation rather than depth, and in positions where others cannot make progress, prepare a break and then win. The Dragon notes say the more human style comes from learning what works in games, and that the network is also a more accurate evaluation, including some tactics a normal evaluation misses. In quiet positions the ordinary search score jumps as it finds deep details, and that behavior does better against engines. The other mode, which will not force the opponent’s only good move when the choice is close, does better against people and worse against engines.

Where Stockfish is weaker. Only in a narrow published sense. A 2014 quotation says Komodo was best at a middlegame once the tactics were over, and Stockfish was best at very deep tactics. The original interview page did not return the answers. Later articles place Stockfish first on the lists and still name it, or Dragon, for high-quality positional suggestions. The difference drawn in 2024 is the question each program answers: perfect-play result, versus practical difficulty.

Ideas. Quiet-conversion labels are D1. Nothing-to-play ordering is S5. The idle-piece probe is S6.

## Playing style

Importance: routine. Neither published record shows a large strength gain from style variety.

What Dragon does. Eight personalities. Default stays on the neural net. The other seven set their own parameters, use the traditional evaluation, and are about one skill level weaker against computers. Variety from 0 to 100 may play a different move and is expected to weaken play. At 5 and at 10, many thousands of ultra-fast games showed no detectable Elo loss, with an estimate of not more than about one Elo per five points. Dynamism scales the dynamic part of the evaluation and leaves material and pawn structure alone. A value around 80 is described as costing 20 to 30 Elo for more realistic scores. Armageddon treats a draw as a loss for the side that must win, then complicates or simplifies. The one numeric Armageddon result in the extract is a clock ratio, not a style score.

Where Stockfish is weaker. At published style variety, not at strength. The illustrated option list has skill and Elo limits that play a weaker move on purpose, and no personality, variety knob, or must-win switch. Contempt was removed in 2021 after a neural-net version was tried and did not work. Removal matched contempt 0 inside non-regression bounds. A reviewer wanted a must-win option because the engine accepts perpetuals a must-win player would refuse.

Ideas. Style directions inside a close-score band are part of O1, not a separate search. The must-win choice near the draw is O5.

## Time management

Importance: routine. These sources do not show Stockfish weaker at spending the clock.

What Dragon does. A per-move plan, a usage scale from −90 to +90, and a separate overhead for the GUI and the connection. The manual says 0 is the believed best usage and is still unchecked at long controls. Komodo 9, tuned on increment controls, forfeited more than 10 percent of game-in-one-minute games. A slower algorithm averaged about +8, mostly from removing forfeits, and was still slightly positive when forfeits were ignored. Extra endgame time was called a poor idea because many games are already decided. A longer think on the first move out of book showed no clear gain. In Monte Carlo mode the search can end when the tree cannot grow, and a shallow score past about seven pawns switches mode to finish a decided game.

Where Stockfish is weaker. Not on these pages. The sudden-death fix was aimed at Stockfish’s pace. Current Stockfish sets a soft target and a hard cap from the remaining clock, the increment, and moves-to-go, then scales the target when the score falls, the best move changes, or the best move already took most of the root effort. A 2024 spectator account of one long game, in which a large fraction of the clock was spent in the first eleven moves, is one reporter, not a controlled match, and it does not mention Dragon.

Ideas. The zero-increment fraction is T5. Holding surplus time for positions that are still open is T6. The lag margin, kept apart from the usage fraction, is T7.

## Evaluation ideas worth re-deriving

Importance: routine. No opened match isolates space, outposts, or bad pieces between current Stockfish and Dragon.

What is worth rebuilding. A published database study treats an unpaired bishop and a knight as equal on average, so the live question is whether the position is open or closed and whether a bishop is shut in by its own pawns. The bishop pair is treated as a material-like asset whose practical size changes with the remaining pawns. Dragon’s release note says the network was trained on billions of positions from Komodo games and that the program relied less on fixed rules after that. The experiment is to rebuild those distinctions as labels from Forge’s own results, then teach only the slice the network does not already score.

Where Stockfish is weaker. A large hole is unlikely once a network is trained. Introducing the neural evaluation gained about 90 Elo over the hand-made eval. Removing the classical eval later cost about two Elo. A 2024 article describes that class of engine as keeping much of the positional strength associated with Leela, and describes Stockfish as the engine that generally leads. One opened case where a hand correction still mattered is a bishop shut in a corner under Fischer Random castling. That is a different starting array. The official Dragon pages did not load for this department, so claims that appear only there are unused.

Ideas. The bad-piece residual is P4. Doubled pawns as separate structures are P5. Durable square control tested only where it disagrees with mobility is P6.

## Sources

https://www.chessdom.com/komodo-mcts-monte-carlo-tree-search-is-the-new-star-of-tcec/
https://komodochess.com/store/pages.php?cmsid=14
https://komodochess.com/dragon-3.3.htm
https://komodochess.com/dragon-3.htm
https://en.chessbase.com/post/komodo-dragon-2-is-here
https://en.chessbase.com/post/gm-kaufman-speaks-about-his-pet-dragon
https://en.chessbase.com/post/introducing-komodo-11
https://en.chessbase.com/post/the-komodo-files-working-with-a-chess-engine
https://en.chessbase.com/post/komodo-8-about-the-authors
https://new.uschess.org/news/inside-story-kaufman-what-your-computer-trying-tell-you
https://journals.sagepub.com/doi/pdf/10.3233/ICG-2014-37116?download=true
https://www.chess.com/article/view/the-evaluation-of-material-imbalances-by-im-larry-kaufman
https://chessprogramming.org/Doubled_Pawn
https://chessprogramming.org/Space
https://github.com/official-stockfish/Stockfish/pull/3575
https://github.com/official-stockfish/Stockfish/pull/4674
https://official-stockfish.github.io/docs/stockfish-wiki/Useful-data.html
https://www.talkchess.com/forum3/viewtopic.php?t=56171
https://talkchess.com/forum3/viewtopic.php?t=52464
