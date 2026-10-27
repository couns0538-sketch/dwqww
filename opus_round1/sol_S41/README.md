# S41 — eval-scale check for a new lock net + `NetScale` (UCI, default 100 = OFF)

## What is here
| path | what |
|---|---|
| `tools/evalscale_20261027.py` | the study tool: `sample` (fixed position set), `dump` (per-net static evals via the harness), `analyze` (quantiles, robust slopes, NetScale proposal) |
| `tools/evalscale_dump.cpp` | harness: per position `hce net total` exactly as `Worker::static_evaluate` computes them for one compiled-in network |
| `tools/test_evalscale_20261027.py`, `tools/mutation_check_s41.py` | unit tests (synthetic data) and the planted-bug check of the tool |
| `tools/bench_ref.py` | UCI driver: options + bench at given depths vs given references (+ perft) |
| `EVALSCALE_20261027.md` | the study result (tables) |
| `forge_sol_S41_netscale_20261027.patch` | the engine change as one patch vs the AL1 tree (`git apply -p1` / `patch -p1`) |
| `run_s41_benches.sh`, `mutation_check_engine_s41.py` | bench evidence script; planted bugs for the engine change |
| `data/positions_10k_20261027.txt.gz` | the fixed 10,000-position set (sha256 in `FILES.txt`) |
| `logs/` | step logs |

Engine change (on this branch): `include/forge/net_scale.hpp`, `src/search.cpp` (one hook in `Worker::static_evaluate`),
`src/uci.cpp` (option), `tests/net_scale_tests.cpp` + `CMakeLists.txt` (ctest `forge_net_scale_tests`).

## NetScale
`option name NetScale type spin default 100 min 50 max 150`. With a network active, the search's static evaluation
(residual net: HCE + network; stand-alone net: network) becomes `trunc(eval * NetScale / 100)`, then the usual clamp.
100 = the AL1 search (bench-identical). The HCE-only path (`UseNNUE false`) is never scaled. Changing the value
clears the hash (the TT stores static evaluations). The `bench` command uses the current value.

## Re-run (PC; nice 19, one process at a time, numpy single-threaded)
```sh
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe   # read-only venv, run with -I -B
T=opus_round1/sol_S41/tools
# 1. fixed set: WAC300 + 9,700 positions at evenly spaced byte offsets of a closed self-play file (read-only seeks)
$PY -I -B $T/evalscale_20261027.py sample --wac <lock archive>/4_tests/suites/wac300.epd \
    --selfplay D:/grok-pc-data/selfplay_out/forge_selfplay_013.txt --n 9700 --out <scratch>/positions.txt
# 2. per-net static evals (builds the harness once per net, Idle priority)
$PY -I -B $T/evalscale_20261027.py dump --lock-tree <lock archive>/1_source/forge_AL1_s198_src --harness $T/evalscale_dump.cpp \
    --positions <scratch>/positions.txt --work <scratch>/dump --net h256_e12=<e12.inc> --net s198=<s198.inc> --net e48f006=<f006.inc> ...
# 3. statistics + NetScale proposal (reference = h256_e12, the scale the margins were tuned on)
$PY -I -B $T/evalscale_20261027.py analyze --ref h256_e12 --second-ref s198 --dump h256_e12=<scratch>/dump/h256_e12.dump ... \
    --out-json stats.json --out-md tables.md
# tests
$PY -I -B $T/test_evalscale_20261027.py && $PY -I -B $T/mutation_check_s41.py
```
Outputs must be new files; the tool refuses to write under `forge_push`, `selfplay_out`, `forge_nnue_train` or
`C:\Users\Administrator\grok-pc`. Inputs are only read.

## For a future lock net
Run steps 2-3 with the new net added; `analyze` prints the NetScale value that maps it back to h256_e12's scale
(`netscale_percent`), and the "sym after NetScale" column checks the mapping with the engine's integer arithmetic.
A NetScale gate is one option, OFF by default, its own srand (TEST_PLAN), only after that net is locked.
