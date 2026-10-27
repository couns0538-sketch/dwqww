# S20 relabel/rescore tool + 1M rescored sample

- `opus_rescore.py`: fixed-depth re-search of Forge text training lines (`FEN | stm_cp | white_result`) with a
  lock-recipe engine. Depth 8 by default, Threads 1, Hash 16, `ucinewgame` before every position (deterministic),
  Idle priority.
  - Mate scores become ±max-score; cp scores are clipped to ±max-score (3000).
  - Optional WDL blend `--blend L` with k = 2.25. The default 1.0 keeps the pure score: the f006 recipe blends at
    training time.
  - Chunked and resumable (`--chunk-lines`, `progress.json`, chunk sha256 checked on restart), joined into
    `rescored.txt` at the end. It refuses any output directory outside `--allowed-root`.
- `opus_rescore_tests.py`: 7 tests (format, sign, mate/clip, blend formula, resume and refusal behaviour).
- `opus_rescore_pilot_check.py`: format, STM-sign agreement, mates, NaN, material sanity, and an every-Nth
  comparison with the original labels.
- `opus_rescore_loadcheck.py`: fen2bin + hce_dump conversion, then both v3b loaders (RAM and mmap). The loaders are
  AST-extracted from a renamed trainer copy; the trainer is never run. Sol's D filter runs on the same files.

## Reproduce (paths of this run)
```
python -I -B opus_rescore.py --engine F:/opus_scratch/rescore_d8/bin/forge_al1_rescore.exe \
  --in F:/opus_scratch/rescore_d8/input/selfplay_1m.txt --out-dir F:/opus_scratch/rescore_d8/full --depth 8
python -I -B opus_rescore_pilot_check.py --in <input> --rescored <out>/rescored.txt --out <json> --sample 2000
python -I -B opus_rescore_loadcheck.py --rescored <out>/rescored.txt --stem <name> --work <new dir> \
  --fen2bin F:/opus_scratch/rescore_d8/bin/fen2bin.exe --hce-dump F:/opus_scratch/rescore_d8/bin/hce_dump.exe \
  --loaders F:/opus_scratch/rescore_d8/input/opus_nnue_smoke_s20_v3b_loaders_src.py [--dfilter <Sol's D filter>]
```
The engine is a box-recipe build of the AL1 lock sources (identity ALL OK, `logs/step0_*`). The input is the first
1,000,000 lines of an 11,700-game lock self-play run (5000 nodes/move) generated for this job (stage A).
