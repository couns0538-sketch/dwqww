# IDEA_SOURCE (R6, nnue-pytorch AMD port)

- Source of the code in this folder: nnue-pytorch (https://github.com/official-stockfish/nnue-pytorch), commit
  b26145006e54e6461cb4b51944ab05cc4850c580, GPL-3.0. The Triton kernels re-implement the maths and launch layout
  of its CuPy kernels `fused_ft_kernel.py` (fused double FT forward, scatter backward with fp32 atomics, per-tile
  bias reduction) and `sparse_linear_kernel.py`. The autograd wrappers follow `fused_ft_functions.py`.
- Licence consequence: the port is GPL-3.0 and stays in this tools folder / the trainer tree
  (`F:\opus_scratch\r6\nnue-pytorch-amd`, branch `opus-r6-amd`; `F:\nnue_pytorch`).
- Forge engine sources (`src/`, `include/`, `tests/` of the engine): **no code from here**. Ideas that could be
  used there, written from scratch: none taken in R6 (the engine does inference only; the FT gather it already
  has is its own code).
