# Forge residual NNUE pipeline implementation plan

> **For agentic workers:** use the existing isolated branch and the authorized native implementation workflow. Root owns Git; delegate independent tests and data tooling.

**Goal:** repair and verify training against the actual Forge6.4.24 residual inference contract; deliver a separately trained artifact without changing search or claiming Elo.

**Architecture:** reuse the supplied Python model and exporter. Add an actual-core inference/HCE probe, a residual trainer, and provenance-preserving finite data tools. Keep the shipped network and standalone exporter compatible.

**Tech stack:** C++20/GCC14, Python3.12, CPU PyTorch2.4.1, NumPy1.26.4, python-chess.

**Spec:** `validation/nnue-pipeline-20261023/SOL_PROMPT.md`.

## Constraints and design decisions

- Start at1ab50b2dd64d9b2f752f7f1285f6968cad2fd792; no search edits. Previous unfinished work is preserved on its original branch.
- The actual model is768→128 per perspective, STM first, SCReLU, int16/4096; output is a residual logit converted by400/2.25 then clipped/truncated before adding HCE.
- Preserve old float32 loader layout and default standalone export; add explicit residual export metadata.
- All outputs use new directories. Keep original data, checkpoints, failures, commands and hashes.
- Legacy13.5M rows have no authenticated game IDs or best moves. They may train only; validation uses fresh completed, identified games. Remove every validation position key from training. Do not invent legacy game IDs.
- For missing best moves, reject any position with a legal capture, promotion or checking move. Record this conservative filter separately from known-best-move filtering.
- Use score cap1000cp, seed20261023, fresh game hash split20%, residual zero-output initialization, result weight0→0.1, cosine learning rate. Select by the complete held-out teacher metric, compared with HCE and the initial model.
- No optional buckets until the basic contract, exporter and loss tests pass. QA owns the later1000-game gate.

## Review focus

Black score/result orientation; residual versus standalone scale; quantization and lane reduction; same-game/position leakage; missing provenance or interrupted games; epoch selection worse than HCE; truncated validation; input mutation and overwritten output.

## Task1 — native baseline and tests first

- [ ] Verify supplied source against Git and freeze old network/search hashes.
- [ ] Build Release, run all14 CTests and capture `bench11` signature292545.
- [ ] Add actual-core JSON probe and2048-position Python/C++ parity test (maximum1cp after integer conversion); include both sides and special moves.
- [ ] Record original export residual-argument failure and tests for offset, schedules, complete validation and data identity.
- [ ] Commit tests/probe and original supplied tools. Run CTest and bench after the commit.

## Task2 — trainer and exporter

- [ ] Implement `residual_logit_target=(score-hce)*2.25/400` and `sigmoid(hce*2.25/400+net)` supervision, with the documented result ramp.
- [ ] Add strict prepared-data manifest/hash checks, cosine schedule, baseline mode, initial and per-epoch exclusive checkpoints, and complete held-out metrics.
- [ ] Extend the shared exporter with `residual=False` compatibility and explicit residual128 export.
- [ ] Run the RED/GREEN tests, old-tool tests and real-core parity. Commit; run CTest and bench.

## Task3 — data provenance and training

- [ ] Add finite complete-game generation with actual best moves/game IDs and OwnBook disabled, reusing the existing game loop.
- [ ] Prepare packed features/HCE/labels with disjoint held-out games and validation-key exclusion; legacy rows stay training-only.
- [ ] Freeze data, split, model and stopping settings before training. Start with bounded representative data, preserve all epochs and report actual positions used.
- [ ] Compare HCE, shipped HCE+net, new HCE+net and the residual term alone on the same held-out positions; verify the exported network through real C++ inference.
- [ ] Commit data tools and evidence; run CTest and unchanged-network bench. Publish and verify the branch and trained artifact.

## Final report

One page: verified contract and tests, counts and exact held-out losses/margin, artifact/source hashes, limitations, QA handoff. A lower training loss is not Elo evidence.
