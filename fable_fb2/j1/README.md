# FB2-J1: real NNUE v3 net trained at scale (branch `fable-fb2-j1`)

Tools (all CPU, read-only venv `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe -I -B`, `nice -n 19`,
one thread; environment `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`):

1. Data split (6.4 min for 288M rows):
   `tools/nnue/fable_nnue_data.py split --pos-glob "D:/grok-pc-data/forge_push/nnue_data/pos/forge_selfplay_*.pos"
   --hce-dir D:/grok-pc-data/forge_push/nnue_data/hce --out F:/opus_scratch/fable/data --holdout-shards _013,_014
   --holdout-rows 200000 --train-shards 64 --seed 1 --partitions 32`
   -> `F:/opus_scratch/fable/data/train/fb2_train_000..063.pos|.hce`, `holdout/fb2_holdout_200k.pos|.hce`,
   `MANIFEST.json` (read-only). Verify: `fable_nnue_data.py check --out F:/opus_scratch/fable/data`.
   Unit test: `tools/nnue/test_fable_nnue_data.py <scratch>` (synthetic shards, set-based reference; PASS).
2. AL1 reference on the holdout: `F:/opus_scratch/fable/s31tool/forge_sol_S31_avg_ckpt.py score --nets src/nnue_weights.inc
   --pos .../fb2_holdout_200k.pos --hce-dir .../holdout --out logs/al1_fb2_holdout_score.json`.
3. Training (resumable chunks, checkpoint every 30 min with exact score + parity):
   `tools/nnue/fable_nnue_chunks.py --out F:/opus_scratch/fable/fb2/train_j1 -- <python> -I -B tools/nnue/fable_nnue_train.py train
   --pos-glob "F:/opus_scratch/fable/data/train/fb2_train_*.pos" --hce-dir F:/opus_scratch/fable/data/train --out <same>
   --hidden 512 --king-buckets 8 --output-buckets 8 --mirror --steps 93000 --batch 8192 --lr 1e-3 --lr-schedule cosine
   --lr-final 5e-5 --warmup-steps 500 --blend-schedule linear --blend-start 0.9 --blend-end 0.6 --chunk-rows 250000
   --chunks 8 --refresh-every 25 --shard-weighting rows --val-pos <holdout.pos> --val-hce <holdout.hce> --val-every-minutes 10
   --ckpt-every-minutes 30 --exact-pos <holdout.pos> --exact-hce <holdout.hce> --parity-tool <forge_nnue_v3_tool.exe>
   --parity-fens F:/opus_scratch/fable/parity/positions_10k.fen --target-loss 0.014310 --plateau 3 --threads 1 --seed 1 --max-minutes 240`
   Outputs in the run dir: `log.txt`, `status.json` (every checkpoint with exact b0.6/b0.8/b1.0, per-phase b0.6,
   parity counts), `ckNN_stepS.fnn3`, `best.fnn3`, `ckpt.pt` (resume), `chunks_log.txt`.
   Resume by hand: add `--resume <run>/ckpt.pt` to the same command.
4. Engine: `FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp" build_pc.sh` (box recipe) -> `forge_fable_v3.exe`;
   identity OFF with `uci_check.py --full`; NPS with `tools/nnue/fable_nnue_nps.py`; sanity games with
   `tools/nnue/fable_nnue_games.py` (see the report).

Evidence: `logs/` (split log, manifest copy, AL1 score, smoke-test logs, training log copies, checkpoints table).
