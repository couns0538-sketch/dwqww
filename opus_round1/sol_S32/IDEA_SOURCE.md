# S32 idea sources

- **Spec**: Sol's S32 "Self-play datagen v2" (SOL_LEFTOVERS_FOR_CLAUDE.md item 16; inventory `jobs[S32].spec_verbatim`):
  datagen mode behind a UCI/CLI flag, fixed-node search, random opening plies, win/draw adjudication, direct FPOS/FHCE
  output, safe with several processes; pass = flag-off standard pass, same seed -> same sha256, v3b loads a 1M sample
  (RAM and mmap), sign conventions, >= 1.5x selfplay.py positions/s or explain. Sol left no prepared S32 files.
- **Game rules, filters, labels**: the PC generator `nnue/forge-nnue-tools/forge_selfplay.py` (sha256 9ff8a48b…):
  `play_game`, `terminal_result`, `decisive_side`, `eligible_score`, Threads 1 / Hash 16, `ucinewgame` per game, and its
  publish-without-replace pattern (`publish_new`: Windows rename, POSIX link). The spec's `h256tools/selfplay.py` is not
  on the PC (MISSING_INPUT); the brief named forge_selfplay.py as the tool to compare against.
- **Record format**: `fen2bin.cpp` / `hce_dump.cpp` (lock archive `5_nnue/datagen_and_format/record_format/`, same
  sha256 as `F:\forge_nnue_train\tools\`), `RECORD_FORMAT_v3b_pos_hce_20261025.md`, and the v3b trainer's
  `read_pos_header` / `load_set` / `load_set_mmap`.
- **RNG**: SplitMix64 (G. Steele, D. Lea, C. Flood, "Fast splittable pseudorandom number generators", OOPSLA 2014).
- **Prior art for in-engine data generation** (idea only, no code used): Stockfish's NNUE training-data generator
  (`generate_training_data`/`gensfen` in the Stockfish tools branch) — search inside the engine process, binary output.
- Own design: build switch FORGE_DATAGEN (default off), prefix claim via the exclusive `.games.part`, `.pos` published
  last, per-attempt seeds (`game_seed(seed, attempt)`), `--convert` mode reusing the same writer, draw adjudication off
  by default (forge_selfplay.py has none).
