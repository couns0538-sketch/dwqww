# OPUS R7 SPEED: AMD training path, data pipeline, engine NPS, gate throughput (WIP)

Branch `opus-r7-speed` (from main 5176ddf7). Engine changes live on `opus-r7-nps` (from the R5D engine head
`opus-r5d-matefix` 5882c383, because main carries no engine source). PC clock times. Machine exclusive: no
(gate conc 8, the live NNUE trainer on the GPU and self-play kept running).

Rules kept: BelowNormal (`nice -n 10`), at most 3 CPU threads in total, every torch run inside the R6 RAM guard
(aborts below 7 GB free; lowest free RAM seen in any of my runs: 7.73 GB, see J1), GPU runs at smoke size only
(batch 4096, 1 loader thread), nothing in `F:\forge_nnue_train` touched, no process killed, no STOP/PAUSE file,
GPL code only in `tools/nnue_pytorch_amd/`, no Elo claims. Supervisor "adopted running job" count stayed 7; the
live trainer printed 1.29-1.31M pos/s before, during and after my GPU runs.

## J1 Forge-net training on the fast AMD path: DONE
Code: `tools/nnue_pytorch_amd/forge_v2/` (README, IDEA_SOURCE). Evidence: `logs/r7/j1/`.
- **Kernel**: one Triton kernel pair for Forge's v2 shape (32 mirrored king buckets x 768, hidden 256, SCReLU
  stm|other, 8 output buckets). Both perspectives in one program, K32H3 -> Forge remap inside the kernel, backward
  with fp32 atomics and torch's clamp-gradient rule. The output layer is `x @ w2^T` + bucket gather.
- **Correctness** (`test_forge_v2_kernels.py`): Triton == Grok Bot's plain path on 3 real batches (output diff
  <= 2.4e-7, every gradient <= 4.7e-10); planted errors caught 2/2.
- **Speed** (batch 4096, 1 loader thread, same data, interleaved; `logs/r7/j1/matrix1`, `pinned/`):

| path | pos/s |
|---|---|
| Grok Bot's original `train_forge_v2.py` (steady state, steps 400-600) | 363k |
| plain path in my harness (embedding_bag + Adam), 2 rounds | 396k / 386k |
| Triton FT + Adam | 1,016k / 895k |
| Triton FT + fused Adam | 1,000k / 886k (978k over a 12.4 s, 3000-step run) |
| Triton FT + fused Adam + torch.compile of the loss | 950k / 918k (no gain) |
| **Triton FT + fused Adam + pinned H2D (`--inflight 3`)** | **1,447k / 1,443k** (unpinned in the same rounds: 976k / 981k) |
| GPU-only ceilings (one batch reused): plain / Triton fused | 472k, 457k / 1,492k, 1,574k |
| data path alone (loader + H2D): setup DLL / clang23 DLL | 3.71M / 5.1M |

  The fast path is **3.6-4.0x the plain path** at the same batch; the loader is not the limit. Peak private memory
  of my process: 3.24 GB in every final configuration. Pinned without the in-flight cap held 0.75 GB more (the host
  ran hundreds of steps ahead); the cap fixed that at equal speed. Losses agree to ~1e-6 between all variants
  (atomic summation order).
- **Export + engine**: `r7_triton_s3000` (3000 steps x 4096 on shard 015 converted by J2's tool, 978k pos/s, loss
  0.0092) exported with Forge's own `tools/nnue/forge_nnue_v2.py` (fnv1a `0dd0ee89e440a9d8`, sha256 in
  `parity/ARTIFACTS_SHA256.txt`). In `forge_r7_base.exe` (the `opus-r7-nps` base, identity ALL OK): `NNUE v2:
  loaded ... king buckets 32 output buckets 8 hidden 256 mirrored`, readyok, bench 13 = 957,760 nodes (1.93M nps;
  the compiled-in net on the same exe: 862,329). Depth-8 sanity: startpos +19, queen down -782, knight up +367.
- **Parity** (10,000 positions from `nnue_v2_tool positions`, engine eval = `nnue_v2_tool eval` built from the
  same tree with the exe's flags): float trainer vs engine **max 1.59 cp** (mean 0.52, 0 positions over 2 cp),
  dequantised max 0.9998 cp (the engine truncates), feature keys 20,000/20,000, output bucket 10,000/10,000,
  Triton vs torch reference 0.0006 cp. PARITY PASS.
- Recommended command: `train_forge_v2_fast.py --backend triton --fused-adam 1 --pinned 1 --inflight 3`.
- Limits: pipeline proof, not a strength-tested net (12M positions). Bigger batches, more loader threads and L1 >= 1024
  were not run (PC rules while the live trainer runs).
