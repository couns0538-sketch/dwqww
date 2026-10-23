# Forge6.4 residual NNUE tools

This directory reuses the supplied Python model and serialization code. The
original `train_nnue.py` CLI remains a standalone trainer. For Forge6.4.24's
HCE-plus-residual evaluation, use `residual_train.py` and its explicit residual
export. The shipped `src/nnue_weights.inc` is preserved.

The verified contract is768→128 per perspective, STM perspective first,
SCReLU, and a256→1 output. A residual logit adds
`trunc(clamp(logit*400/2.25, -30000, 30000))` centipawns to the actual HCE;
the combined score is then bounded by Forge's non-mate score range.

## Environment and native probe

Use Python3.10–3.12 with NumPy1.26.4, python-chess1.999/chess1.11.2 and
PyTorch2.4.1. CPU training is the verified residual path. The older standalone
DirectML entry point remains available; residual DirectML hardware execution
has not been verified.

```sh
python -m pip install numpy==1.26.4 python-chess==1.999 psutil==7.2.2
python -m pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_BUILD_NNUE_TOOLS=ON
cmake --build build -j 4
python -B tools/nnue/tests/test_engine_parity.py --probe build/forge_nnue_probe --out NEW_PARITY_DIRECTORY --positions 2048
```

Keep strict floating-point flags when reproducing the recorded builds. Probe
input is one FEN per line; output is one JSON record per line. `--hce-only`
omits network inference for dataset preparation. The parity test uses the
actual C++ core, both sides, legal walks and special moves; its declared bound
is one centipawn after integer conversion. It is not a playing-strength test.

## Data contract

Legacy text is `FEN | scoreSTMcp | resultWhite`. It has no authenticated game
identity or best move. Do not use a position-hash split to claim game-held-out
validation, or convert the score to White POV without an explicit adapter.

The finite generator records completed games with game ID, ply, actual best
move, result and engine identity. Dataset preparation splits those games
deterministically and excludes every validation position key from all
training. Legacy text may be added to training only. Without its best move,
the conservative legacy filter excludes any position with a legal capture,
promotion or checking move; this is stricter than a best-move filter.

```sh
python -B tools/nnue/generate_residual_data.py --engine FROZEN_ENGINE --network src/nnue_weights.inc --source-commit BASELINE_SHA --out NEW_GAMES_DIRECTORY --games 256 --workers 2 --nodes 5000 --seed 20261023
python -B tools/nnue/prepare_residual_data.py --games-jsonl NEW_GAMES_DIRECTORY/games.jsonl --legacy 'LEGACY_DIRECTORY/*.txt' --probe build/forge_nnue_probe --out NEW_PREPARED_DIRECTORY --max-train 1000000 --score-cap 1000 --seed 20261023
```

Preparation requires the generator's completed manifest and original JSONL.
It uses a seeded reservoir across all legacy inputs rather than only the first
file. Source hashes, game identities, validation exclusion and ordered row
recipes remain available for replay. Derived native JSON streams are hashed
and discarded on success; failed probe output is retained.

Prepared `train.npz` and `validation.npz` contain `features` int16[N,2,32]
with-1 padding, `hce` and `score` int32[N] in STM centipawns, and `result_stm`
float32[N]. `manifest.json` binds bytes, counts, filters, sources and disjoint
held-out game identities. Original files are retained and rehashed.

## Train and hand off

```sh
python -B tools/nnue/residual_train.py --data-dir PREPARED_DATA --run-dir NEW_RUN_DIRECTORY --epochs 20 --batch-size 1024 --threads 4 --lr .001 --min-lr .00001 --result-start 0 --result-end .1 --seed 20261023
```

Use `--baseline-only --initial-net src/nnue_weights.inc` with a separate run
directory to measure the shipped network on the same validation set. The
trainer keeps the initial checkpoint and every epoch, reports HCE and combined
loss, and selects using the entire held-out pure-teacher metric. A result-weight
ramp never changes that selection metric. All output directories must be new.

Each export has `.inc`, old-loader-compatible float32 `.bin`, and metadata;
training checkpoints additionally retain optimizer/RNG state. Candidate nets
are separate artifacts. Run actual C++ parity against an exported candidate
before integration. Lower held-out loss does not establish Elo: the user's QA
crew owns the subsequent1000-game gate against the unchanged6.4.24 baseline.

The original attachment and its checksums are preserved under
`validation/nnue-pipeline-20261023/original-inputs/`. The supplied `README.txt`
documents that historical standalone bundle; this file describes the current
residual workflow.
