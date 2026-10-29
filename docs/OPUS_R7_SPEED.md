# OPUS R7 SPEED: AMD training path, data pipeline, engine NPS, gate throughput (WIP)

Branch `opus-r7-speed` (from main 5176ddf7). Engine changes live on `opus-r7-nps` (from the R5D engine head
`opus-r5d-matefix` 5882c383, because main carries no engine source). PC clock times. Machine exclusive: no
(gate conc 8, the live NNUE trainer on the GPU and self-play kept running).

Rules kept: BelowNormal (`nice -n 10`), at most 3 CPU threads in total, every torch run inside the R6 RAM guard
(aborts below 7 GB free), GPU runs at smoke size only (batch <= 8192, in practice 4096, 1 loader thread), nothing
in `F:\forge_nnue_train` touched, no process killed, no STOP/PAUSE file, GPL code only in
`tools/nnue_pytorch_amd/`, no Elo claims.

## J1 Forge-net training on the fast AMD path (in progress)
- `tools/nnue_pytorch_amd/forge_v2/forge_v2_kernels.py`: one Triton kernel pair for Forge's v2 shape (both
  perspectives, gather-sum, us/them mix, clamp, square; K32H3 -> Forge remap inside the kernel; backward with fp32
  atomics, torch's clamp-gradient semantics).
- `train_forge_v2_fast.py`: Grok Bot's trainer (same model, loss, Adam, clip, export through Forge's
  `tools/nnue/forge_nnue_v2.py`) with `--backend plain|triton`, `--fused-adam`, loader-only and synthetic modes.
- `test_forge_v2_kernels.py`: PASS on 3 real batches (output diff 2.4e-7, every gradient <= 4.7e-10); planted
  errors caught 2/2 (one wrong remap entry, side to move swapped). Log: `logs/r7/j1/test_kernels_1.log`.
- First smoke run (batch 4096, 1 loader thread, Triton + fused Adam): 895k pos/s over 180 steps (short window).
