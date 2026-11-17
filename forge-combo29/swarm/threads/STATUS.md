# STATUS — swarm/threads

## 2026-11-17 (seat start)

**Area**: `Threads` above one — entirely unexplored in this audit before this seat.
**Base**: `6b98f217`. **Branch**: `swarm/threads`. **Folder**: `forge-combo29/swarm/threads/`.

**Machine**: 4 cores, Intel Xeon (KVM), 1 thread/core, no SMT, 15 GB. **Threads 8 is
2.0x oversubscribed** and every Threads 8 row says so.

### Done

| part | what | evidence |
|---|---|---|
| build | g++ 13.3, `-DCMAKE_CXX_COMPILER=/usr/bin/g++`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`; sha256 `e06310ec…` | `evidence/pin_summary.json` |
| **gate** | 4/4 honesty pins exact at Threads 1 (312,866 / 862,329 / 3,024,920 / 4,865,609) | `evidence/pin_*.raw.txt` |
| gate scope | pins re-run at T1/2/4/8 — identical, **because bench ignores Threads** (`Searcher(16)`) | `evidence/pins_by_threads.json` |
| controls | Threads reaches the engine; MultiPV>1 disables helpers; bench is thread-blind | `evidence/controls.json` |
| determinism | 40 positions x 3 repeats x 4 thread counts x 2 limits = 960 searches | `evidence/det_depth12.jsonl`, `det_nodes100k.jsonl` |
| magnitude | score spread / node ratio per thread count, Threads 1 as the 0-cp control | `evidence/score_spread.txt` |
| drawn root | bail fires 40/40 identical, 4 fixtures + 3 controls, all thread counts | `evidence/drawn_root.json` |
| book/clock | booked 9/15 at every count; movetime 290.7–293.2 ms; withdrawn RNG finding | `evidence/book_clock.json` |
| wall time | depth 16 and movetime 1000 arms; `wall = inflate / rate` closes to 1e-16 | `evidence/walltime_d16.json`, `fixed_depth_cost.txt` |
| depth reached | paired per position, exact sign tests | `evidence/depth_reached.json`, `depth_sign_tests.txt` |
| node budget | no per-worker overshoot; 1 row over by 1 node of 480 | `evidence/node_budget.json` |
| **zero-info** | `go nodes 1000` at T2 returns an **unsearched first candidate 45/60** | `evidence/zero_info.json`, `first_candidate.json` |
| TSan | probe fires (1), plant fires (25,960), clean build **0** at T4/T8 | `evidence/tsan_*.json` |
| thread switch | 200 switches, 0 illegal, 0 zero-info | `evidence/thread_switch.json` |
| move quality | 13 flips measured, **conclusion declined** (7/13 sign-flip at depth+4) | `evidence/move_quality.json`, `pinned_noise.json` |
| citations | all 14 `file:line` citations resolve and carry the claimed token | `scripts/check_citations.py` PASS |

### Headline results

1. **The inherited claim is confirmed.** Threads 1: **0/40** differ (nodes, score, move)
   over 120 searches. Threads > 1: **40/40** differ in nodes, 37–39/40 in score, 13–22/40
   in bestmove. Median score swing 24–38 cp, max 2,109 cp.
2. **`bench` and `perft` ignore `Threads`.** `bench` builds `Searcher(16)` whose thread
   argument defaults to 1. The four pins are a Threads-1 gate and certify nothing about
   threading.
3. **Threading is a fixed-depth pessimisation**: T4 = 1.24x wall time, T8 = 2.00x, to
   reach the same depth, because node inflation (3.68x) outruns the rate gain (2.96x).
4. **The one resolved gain**: T4 reaches **+1.4 ply** in a fixed second (24 deeper / 7
   shallower, sign test p = 0.0033). T2 and T8 are **not resolved** (p = 1.000, p = 0.736).
5. **`go nodes ≲50k` at Threads ≥2 can return an unsearched first-legal move with zero
   `info depth` lines** — 45/60 at T2/N=1000, 0/60 at Threads 1. This gives the audit's
   only piped-harness detector a false-positive class.
6. **The drawn-root bail is completely thread-invariant** (40/40 identical).
7. **No data race found** under TSan, with a probe and a planted-fault proof.

### Withdrawn

- "Book moves differ across thread counts" — caused by `book_rng` seeded from the clock
  plus `Book Variety 30`; reproduces at Threads 1 (3/5). Not a thread effect.
- "Threaded moves are worse moves" — measured (13 flips) and **declined**: 7 of 13 gaps
  change sign at depth+4, so they are horizon artefacts, not a quality ordering.
- Two faults in my own instruments, both fixed and reported in FINDINGS §8: a bench
  control that required bit-equal wall time, and a TSan runner that never passed
  `TSAN_OPTIONS` (so its "0 on the planted build" counted nothing).

### Not done

- No SPRT / Elo. No ponder, `go infinite`+`stop`, or mid-search `setoption` race test —
  TSan coverage is depth-limited searches only.
- No Threads 16+ (4 cores). No `Threads` x `Hash` interaction (Hash 64 throughout).
- Mechanism of the node inflation **not** established.

### Next command I would run

```
python3 scripts/tsan_run.py /home/ubuntu/work/tsan/forge <fens> 4 evidence/tsan_go_infinite.json 0
```

after adding a `stop`-after-delay arm to `tsan_run.py` — the untested race surface named
in FINDINGS §6.
