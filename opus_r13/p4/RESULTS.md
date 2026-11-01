# R13 Phase 4 - v2-feature nets with bullet (FORGENN2) - IN PROGRESS (no GPU run: needs Engine NNUE's window)

Branch `opus-r13-p4-v2nets` (from main). UNPROVEN: no net trained here yet; no Elo claim.

## Deliverables (this branch, opus_r13/p4/)
| file | what | state |
|---|---|---|
| forge_v2_bullet/ (Cargo.toml, src/main.rs) | bullet da426a49 trainer, stages a / b / c in one binary; own SparseInputType `ForgeV2` | written, build pending |
| export_v2.py | bullet raw f32 `quantised.bin` -> FORGENN2 (round(x*4096), overflow = error) via the crew's write_v2 | written |
| forge_nnue_v2.py | crew tool, unchanged copy of forge-bundle-int b7c17722 tools/nnue/forge_nnue_v2.py | copied |
| v2_eval.cpp | engine-side parity harness: forge::nnue::v2::load + refresh + evaluate (engine's own feature code) | written, build pending |
| eval_ref.py | trainer-side reference: numpy float32 replay of nnue::v2 on the exported file + the Rust feature lists | written |

## Design facts (checked in the sources)
- FORGENN2 (forge/nnue_v2.hpp, forge-bundle-int b7c17722): (inputs -> H) per perspective, SCReLU = clamp [0, 1] then square,
  side to move first, one linear output per bucket; cp = trunc(out * 400 / 2.25); weights int16 / 4096 (w1, wt, wp, b1:
  WeightScale; w2, b2: OutputScale, both 4096). Stages: a = 768 + 8 output buckets; b = a + O6 threats (9216, count-valued);
  c = b + O7 pawn pairs (1792). King buckets stay 1 (C4 not in the staged order).
- Output buckets: bullet MaterialCount<8> = (pieces - 2) / 4 = Forge's default map (forge_nnue_v2.output_layout(8)).
- bullet's ChessBoard is stored in the side-to-move frame (black to move: ranks flipped, colours swapped), so the side-to-move
  features use the stored squares, the other perspective square ^ 56 with colours swapped (same as bullet Chess768).
- FTP1 block-aware L1 permutation: does not apply to FORGENN2 (no int8 L1 layer after the hidden layer; the output is a
  dense dot of 2H floats, where the order of hidden units changes nothing). It applies to the HalfKA .nnue path.
- All three output paths of nnue::v2::output (AVX2, SSE, scalar) map hidden unit h to lane h % 16 and add the lanes in order,
  so the paths are bit-identical by construction and a float32 replay (eval_ref.py) can match them exactly.

## Next
cargo build (CPU backend) with my own CARGO_HOME copy (no writes into F:\bullet_hip), feature parity (Rust lists vs engine via
v2_eval on 10k FENs per stage, AVX2 + SSE builds), CPU smoke on 1M positions, GPU_REQUEST.md.
