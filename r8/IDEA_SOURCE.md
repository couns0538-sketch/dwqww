# IDEA_SOURCE (R8, self-play data generation speed)

Ideas only: no code from any of these projects is in this branch. The driver is new code; the chess rules come from
Forge's own Board (`src/board.cpp`), the game rules from the user's `forge-nnue-tools/forge_selfplay.py`.

| source (licence) | what it does | idea taken | used? |
|---|---|---|---|
| Stockfish `tools` branch, `src/tools/training_data_generator.cpp` (`generate_training_data`, ex `gensfen`) (GPL-3.0, repo licence) | in-engine self-play with depth/node limits, random moves at random plies, `write_min_ply`, eval-limit win adjudication over 4 plies, low-score draw adjudication from ply 80, insufficient-material draws, one shared duplicate-hash table (2^26 keys), per-game position buffer, buffered writer | in-process de-duplication instead of a database; buffer a game and write it once it is finished | yes (driver: in-memory set, per-game batch, 1 MiB write buffer) |
| Stormphrax `src/datagen/datagen.cpp` (GPL-3.0-or-later, file header) | in-engine datagen: soft 24k / hard 1M nodes, 8-9 random plies, depth-10 opening verification (drop |score| > 500), per-thread searcher with hash 16 reset per game, in-check / noisy-best-move positions tagged as filtered, win adjudication 1250 cp x 5 plies, draw adjudication from ply 70 (|score| < 10 for 10 plies), Syzygy adjudication, marlinformat/viriformat output per thread, one batch per game, NUMA binding per worker | per-thread engine with a small fixed hash, filtering at generation time, per-game batches, the list of adjudication / opening-verification options (as switchable options only) | per-thread engine + filtering + batches: yes; opening verification and draw adjudication: not used (they change the data) |
| Berserk (GPL-3.0, repo licence) | no data generator in the public tree (a `fen-gen` branch is linked from the README) | - | no |
| Obsidian (GPL-3.0, repo licence) | trained on Lc0 data; no data generator in the repo | - | no |
| python-chess (GPL-3.0) semantics, via the live script | `is_insufficient_material`, `is_repetition(3)`, `fen(en_passant="fen")`, score ordering of mates | the driver reproduces these rules in its own code (Forge Board), proven by the line-by-line equivalence test | rules only |
| own (R8) | the live pipeline's cost is Python + python-chess per move (14% of wall time outside go -> bestmove) plus a Python worker sharing the engine's two logical CPUs, and one SQLite insert + fsync per game against a 7.5 GB table | a native driver for the unchanged engine; direct FPOS `.pos` output | yes |
