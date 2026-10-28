# S-A4 — hidden layer 512 (after S-A2)

Branch `opus-sol-SA4` = `opus-sol-SA2` (4b2a6800: NnueInt16 + trainer `--weight-clip`) + this job.

## Engine: H512 behind a compile flag (default build = the lock's H256 net, identity)
- Width: `-DFORGE_NNUE_HIDDEN=512` (existing flag; all builds pass 256). Net: new flag `FORGE_NNUE_WEIGHTS` selects an
  include file instead of `src/nnue_weights.inc`; its static_asserts reject a width mismatch.
- Box recipe: `build_pc.sh "$PWD" out.exe -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512 '-DFORGE_NNUE_WEIGHTS="F:/…/net.inc"'`.
  CMake: `-DFORGE_NNUE_WEIGHTS_FILE=<net.inc>` with `-DFORGE_NNUE_HIDDEN=512` in `CMAKE_CXX_FLAGS`.
- Both NNUE paths work at H512: float (16 lane sums) and NnueInt16 (int16 weights, int32 accumulators; eligibility and
  int64 output bound hold: 2·512·8192·32768 = 2^38 ≤ 2^53). Memory per search-stack entry doubles (float + int32
  accumulators: 8 KiB at H512 vs 4 KiB at H256).
- CTest `forge_nnue_h512_tests`: the S-A2 test (`tests/nnue_int16_tests.cpp`) built for H512 with a seeded synthetic net
  generated at build time (`tests/nnue_gen_net.cpp`, 512 units, seed 20261027) — int16 == integer reference, float ==
  float32 emulation, incremental == fresh, representation tag, analytic float/int16 bound; runs in CI (release, ASan, TSan).
- `mutation_check_sa4.py <worktree> <new out dir>`: width bugs (loops stopping at unit 256, a fixed 256 offset, the
  include flag ignored) must fail at H512; they pass at H256 (why the H512 target exists).

## Nets (scratch `F:\opus_scratch\sol_SA4\nets`, sha256 in `logs/scratch_outputs_sha256.txt`)
- `h512_smoke_e2.inc`: trained with `trainer_v3c_clip.py --shape 512 --weight-clip` (renamed copy, CPU, data32 sample,
  2 epochs, seed 99); deterministic (2 runs byte-identical). Pipeline artifact, not a playing net.
- `h512_widened_lock_split.inc`: the lock net widened by `widen_net_sa4.py --mode split` (unit copies, output weights
  split ceil(w/2) + rest): NnueInt16 evaluation identical to the lock's on every position — H512 parity/NPS on the
  lock's search tree.
- `h512_widened_lock_zero.inc/.pt`: `--mode zero` (lock units + 256 new units with zero output weights): the optional
  GPU warm start (`GPU_RECIPE_H512.md`).

## How to run
```sh
cd /f/opus_scratch/sol_SA4; export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP=… TEMP=…
J=<worktree>/opus_round1/sol_SA4
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa4.py --stage
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa4.py --suite r1 && nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa4.py --compare r1   # H512 smoke net x2
nice -n 19 $PY -I -B $J/widen_net_sa4.py --net <lock .inc> --mode split|zero|copy --out x.inc [--pt x.pt]
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa4.py --suite w1 && nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa4.py --compare w1   # lr-0 warm starts
# parity (per net; dump built with -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512 -DFORGE_NNUE_WEIGHTS=…, see ../sol_SA2/README.md)
nice -n 19 $PY -I -B ../sol_SA2/sa2_parity.py --net <net.inc> --fens fens_10k.txt --dump dump_avx2.tsv --dump dump_scalar.tsv --out p.json
nice -n 19 $PY -I -B $J/cross_width_check.py --h256 <SA2 lock dump> --h512 <split dump> --out x.json
# bench + NPS (advisory, CPU-time NPS on the loaded PC)
nice -n 19 $PY -I -B ../sol_SA2/uci_bench.py <exe> [--opt NnueInt16=true] --depths 11 13 16 20
nice -n 19 $PY -I -B ../sol_SA2/nps_ab_opts.py <H256 exe>[::NnueInt16=true] <H512 exe>[::NnueInt16=true] 5 16 20 --allow-node-diff
```
GPU: `GPU_RECIPE_H512.md` (queue lines for the crew; not run here).
