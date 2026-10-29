# IDEA_SOURCE — FB2-J7 (NNUE v4 ideas, prototyped in the trainer)

Trainer-only prototypes in `tools/nnue/fable_nnue_train.py` (branch `fable-fb2-j7`, on top of the J1 trainer); no
engine format exists for them yet, so their checkpoints are `.pt` models scored with the float forward
(`--float-exact`, `float_score`) and the baseline is scored the same way for a fair comparison. No code copied.

| prototype | flag | idea | source (idea only) |
|---|---|---|---|
| larger first layer | `--hidden 1024` (already supported by v3: loader, AVX-512 kernels, FB1 measured 0.74x NPS residual / about 1.0x standalone) | more features per king bucket | every NNUE generation (SF HalfKA 1024..3072, Koivisto, Berserk) |
| second layer | `--l2 N` (2H -> N -> 1 with clipped ReLU, per output bucket) | a hidden layer after the accumulator lets the net combine features non-linearly before the output | Stockfish's L1 -> L2 -> L3 stack (2020 -), Ethereal/Berserk 2-layer nets |
| pairwise dual-perspective term | `--pairwise` (sum over units of w3[ob] * screlu(us) * screlu(them)) | an interaction between the two perspectives' activations (own idea in this form; related to SF's "pairwise multiplication" of the first layer halves, 2024) | Stockfish SFNNv9 pairwise mul (idea), own formulation |
| king-bucket refinement | `--king-buckets 16` (v3 layout "0123 4567 8899 aabb cccc dddd eeee ffff", mirrored) vs 8 | finer king placement in the first two ranks and separate bands above | FB1's layout rationale; SF's 32-bucket HalfKAv2_hm, Koivisto's 16 buckets |

Protocol: every prototype and the H512/8/8 baseline train for the same wall budget on one thread with the same
seed, data, batch, LR and WDL schedules (`fable_fb2/j7/README.md`); the comparison is the float holdout b0.6 at
equal positions seen (per-phase breakdown kept), i.e. an early-learning comparison, not a converged one.
