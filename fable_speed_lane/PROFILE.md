# PROFILE: where combo29 spends its time

Measured 2026-11-10 08:47 to 08:55 Vienna on the control rebuild `c29ctl` (every code and data byte equal to the lock exe). All runs on CPU 3 at Idle priority.

## Method

1. **Self time.** `tools/spd_rip_sampler.py`: the engine runs `bench 22` as a pinned child; its instruction pointer is read each time the thread's own cycle counter has advanced by 1.5 million cycles. Samples are therefore spread over the thread's CPU time, not over wall time. Addresses are symbolised with `llvm-symbolizer --inlines` against the build's PDB, so inlined code is charged to the function it was written in. Two runs per mode; 0 unresolved samples.
2. **Exact counts.** `tools/spd_counters.py` reads the frontend PGO counters of the instrumented stage (`bench 11/13/16`): 4,200,115 nodes with the net, 3,731,176 without. Counts are per source function and do not depend on inlining or load.

| Run | Samples | nps during the run |
|---|---|---|
| net on, a / b | 14,367 / 14,770 | 1.88 M / 1.74 M |
| net off, a / b | 10,779 / 10,072 | 1.42 M / 1.91 M |

**Limit of this profile.** The PC was loaded (gate engines on CPUs 4-11, trainer on 0-2). Memory-bound spots are inflated by cache and TLB pressure from the other processes; CPU-bound spots are not. I picked candidates from the CPU-bound spots only.

## Hotspots by emitted function (share of samples, run a / run b)

| Function as emitted | net on | net off |
|---|---|---|
| `Worker::search` (with inlined picker, make/unmake, NNUE update) | 33.5 / 33.9 | 27.3 / 27.2 |
| `evaluate_position<false>` (hand-crafted eval) | 19.6 / 19.4 | 27.0 / 27.8 |
| `Worker::qsearch` | 10.9 / 11.1 | 9.3 / 8.9 |
| `TranspositionTable::probe_owned` | 7.7 / 8.1 | 9.3 / 9.1 |
| `Board::generate_pseudo_legal` | 6.1 / 5.6 | 6.7 / 7.2 |
| `Board::see_ge` | 5.0 / 4.8 | 5.9 / 5.8 |
| `nnue::evaluate` | 4.4 / 4.4 | - |
| `std::__final_insertion_sort` + `__introsort_loop` (picker sort) | 4.7 / 4.5 | 5.8 / 5.5 |
| `Board::has_legal_move` (with the king-lines build inlined) | 2.9 / 2.6 | 2.9 / 2.9 |
| `MovePicker::generate_quiets` | 1.8 / 2.0 | 2.4 / 2.1 |
| `MovePicker::generate_evasions` | 1.1 / 1.2 | 1.1 / 1.2 |
| `Board::is_pseudo_legal` | 1.0 / 1.1 | 0.9 / 1.1 |

The two runs of each mode rank the same top eight.

## Hotspots by source function (net on, run a / run b)

| Source function | Share | Kind |
|---|---|---|
| `Worker::search` own code | 7.5 / 7.9 | mixed |
| `TranspositionTable::probe_body` | 6.0 / 6.3 | memory: 5.5 % sits on the first load of the cluster (`search.cpp:289`) |
| `nnue::update` | 5.7 / 5.9 | memory: weight columns (`nnue.cpp:127`, `:150`) |
| `evaluate_pieces` | 5.3 / 4.9 | CPU |
| `nnue::evaluate` | 4.0 / 4.1 | waits on the update's loads; 1.0 % is the ordered 16-term sum |
| `MovePicker::pick_best` | 3.9 / 3.9 | CPU (closed: PICKBEST) |
| `evaluate_king` | 3.2 / 3.4 | CPU, branchy |
| `Board::see_ge` | 2.5 / 2.5 | CPU |
| `Board::generate_pseudo_legal` | 2.4 / 2.2 | CPU |
| `Worker::corrected_eval` | 2.1 / 2.3 | memory (closed: C2 matkey, CorrHistPrefetch) |
| `Worker::record_move` | 1.3 / 1.1 | one store-forwarding stall, see follow-ups |

## Sizing of the candidates (net on / net off, share of all samples)

| Target | Measured cost | What a patch can remove | Expected gain |
|---|---|---|---|
| King shelter and storm loop plus king-pawn distance in `evaluate_king` (`eval.cpp:209-228`, `:271`) | 4.1 % / 4.8 %, counting the code inlined into those lines; the loop runs 7.4 M times per 2.53 M evaluations and its branches depend on data | everything on a cache hit; these terms depend only on the pawns and the king square | about +3 %, the largest target |
| `has_legal_move` at every non-check node | 2.9 % / 2.9 %; 3.80 M of the 3.92 M king-lines builds start from its one witness move, and 53 % of main-search nodes return at the TT cutoff right after | the build at nodes that never test another move | about +0.8 % |
| Slow legality test while in check (`is_legal` line 744 into `square_attacked_with_occupancy`) | 1.0 % / 0.8 % plus about 0.3 % of set-up; 2.54 M of the 3.96 M slow tests are non-king moves in check | those 2.54 M tests | about +0.6 % |
| Pawn-capture loop of the generator (`board.cpp:488-497`) | about 0.4 %; 9.73 M iterations for 0.68 M captures | iterations of pawns with nothing to capture | about +0.3 % |
| `attackers_to` in `make_move` (`board.cpp:1068`) | 0.26 % / 0.41 % (the rest of `attackers_to`, 1.1 %, belongs to `see_ge`) | most of it for ordinary moves | about +0.2 % |
| Queen rays recomputed for WeakQueen (`eval.cpp:190-192`) | 0.12 % on those lines | at most that | dropped: too small to measure |

Gains are estimates from sample shares. They are UNPROVEN until timed; QA's quiet ABBA decides.

## Follow-ups for owners (not acted on in this job)

- **`DIRTY_INPLACE` on clang.** The store-forwarding stall that Opus's H2 and the SDK's D4d removed is still in the clang build: a 32-byte reload of the `DirtyPieces` temporary right after narrow stores, 1.0 % of all samples on one instruction (`search.cpp:839`, address RVA `0x410d`). Both earlier timings of that patch were on g++ builds. Re-timing the existing patch on combo29 may be worth a slot.
- **TT prefetch under load.** 1.4 % of samples sit on the instruction after `prefetcht0` (`search.cpp:1384`). That is a page-walk cost of the loaded machine and should be far smaller in a quiet window.
- **CPU lane.** The live gate runs on CPUs 4-11 above Idle priority, so only CPU 3 of the Fable lane was usable (details in `STATUS.md`).

## Files

Raw data stays on D: under `D:\forge_jobs_20261109\fable2\out\prof\`: per run `rva_hist.tsv`, `rva_frames.tsv`, `self_by_source_function.tsv`, `self_by_emitted_function.tsv`, `self_by_line.tsv`, `stats.json`; `counters_net_on.tsv`, `counters_net_off.tsv`.
