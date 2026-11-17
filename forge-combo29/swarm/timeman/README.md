# swarm/timeman — time-manager accounting

Audit base: `6b98f217` (divergent commit, not an ancestor of `main`).

| file | what it is |
|---|---|
| `FINDINGS.md` | the report |
| `STATUS.md` | what is done, withdrawn, or still open |
| `scripts/` | every harness and probe, each runnable on its own |
| `evidence/` | machine output behind every number in FINDINGS.md |

## Build

```bash
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++
cmake --build build -j4
bash scripts/check_pins.sh build/forge     # 312866 862329 3024920 4865609
```

Check the pins before trusting any number. The one time this was skipped in this seat, the pin
script passed against a **stale binary copied from the unpatched tree** — see FINDINGS.md §2.

## Run order

```bash
python3 scripts/p1_movestogo_base.py      build/forge OUT
python3 scripts/p2_movestogo_fallback.py  build/forge OUT base
python3 scripts/p3_games.py               build/forge OUT --games 50 --tc 1000,100
python3 scripts/p4_movetime.py            build/forge OUT/p4.json
python3 scripts/p7_floor_and_increment.py build/forge OUT/p7.json
python3 scripts/p8_analyse.py             OUT/p3_games.json OUT
python3 scripts/p11_floor_derivation.py   OUT/p11.json
```

`scripts/plan_table.cpp` compiles against `include/forge/clock_plan.hpp` and prints the exact plan
the engine computes, so the arithmetic in FINDINGS.md is the engine's own rather than a restatement
of it. `scripts/p5_flagcheck.py` and `scripts/p6_overrun.py` exist only to test the withdrawn
"forfeit" in FINDINGS.md §6.
