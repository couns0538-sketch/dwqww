# Task for Sol 6.1 Ultra: rebuild and verify Forge's NNUE training pipeline (one 7-8 hour job)

You are working on Forge, my C++ chess engine (repo couns0538-sketch/dwqww, base commit `1ab50b2d`, Forge 6.4.24). It is a hybrid: hand-crafted eval (HCE) plus a 768->128x2 SCReLU residual NNUE. Today the net's validation loss is worse than HCE alone, so the net adds nothing. Your job is to find out why and fix it. Do NOT change search.

## Attached files
- `forge_source_1ab50b2d.tar.gz`: source at 1ab50b2d (src, include, tests, tools incl. tools/tune/nnue_train.cpp, docs, CMakeLists.txt). Key files: src/nnue.cpp, include/forge/nnue.hpp, src/eval.cpp, eval_params.cpp, src/nnue_weights.inc.
- `forge-nnue-tools.tgz`: Python trainer and self-play tools (train_nnue.py, convert_training.py, forge_selfplay.py), engine_contract.json, tests, a small example sample (examples/forge_sample.txt). Self-play file format: FEN | score | result.
- `NETS_history_GrokChess_and_Forge.md`: history of past net runs (mostly GrokChess; use as ideas only).
- A self-play data sample from my PC (about 13.4M positions exist there; the sample is what I attach).

## Hour 1: diagnosis only
Read the trainer, data generation, exporter, nnue.cpp, nnue.hpp, eval.cpp, eval_params.cpp and nnue_weights.inc. Write a short report on likely causes: target and scale mismatch with what the engine adds (the engine adds out*400/2.25 cp), split by game or not, label noise, WDL/result mix, filtering. Report HCE-alone and net validation loss on a game-level held-out set.

## Then build
1. A trainer-vs-engine parity test: the trainer's forward pass must match nnue.cpp inference on 1000 to 10000 FENs within quantisation error.
2. A residual trainer (target = search score minus HCE, at the scale the engine uses) with a position filter (no in-check, no tactical best move, a score cap), a game-level split, a result-weight ramp, a cosine LR schedule, per-epoch checkpoints, and a baseline mode that reports HCE-alone loss.
3. An exporter to Forge's .inc net format. Keep the old loader working.
4. Optional, only after 1-3 pass: 8 output buckets by piece count, with the matching nnue.cpp change.
5. A net-only vs HCE-only fixed-position report (no games).
6. A trained net from whatever data fits.

## Rules
- Work on a new branch off 1ab50b2d. Split commits, one concern each: tests first, then trainer fixes, then data tools.
- Run ctest and check `bench 11` after each commit. It must not change when no new net is loaded.
- Ideas only from public descriptions of top engines (Stockfish, Viridithas, Bullet-style trainers). No copied code, comments, tables or constants. Cite the idea source in each commit message.
- Write all outputs to fresh folders. Never overwrite existing data.
- Do not claim Elo. Strength is judged only by a 1000-game SPRT run by my QA bot.
- If the loss stays bad on clean data, report that it needs more data and state the position count you used.
- End with a one-page report stating what was verified and what was not.

## Acceptance
- Parity test passes.
- Held-out game-split loss of net plus HCE is below HCE alone, with the margin stated.
- Then my crew takes over: Code Review reviews the diff, and QA runs one 1000-game gate of 6.4.24 plus the net against 6.4.24.
