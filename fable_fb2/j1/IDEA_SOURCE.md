# IDEA_SOURCE — FB2-J1 (real v3 net trained at scale)

All code in this job is written from scratch for Forge; the sources below are where the *ideas* come from.

| idea | source | how it is used here |
|---|---|---|
| exact-duplicate removal of (position, side to move) before training; holdout rows win | Forge jobs S16 (6,069 training rows shared a position with the 013/014 holdout) and S17 (game-group leak audit) on `opus-sol-S16/S17`; common practice in NNUE data pipelines (nnue-pytorch's data tooling, Stockfish binpack discussions) | `fable_nnue_data.py split`: 64-bit row hash in 32 partitions, first occurrence kept, holdout shards hashed first |
| global shuffle of training rows (consecutive rows of a game are near-duplicates) | FB1 M4 finding (a single ordered shard overfits in minutes); nnue-pytorch shuffles games/positions across the whole set | scatter every kept row to a random output shard, then permute each shard in memory |
| phase-stratified holdout (same piece-count histogram as the training set) | own (so that the holdout metric weights every phase like the training distribution; per-phase losses are reported at every checkpoint) | largest-remainder rounding of the training phase fractions to exactly 200,000 rows |
| WDL-lambda schedule (teacher-score weight decreasing towards the game result) | nnue-pytorch `--start-lambda` / `--end-lambda` (idea only) | `--blend-schedule linear --blend-start 0.9 --blend-end 0.6`; the end value is the lock blend b0.6 of the metric |
| cosine LR decay with linear warmup | Loshchilov & Hutter, SGDR (2017); nnue-pytorch's default scheduler | `--lr-schedule cosine --warmup-steps 500` over the run horizon `--steps` |
| quantisation-aware training on the engine's integer grid, factoriser merged at export | FB1 M3 (`fable-nnue-arch`), nnue-pytorch's factorised feature sets | unchanged from FB1 |
| checkpoint = exported net + exact integer holdout score + engine parity; early stopping on a plateau | standard early stopping; FB1's `score` and `parity` commands | `--ckpt-every-minutes 30 --plateau 3 --target-loss <AL1 score>` |
| resumable chunks (optimiser state, schedules and RNG state restored) | standard checkpointing; the production supervisor's resume behaviour (A7) | `ckpt.pt` written atomically; `fable_nnue_chunks.py` relaunches with `--resume` |
| standalone (non-residual) H512 net | FB1 M5 NPS measurement (standalone 117-119% of AL1 per node, residual 83%) and equal loss per position seen | the J1 run trains a standalone net |
