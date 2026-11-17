# Reproducing this audit

## 1. Build

The workspace `/usr/bin/c++` is clang 18 with a broken header path. Use g++ 13 explicitly:

```bash
cd forge-combo29
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 \
  cmake -S . -B /tmp/build-base -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_BUILD_TYPE=Release
LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13 cmake --build /tmp/build-base -j4
```

Host needs AVX-512F + BMI2 for the CMake default (`-march=x86-64-v4`, PEXT + NNUE ZMM). On a
host without them add `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` — the pins still hold, but
the node counts in this report were measured on the non-portable build.

## 2. Pins (do this FIRST — a build is an input)

```bash
printf 'bench 11\nbench 13\nbench 16\nquit\n' | /tmp/build-base/forge | grep 'bench depth'
printf 'position startpos\ngo perft 5\nquit\n' | /tmp/build-base/forge | tail -1
```

Must print `312866`, `862329`, `3024920`, `nodes 4865609`. If they do not match, nothing else
in this audit applies to your binary.

## 3. Run

```bash
pip install chess

cd forge-combo29/swarm/consumer

python3 selftest.py                                   # 31 checks, must be all-pass
python3 probe.py /tmp/build-base/forge evidence/wire-base.json
python3 analyse.py evidence/wire-base.json evidence/controls-base.json
python3 depth_ladder.py /tmp/build-base/forge
python3 null_token.py /tmp/build-base/forge
python3 reader_trap21.py /tmp/build-base/forge
python3 unbounded.py /tmp/build-base/forge 60          # ~6 min

# the two match arms (~14 and ~18 min at 50 ms/move)
python3 games.py /tmp/build-base/forge --games 100 --movetime 50 \
        --out evidence/games-100-strict.json
python3 games.py /tmp/build-base/forge --games 100 --movetime 50 --allow-bail-play \
        --out evidence/games-100-naive.json

python3 verify_failures.py evidence/games-100-strict.json
python3 game_report.py evidence/games-100-strict.json evidence/games-100-naive.json
python3 bail_cost.py /tmp/build-base/forge \
        evidence/games-100-strict.json evidence/games-100-naive.json
python3 check_numbers.py                              # 37 numbers vs the evidence
```

`evidence/games-100-*.json` are stored gzipped; every reader goes through `evio.load_json`,
which tries the plain name then the `.gz`.

## 4. What to check if you only read one thing

`python3 check_numbers.py` recomputes every figure `FINDINGS.md` asserts from the JSON
evidence and prints how many checks it ran. `python3 selftest.py` proves the audit's own
checkers can fail — it caught a real gap in this seat's client (the depth-inflation check
never ran on the path where inflation happens).

## 5. Order of operations that matters

`ASSUMPTIONS.md` was written **before** `probe.py` was first run. If you re-run the audit,
write your own assumption list first and timestamp it; a verdict added after seeing the output
is a different kind of evidence from a prediction that held.
