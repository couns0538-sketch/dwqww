# opus-r3-stack: every feature option (reference for the owner and the gate crew)

All defaults are OFF: with no option set and no build switch the engine searches exactly like the AL1 s198 lock
(bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690).
"ON pins" are bench node counts (Threads 1, Hash 16) measured on the stack; "= branch" means they equal the
numbers recorded by the feature's own job or measured on its own branch exe (`logs/` of this folder).
Node-exact features change speed only (ON pins = lock pins). Gate entries: `opus_r3/R3-3/GATE_PROPOSALS.md`.

## Runtime UCI options (default build)

| option | type / default / range | job | what it does | ON pins on the stack (d11/d13/d16[/d20]) |
|---|---|---|---|---|
| SmpExactNodes | check, false | O1 | fresh helper node counts for node-limited SMP searches; exact total after the helpers stop | SMP only (Threads>1) |
| SmpBestThread | check, false | O1 | report the deepest worker's move/PV (mate scores never overridden) | SMP only |
| LocklessTT | check, false | O1-LTT | TT without striped locks (two atomic words per entry, tag mixed with data) | Threads 1: lock pins (= branch) |
| SyzygyPath (+ SyzygyProbeDepth 1-10, Syzygy50MoveRule) | string, empty | C1 | own Syzygy WDL/DTZ prober | 3-4-5 tables: 313631/866959/2460490 (= branch) |
| CorrHistPlus | spin 0-7 (bits 1/2/4) | C2 | continuation / minor-piece / non-pawn correction keys | 1: 318363/915778/2347193; 2: 296553/824640/2914749; 4: 340927/734347/2794671; 7: 317529/866764/2715911 (= branch) |
| HardDeadline | spin 0-1000 ms | C3 | watchdog sends bestmove at the hard limit + N ms if the search has not answered (R3 fix: no search output after it) | clocked searches only; bench unchanged |
| NNUEFile + NNUEKingBuckets 0-32 | string + spin | C4 | v2 net with king-bucketed input layer | replicas: lock pins; fail-loud rule for unusable requests |
| NNUEOutputBuckets | spin 0-16 | C5 | output head chosen by piece count | smoke ob8: 347579/1100105/2902266/14958675; kb4+ob8: 544057/1266127/3882123/17316510 (= branch) |
| PureNnue | spin 0-1 | O4 | stand-alone net, no hand-crafted evaluation | material smoke net: 450072/1280779/5669969/27276967 (= branch) |
| NNUEThreats | spin 0-1 | O6 | threat inputs (attacker/victim pairs) | threat smoke net: 343217/1069707/3461769/10485984 (= branch) |
| NNUEPawnPairs | spin 0-1 | O7 | pawn-pair inputs | pawn-pair smoke net: 325381/803697/3053216/13860219 (= branch) |
| CorrMargins | spin 0-1 | O5 | correction-size pruning margins (own search instance) | 343365/858019/2522546/12894582 (= branch) |
| CorrExt | spin 0-1 | O8 | correction-history extensions with a per-path budget (own search instance) | 312961/838790/2891507/12313394 (= branch) |
| CuckooRep | check, false | C6 | upcoming-repetition draw bound (own search instance) | 324211/790682/3148570 (= branch) |
| MaterialKeyTable | check, false | S11 | material key from a contribution table | node-exact (lock pins) |
| NetScale | spin 50-150, default 100 | S41 | scales the compiled-in network's evaluation | 90: 314443/981369/2815907; 110: 268059/999732/3035562 (= branch); 99: 308948 at d11 |
| HistRework | spin 0-3 | A1 | threat-keyed history twin + joint correction | 1: 373261/1043893/3399770; 2: 320427/881902/3041041; 3: 336192/869621/3052885 (= branch) |
| IntendedThreefold | check, false | S-IT | FIDE 9.2.1 claim as a draw floor (GitHub issue #7) | bench unchanged (no claimable history in bench) |

Combinations of CorrMargins / CorrExt / CuckooRep run combined search instances (8 in all); e.g. all three:
d11 353437, d13 944233. A v2 net bypasses NetScale, NnueLazyAcc and NnueInt16 (they act on the compiled-in net).

## Build switches (default off; PC recipe `-D<NAME>=1`, CMake `-D<NAME>=ON`)

| switch | job | effect | check on the stack |
|---|---|---|---|
| FORGE_NNUE_O2 | O2 | SSE2/AVX2 accumulator kernels, 64-byte alignment (bit-identical) | off: exe byte-identical to pre-O2; on: byte-identical to O2's merged code; lock pins |
| FORGE_NOZERO_MOVE_BUFFERS | S14 | no zero-fill of move buffers | node-exact (lock pins) |
| FORGE_S13_TT_CHILD_PREFETCH + UCI TtChildPrefetch | S13 | prefetch the child's TT bucket at null move / ProbCut | node-exact |
| FORGE_SPEEDSTACK | S29 | S11 table + S13 prefetch, always on | node-exact to d22 |
| FORGE_NNUE_LAZY_ACC + UCI NnueLazyAcc | S12 | null-edge accumulator alias | node-exact to d20 (also with O2) |
| FORGE_PROF (+ src/profile.cpp) + UCI Profile, command bench_prof | S08fix | search profile counters (diagnostic) | node-exact to d22 |
| FORGE_NNUE_INT16 + UCI NnueInt16 | S-A2 | integer inference (int16 weights, int32 accumulators) | ON: 330610/858175/2760596/9564588 (= branch) |
| FORGE_DATAGEN (+ src/datagen.cpp) | S32 | `forge datagen` self-play data mode | no search change; S32 output reproduced byte for byte (port_b) |
| FORGE_ATTACKS_INIT_ONCE | S04fix | synchronised first attack-table init | no search change; 1000/1000 cold-start probe (port_b) |
| FORGE_NNUE_WEIGHTS + FORGE_NNUE_HIDDEN=512 | S-A4 | another net include (e.g. H512) | H512 checks pass (port_c); no trained H512 net exists |

Every switch at once: 0 warnings, FMA 0, uci_check --full ALL OK, CMake CTest PASS (known lines only); CI workflow
`opus-r3-switches` runs release/ASan/TSan in that configuration. Tool target: S37 `forge_nnue_microbench`.
