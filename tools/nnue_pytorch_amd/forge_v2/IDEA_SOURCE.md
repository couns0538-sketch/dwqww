# IDEA_SOURCE (R7 J1, forge_v2)

| idea | source | how it is used here |
|---|---|---|
| Forge v2 model, loss, Adam + cosine LR, weight clip, K32H3 -> Forge index remap, export through Forge's writer | Grok Bot's `F:\nnue_pytorch\forge_tools\train_forge_v2.py` and `parity_forge_v2.py` (local tools in the GPL tree, read only, 2026-10-29) | copied into `train_forge_v2_fast.py` (plain backend unchanged) and `parity_forge_v2_fast.py` |
| sparse gather-sum forward, atomic scatter backward, bias reduced in registers over POS positions per program | nnue-pytorch's CuPy feature-transformer kernels (GPL-3.0) via the R6 Triton port (`tools/nnue_pytorch_amd/src/.../triton_ft_kernels.py`) | same kernel structure, new math: SCReLU of the us/them-mixed accumulators instead of SF's pairwise product |
| feature remap inside the kernel (no host-side index rewrite) | own (R7) | the 73,729-entry int32 table is read in both kernels |
| pinned host memory + non-blocking H2D, bounded queue depth | nnue-pytorch's `use_pinned_memory` transport option; CUDA event throttling (standard practice) | `--pinned`, `--inflight` |
| Forge v2 network semantics and file format | Forge `include/forge/nnue_v2.hpp`, `tools/nnue/forge_nnue_v2.py`, `tools/nnue/nnue_v2_tool.cpp` (read only) | parity reference; nothing of the GPL code went into Forge sources |
