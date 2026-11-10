# PROFILE: where combo29 spends its time (net on, one thread)

Measured 2026-11-10 16:02 to 16:07 Vienna on `c29ctl`, my rebuild of the lock source with the lock recipe (13 of 13 pins equal the lock's; MD5 `eaf05dca39eb20a794b873dc54849d45`).

## Method

**Instruction-pointer sampling** with my own tool `tools/rip_sampler.py`: the engine runs `bench 22` (net on, single thread, bench's own 16 MB table) as a child pinned to CPU 12; the sampler, on CPU 2, reads the engine thread's instruction pointer each time the thread's own cycle counter has advanced by at least 1.5 million cycles. Addresses are resolved with the installed `llvm-symbolizer --inlines` against the build's PDB. A `bench 11` runs before sampling as warm-up. Every sample goes to exactly one category by the rule fixed in `PREREG.md` (the innermost frame that names a listed function or was written in an engine `.cpp` file decides; helpers inlined from headers are charged to their caller). The shares therefore add to 100 %.

**Exact call counts** come from the build's own profile data (`llvm-profdata show`), over the recipe's training run (`bench 11 + 13 + 16`, 4,200,115 nodes).

Two measurements were taken. In the first, six of my own determinism engines were running on CPUs 1, 3, 4, 5, 6 and 14 (CPU 13, the sibling of CPU 12, was idle in both). In the second nothing else of mine was running. The second is the one to read; the first shows what shared cache load does.

## Result (share of samples, %)

| Category | Quiet, run 1 | Quiet, run 2 | **Quiet, both** | With my six other engines running |
|---|---|---|---|---|
| Hand-crafted evaluation | 21.12 | 20.65 | **20.88** | 19.92 |
| Make/unmake and legality | 18.03 | 17.84 | **17.94** | 17.73 |
| Move ordering | 16.81 | 16.45 | **16.63** | 17.32 |
| Search own code | 15.33 | 15.77 | **15.55** | 14.82 |
| NNUE accumulator update | 8.10 | 8.53 | **8.31** | 8.11 |
| Move generation | 7.30 | 7.38 | **7.34** | 6.80 |
| Transposition table | 7.02 | 7.53 | **7.27** | 9.32 |
| NNUE output layer | 5.58 | 5.20 | **5.39** | 5.28 |
| Other (system libraries, unresolved) | 0.72 | 0.64 | **0.68** | 0.70 |
| NNUE accumulator refresh | 0.00 | 0.00 | **0.00** | 0.00 |
| Sum | 100.01 | 99.99 | 99.99 | 100.00 |
| Samples | 10,133 | 10,132 | 20,265 | 21,545 |
| Engine speed during the run | 3.13 M nps | 3.12 M nps | | 2.95 M nps |

Sums differ from 100 by rounding only. Unresolved samples inside the engine image: 0 in every run. All four runs were valid (34,048,354 nodes, exit 0).

The network costs 13.7 % in all (update 8.3 %, output layer 5.4 %); the table 7.3 %. The largest single category is the hand-crafted evaluation, which the network corrects but does not replace.

## Exact counts per node (4,200,115 nodes)

| Function | Calls | Per node |
|---|---|---|
| `Worker::record_move` (a move is about to be made) | 4,006,631 | 0.95 |
| `nnue::update` | 3,100,891 | 0.74 |
| `nnue::evaluate` = `Worker::static_evaluate` | 2,530,181 | 0.60 |
| `nnue::refresh` | 24 | 0.00 |
| `TranspositionTable::probe_owned` | 4,195,674 | 1.00 |
| `TranspositionTable::prefetch` | 4,092,820 | 0.97 |

77 % of all recorded moves later have their accumulator computed.

## Hot lines (with my six other engines running; quiet tables are in the log)

| Line | Share | What it is |
|---|---|---|
| `search.cpp:289` | 5.75 % | first load of the table cluster in `probe_body` (memory latency; the prefetch is already issued before `make_move`) |
| `nnue.cpp:127` | 2.60 % | the fused update loop for quiet moves |
| `nnue.cpp:150` | 1.98 % | the fused update loop for captures |
| `nnue.cpp:194`, `:196` | 2.82 % | output layer: clamp, square, multiply by the output weights |
| `nnue.cpp:246` | 1.06 % | output layer: the ordered sum of the 16 partial sums |
| `search.cpp:839` | 1.23 % | `record_move` stores the piece changes (the stall job 2 reported; closed as `DIRTY_INPLACE`) |

## Machine code of the update loops

`out\prof\nnue_lock_codegen.s` (the lock's flags and profile data, `nnue.cpp` alone): each update loop is 16 straight-line groups of `vmovaps` load, `vsubps`, `vaddps`, `vmovaps` store on 512-bit registers per side, with no overlap checks and no narrower fallback. Hand-written AVX-512 would emit the same instructions, so that candidate was dropped before any code.

## Sizing of the open candidates

Rough figures: about 1,700 CPU cycles per node in the quiet run (assuming 5.4 GHz).

| Target | Measured | What a patch could remove | Expectation |
|---|---|---|---|
| Waiting for weight columns in `nnue::update` | `update` itself is 5.3 % of samples, about 125 cycles per call; the same 32 register groups would take about 40 cycles with every operand in the first-level cache | most of the difference, if the columns are fetched while `make_move` and the table probe run; the cost is extra prefetch instructions on all 0.95 recorded moves per node, of which 23 % are never used | at best about +2 %, more likely +0.5 to +1.5 % |
| Output layer after an update | 5.4 %, about 155 cycles per call; two serial chains of 16 additions each, whose order is fixed by bit-exactness, need about 110 cycles by themselves | only the reload of the freshly stored accumulator | under +0.5 % |
| Table probe | 7.3 % quiet, 9.3 % under shared-cache load | nothing new: alignment, early prefetch and large pages are in the lock or closed | no candidate |
| Refresh | 0.00 % | - | no candidate |

Expectations are estimates from sample shares and are UNPROVEN until timed.

## Verdict

C3 DONE. Top category: hand-crafted evaluation, 20.9 %. Within the network and table paths, the only target that could plausibly reach +2 % is the wait for weight columns in the accumulator update; it is the first candidate of C4.

## Evidence

`evidence/logs/profile_bench22_neton_quiet.log` (the quiet runs), `evidence/logs/profile_bench22_neton.log` (with my other engines running), `evidence/logs/profile_call_counts.log`. Raw address histograms stay on the PC under `out\prof_quiet\` and `out\prof\`.
