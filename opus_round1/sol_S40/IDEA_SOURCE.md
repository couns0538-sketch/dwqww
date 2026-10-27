# IDEA_SOURCE (S40 cross-folder datagen dedupe + merge)

IDEA_SOURCE: deduplicate a second self-play output against the main training data and the 013/014 holdout, by
position and by game, and write new sealed shards in the trainer's record format, as specified in Sol's S40 task
(`forge_sol_all_jobs_inventory_20261026.json`, job S40, spec line 211; copy `F:\opus_scratch\sol_inventory_17aa0cae.json`).
Ideas only; no engine code is involved and nothing is copied from another engine.

- Record formats: the PC's own converters `tools/fen2bin.cpp` (FPOS v1) and `tools/hce_dump.cpp` (FHCE v1) under
  `F:\forge_nnue_train\tools` (read-only; byte-identical copies used in scratch, sha256 in the logs), and the v3b
  trainer's loader (`load_set`, `load_set_mmap`), which the outputs must satisfy unchanged.
- Text format, per-folder dedupe, `.part` / `.md5` sealing and the committed-offset table: the PC generator
  `C:\Users\Administrator\grok-pc\nnue\forge-nnue-tools\forge_selfplay.py` (read only).
- Position identity (board32 + side to move) and the conservative ordered-text game rule with the 20-in-100
  interleaving tripwire: Sol's Job D filter, as already used in opus-sol-S16 / opus-sol-S17.
- 64-bit candidate key: the splitmix64 finalizer constants (Steele, Lea, Flood, "Fast splittable pseudorandom number
  generators", OOPSLA 2014), as in opus-sol-S16; every candidate is confirmed byte for byte.
- Game ID of an inferred group = sha256 content fingerprint of its rows (original to this job).
- numpy (BSD) and python-chess (GPL-3.0, test reference and fixture builder only) are used as libraries from the PC's
  read-only NNUE venv; nothing is installed.
