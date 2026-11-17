# STATUS — `go mate N` surface audit

Seat: owner-audit (`swarm/gomat`). Base commit `6b98f217`.

## State: COMPLETE

All five assigned measurements are done, plus one defect found and characterised.
Every number in `FINDINGS.md` is read from a committed JSON file under
`evidence/`, produced by a committed script under `scripts/`.

## Build

| item | value |
|---|---|
| compiler | `/usr/bin/g++` (Ubuntu 13.3.0-6ubuntu2~24.04.1), as the build trap requires |
| env | `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13` |
| cmake | 3.28.3, `-DCMAKE_CXX_COMPILER=/usr/bin/g++`, Release, `-march=x86-64-v4` |
| engine | `id name Chess Engine Forge 6.4.24 candidate` |
| `build/forge` sha256 | `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` |

### Honesty pins — all four match (`evidence/pins.log`)

`312,866` / `862,329` / `3,024,920` / perft 5 `4,865,609`. Net-off bench also
matched (375,354 / 907,205 / 2,448,617).

## What was measured

| # | measurement | evidence file | status |
|---|---|---|---|
| 1 | finds mates at 1/2/3/4; no-mate behaviour | `corpus.json`, `raw_modes.json`, `surface.json` | done |
| 2 | `go mate 1` termination and bound; N=1..6 wall time | `termination_a.json` | done |
| 3 | disabled heuristics via 19-build ablation, singles + pairs | `BUILDS.txt`, `control_identity.json`, `ablation.json` | done |
| 4 | clock adherence, and what a clock does to the label | `termination.json`, `clock_label.json` | done |
| 5 | comparability table with the 163x cell in its distribution | `compare_real.json`, `compare_mate.json`, `compare_summary.txt` | done |
| + | mate-distance overclaim: found, classified, rate measured | `overclaim*.json` | done |

## Headline numbers

* 32/32 proven mates at 1-4 found; **80/80** distances correct at or under N.
* **36/36** no-mate requests terminated at exactly `2N-1`; `go mate 1` costs
  0.001-0.002 s. `go mate 6` costs **101-135 s** on a real middlegame.
* **1140/1600** real cells differ between `go mate N` and `go depth 2N-1`;
  median node ratio at N=4 is **188x**, so 163x is not an outlier on real
  positions (it IS one on the proven-DTM corpus: 166.9x vs median 1.19x).
* TT gates change **0/148** answers; Lmr+FutilityPrune change **55/148**.
* Clock: 3 of 7 clock forms changed the answer on a mate-in-4 board; 5 of 21
  clocked cells publish a score the clockless search does not give at the same
  reported depth.
* Defect: **6 M>N overclaims in 1200 requests**, of which **2 are wrong
  distances** with PVs that do not replay to mate.

## Two errors of my own, both caught and both recorded

1. A runner sent `ucinewgame` after `position`, so 37 positions all searched
   startpos. Caught by identical node counts, not by an assertion.
2. An ablation build wrote gate definitions to a text file only, leaving 13
   byte-identical binaries. Caught by sha256. The builder now hard-fails on a
   hash collision and `control_identity.py` re-proves control == base (64/64).

## Not done

* No `Threads > 1`. No middlegame ablation. No `stop` stress (2/2 smoke test
  only). No N > 6. No fix patch proposed.

## Next command if resumed

```
python3 swarm/gomat/scripts/run_overclaim_scan.py --exe build/forge \
  --out swarm/gomat/evidence/overclaim_scan_n5.json --positions 400 --seed 991
```
(a second seed at N=5,6, which is where class A is predicted to dominate)
