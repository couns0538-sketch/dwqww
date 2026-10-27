# S20 idea sources

- Spec: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 2 item 12 / inventory S20. The goal is a fixed-depth re-search with the
  lock, WDL/score blend options compatible with the D filter, and a 1M rescored sample with stats and sha256. The
  crew rework (10:30) says blend defaults follow the f006 recipe.
- Rescoring self-play positions with a deeper fixed-depth search is the standard "relabel" step of NNUE data
  pipelines (e.g. Stockfish's `rescore` / nnue-pytorch data tools, and Leela-style relabelling with a stronger
  search). The WDL-blended target `L*sigmoid(k*s/400) + (1-L)*result` is the trainer's own target formula (Forge
  `train_resid_v3b`, k = 2.25, the f006 blend schedule 1.0 -> 0.6).
- Formats and converters come from the archive's Job D format package: `fen2bin.cpp`, `hce_dump.cpp`,
  RECORD_FORMAT (text `FEN | stm_cp | white_result`, FPOS/FHCE v1). The v3b loaders are read from a renamed copy
  of the trainer by AST extraction.
- The self-play generator is the repository's `nnue_tools/forge-nnue-tools/forge_selfplay.py`, run with a copy of
  the lock exe at Idle on one CPU.
