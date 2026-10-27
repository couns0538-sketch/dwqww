# IDEA_SOURCE — S09fix (8 piece-count output buckets for the H256 residual net; QA fix-ups S09-1..5)

This file is the S09-3 deliverable: the idea sources of the 8 output buckets that Sol's S09 trainer patch
(`forge_sol_S09_trainer_20261026.patch`) and the CR-passed engine step 1 (`fc_buckets8_h256e12.patch`) implement.
Sol's packet had no IDEA_SOURCE for the bucket idea itself (only for the converter and the fast-FEN helper).

## The idea
Split the output layer (2H -> 1) into 8 heads (2H -> 8) and use, for every position, the head picked by the number
of pieces on the board including both kings: `head = clamp((pieces - 1) // 4, 0, 7)`
(2-4 pieces -> head 0, 5-8 -> 1, ..., 29-32 -> 7). The accumulator (768 -> H per perspective), SCReLU, residual HCE
term, sigmoid K 2.25, int16/4096 storage and float inference stay as they are. With one head (`--buckets 1`, the
default) nothing changes.

## Sources (ideas only; no code or weights copied)
1. **Stockfish layer stacks**, the general technique and the exact bucket formula:
   - nnue-pytorch documentation, "Multiple subnetworks (layer stacks)": "let's use 8 buckets, based on the integer
     quotient `(piece_count - 1) / 4`" — https://official-stockfish.github.io/docs/nnue-pytorch-wiki/docs/nnue.html
   - Stockfish `src/nnue/network.cpp`: `pcBucket = (pos.count<ALL_PIECES>() - 1) / 4` (current master combines it
     with a queen bucket for 32 stacks; the 8-stack versions used the piece-count bucket alone) —
     https://github.com/official-stockfish/Stockfish/blob/master/src/nnue/network.cpp
   - Chess Programming Wiki, NNUE, "Output Buckets" / "LayerStacks" — https://chessprogramming.org/NNUE
   Read for the idea and the formula only (checked 2026-10-27). Forge's net has no hidden layers after the
   accumulator, so "layer stacks" reduce to output buckets: 8 output rows instead of 1.
2. **Forge's own earlier work** (Couns's repository; reuse allowed):
   - `dwqww` commit `bde3dc9d` ("buckets8", by Sol): head-count macro, band formula, head-major W2 layout.
   - Coder's CR-passed step 1 `fc_buckets8_h256e12.patch` (sha256 `ed28132d…`, lock archive
     `5_nnue/research_buckets8_step1/`): engine loader with 8 heads, the `.inc` layout
     (`#define FORGE_NNUE_OUTPUT_HEADS 8`, `NnueW2[8*2H]` head-major, `NnueB2[8]`; the alias
     `FORGE_NNUE_OUTPUT_BUCKETS` is accepted), `make_heads_inc.py`.
   - Engine NNUE's `train_resid_b8.py` and its trained net `fc_buckets8_b8ep8_h256e12` (step 2, md5 `09227945…`,
     8 epochs fine-tuned from the h256_e12 net on Forge self-play 001-012, 015-019, holdout 013+014).
3. **Sol's S09 trainer patch** (`forge_sol_S09_trainer_20261026.patch`): the trainer side (8-row output layer, head
   gather by `(codes > 0).sum()`, 8-head export). S09 v2 keeps that code unchanged and only restores the CLI
   defaults (S09-2) and keeps the 1-head checkpoint config byte-identical.

## What S09fix itself adds (own work, no outside code)
Restored defaults + recipe-as-arguments file, the export/training identity checks (S09-1), the real-holdout
validation with an independent nibble piece count and a bias-shift head-selection control (S09-5), the CPU optimizer
check, the one-file patch helper (rebuilds the step-2 net from the lock archive), the packaging of Sol's packet into
one FILES index + per-step archives (S09-4), tests and a planted-bug check.

UNPROVEN: no 8-head net was trained here, no gate, no Elo or strength claim.
