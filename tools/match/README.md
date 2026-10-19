# Reproducible match support (not an Elo claim)

All Forge support scripts and newly generated positions are original MIT-licensed material.
Python 3.10+ is needed for the optional scripts. The engine itself remains dependency-free C++20.
Fastchess is a separate external MIT-licensed process. No GPL engine code or weights were copied.
See `fastchess-provenance.json` for the actually executed official CI binary and digest.

## Obtain the pinned external runner

On a machine with network access:

```sh
git clone https://github.com/Disservin/fastchess.git ../fastchess
cd ../fastchess
git checkout 60d7a7a26c6b0582a15c112fb29a1829bef2adb3
make -j2
./fastchess -version
```

This is a build recipe, not a claim that a local build produced the same CI executable.
Retain your compiler version, flags and binary hash. The native Fastchess `man.md` at that
commit is the authoritative option reference. Preserve its license when redistributing it.
Its bundled example books/tablebases are NOT our opening corpus and are not redistributed.

## Rebuild baseline and candidate identically

Use untouched source directories, one Release build per source, the same GCC/Clang version
and flags, no PGO, no parallel search. The source supplied by hash `cbb96c...` is v5.7.0;
use that as the one-change causal baseline. The exact v5.6.0 archive is a separate historical
comparison and includes three additional inherited differences, documented in the report.

```sh
cmake -S ../baseline -B ../build-baseline -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror"
cmake --build ../build-baseline -j2
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror"
cmake --build build -j2
ctest --test-dir build --output-on-failure
```

## A/A calibration first

```sh
python3 tools/match/run_match.py --fastchess ../fastchess/fastchess \
  --baseline ../build-baseline/forge --candidate ../build-baseline/forge \
  --openings tools/openings/forge-10000.epd --out ../matches/aa \
  --pairs 8 --nodes 5000 --cpu 0 --aa
```

Identical binaries, fixed nodes, restart per game, color-swapped pairs. The runner validates
all pair colors/FENs, identical A/A move sequences and results, and independent pentanomial
counts against Fastchess. Its statistics deliberately contain no Elo estimate. An all-neutral
A/A pentanomial can make Fastchess print NaNs/zero variance; that is not a precise strength estimate.
Smoke mode has a 200-move draw cap; strength mode has no such adjudication.


### Completed fixed-node regression screen

A 100-pair/200-game run at 10,000 nodes per move against unchanged 5.7.0 completed with
W69 D65 L66, pentanomial `[3,21,50,22,4]`, and 200 normal terminations. It is useful as a
crash/regression and low-budget search screen, but fixed-node results are not Elo evidence and
are not pooled with the preregistered time-control SPRT.

## Preregistered strength gate (NOT completed for 5.8.0)

Before looking at strength data, freeze source/binary/compiler/book hashes and the following
settings. Use an otherwise idle host. Change none of them after seeing results.

```sh
python3 tools/match/run_match.py --fastchess ../fastchess/fastchess \
  --baseline ../build-baseline/forge --candidate build/forge \
  --openings tools/openings/forge-10000.epd --out ../matches/see-sprt \
  --mode sprt --pairs 10000 --tc 10+0.1 --cpu 0 --seed 20261003
```

Both engines use Hash=32 MiB, Move Overhead=10 ms, one search thread, the same core and
settings, one concurrent game, no pondering, and restart each game. Forge has no Threads
option; do not send an unsupported `Threads` setting. The runner deterministically
orders unique openings by SHA-256(seed + newline + EPD), then tells Fastchess to read them
sequentially; the fixed `-srand` seed is also retained. No repeated openings inside a run.

Pentanomial paired-game SPRT, logistic model, H0: delta=0 Elo, H1: delta=+5 Elo,
alpha=beta=0.05. The nominal likelihood boundaries are +/-ln(19) = +/-2.944438979.
Use Fastchess's explicit `H1 was accepted` / `H0 was accepted` completion message,
not a rounded displayed LLR or a positive point estimate. Stop at a boundary or at
10,000 complete pairs (20,000 games). Reaching the cap without a boundary is INCONCLUSIVE.
Accepting H1 is not a claim that the true gain is at least 5 Elo; 5 is the design alternative.

No score-based resignation/draw or tablebase adjudication is enabled. Normal rule-based
endings are handled by Fastchess. Any crash, illegal move, timeout, malformed/incomplete pair,
changed hash, or warning invalidates the run pending investigation. Do not count restarted
or discarded games selectively. Interrupted/incomplete runs preserve their logs but cannot
be reported as completed evidence. Automatic resume is deliberately not implemented: use a
new preregistered output directory or a separately reviewed native Fastchess recovery plan.

The completed 16-pair 3+0.03 pilots are infrastructure checks, not this strength gate, and
must not be pooled with a fresh 10+0.1 gate. Synthetic development openings are not a broad
chess population: replicate on a separate license-verified corpus and at a longer time
control before generalizing. CPU affinity does not make this shared VM dedicated hardware.

## Retained evidence

Each run refuses to overwrite an output directory and records exact arguments, executable
and opening hashes, selected EPDs, machine/affinity information, PGNs in UCI notation,
Fastchess's native state/logs and independently checked W/D/L + pentanomial counts.
`pgn_stats.py` can recheck the retained PGNs. `test_match_tools.py` tests all five bins,
incomplete pairs, color mistakes, duplicate openings, inconsistent results and abnormal endings.

The raw Fastchess output can include small-sample Elo estimates. They are diagnostic output,
not a Forge playing-strength claim. The final verdict is the preregistered test outcome.

## Opening reproduction / independent legality verification

The committed EPD and move sequences were generated BEFORE the engine change, using
unchanged v5.7.0, seed 20261003 and no evaluator screening. They are covered by the project
MIT license, with explicit provenance in `../openings/manifest.json`.

```sh
cmake -S . -B build -DFORGE_BUILD_VALIDATION_TOOLS=ON
cmake --build build -j2
build/forge_openings 10000 20261003 /tmp/recreated.epd /tmp/recreated.moves
cmp /tmp/recreated.epd tools/openings/forge-10000.epd
cmp /tmp/recreated.moves tools/openings/forge-10000.moves
# Optional independent validation, without copying the external header into Forge:
c++ -std=c++20 -O2 -isystem ../fastchess/app/third_party tools/verify_openings.cpp -o /tmp/verify-openings
/tmp/verify-openings tools/openings/forge-10000.moves
```
