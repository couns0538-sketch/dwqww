# IDEA_SOURCE — FB2-J2 (self-play datagen v2)

All code is new (`include/forge/datagen2.hpp`, `src/datagen2.cpp`, `tests/datagen2_tests.cpp`,
`tools/nnue/fable_datagen_decode.py`, the `datagen` branch in `src/uci.cpp`); nothing was copied from another engine.
The engine API it uses (Board, Searcher, Evaluator) is Forge's own. Ideas and where they come from:

| idea | source | here |
|---|---|---|
| in-engine self-play writing the trainer's FPOS/FHCE directly, per-game `ucinewgame`, deterministic per-game seeds, win adjudication by a streak of the same side being ahead, filters (quiet best move, not in check, no mate, |score| cap) | Forge job S32 (`opus-sol-S32`, `src/datagen.cpp` on `opus-r3-stack`) and the PC generator `forge_selfplay.py`; the terminal-rule order is S32's | the same game rules so that the labels stay comparable with the production shards; S32's record rule is the special case `--pv-capture-plies 1` |
| binpack-style game storage: start position + move list + per-ply score, positions rebuilt by replay | Stockfish / nnue-pytorch `.binpack` (Sopel's format: positions stored as move chains) — idea only | FGB1: 5 bytes per ply (u16 move, i16 score, u8 flags) + the start FEN per game; 37 bytes per record in FPOS+FHCE; the converter and a python-chess decoder rebuild the rows exactly |
| random-opening diversity: uniformly random plies with a per-game jittered count, then softmax (temperature) sampling over shallow-search move scores, then an evaluation cap that redraws lopsided openings | common datagen practice (Stockfish `gensfen` random moves / `random_multi_pv`; Leela's temperature sampling; CCRL/fishtest books) — ideas only | `--random-plies N --random-plies-jitter J --temp-plies M --temperature T --temp-depth D --opening-eval-cap C --book FILE`; the summary reports distinct start and post-opening positions |
| draw adjudication after a minimum ply when both sides' scores stay inside a window | cutechess-cli / fastchess `-draw movenumber=.. movecount=.. score=..` | `--draw-cp --draw-plies --draw-min-ply` (off by default, on in the smoke) |
| filtering tactical positions by looking at the PV, not only the best move | own: a capture or promotion within the first k PV moves means the position is tactically unstable (k = 2 by default) | `RecordNoisyPv`, `--pv-capture-plies` |
| random subsampling of records to reduce within-game correlation; skipping the first plies after the opening | nnue-pytorch's `early_fen_skipping` / `random_fen_skipping` loader options | `--skip-prob p --min-ply P` (recorded in the flags, deterministic through the game's RNG) |
| gives-check as a reported (optionally filtered) attribute | own | `RecordGivesCheck`, `--filter-gives-check` |
| exactness tests: direct writer == converter == independent decoder, same seed == same bytes, checksum trailer | FB1's parity discipline (engine int == trainer int) | `forge_datagen2_tests` (C++), `fable_datagen_decode.py test` (python-chess) |
