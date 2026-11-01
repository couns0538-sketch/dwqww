# Lock profile — recorded before engine changes

Lock SHA256: FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072.
Source: unmodified AL1 s198 snapshot; manifest evidence/lock-source.sha256.
Host: AMD Ryzen 7 9850X3D, Windows, logical CPU 2, Idle, Threads=1, Hash=16.

120.009 seconds, 24,112 instruction-pointer samples, zero sampling errors,
19 completed d20 benches, all 12,389,307 nodes. Raw evidence: profile02/profile.json,
symbols.txt, bench.log. Addresses normalized from runtime image base to PE preferred base.

## Hotspots

Percentages below estimate **sampled wall time**, not hardware-cycle time.
Own-process main-thread suspend/GetThreadContext sampling is intrusive; these timings
are NOT speed evidence. Random 2–6 ms requested intervals reduce periodic aliasing.
No other process/thread was suspended. Main thread executes synchronous bench.
Function percentages are self-IP attribution, not inclusive stack measurements.

| Region | Samples | % of all samples |
|---|---:|---:|
| Worker::static_evaluate (includes inlined NNUE and bookkeeping) | 3035 | 12.587 |
| NNUE output arithmetic, 0x1400f30cf–0x1400f3281 exclusive | 1056 | 4.380 |
| NNUE quiet SIMD update block, 0x1400f2cbe–0x1400f2eba exclusive | 723 | 2.999 |
| nnue::refresh function | 0 | 0.000 observed |
| Residual HCE evaluate_position | 3777 | 15.664 |
| Worker::search | 4940 | 20.488 |
| Unresolved or external IP | 1289 | 5.346 |

NNUE subregions overlap the static_evaluate total; do not sum those rows.
Other NNUE update/control paths remain grouped within static_evaluate, not falsely
assigned to output. The quiet update block already uses zmm float instructions.
Output is two ymm groups retaining 16 ordered lanes. Source and disassembly agree.
Unknown/external samples and scheduling pauses limit precision. Inclusive percentages
are unavailable with this sampler. This profile selects a hypothesis, not a gain.

## Decisions, in requested order

1. Refresh cache: skip. No samples in refresh; code refreshes roots and otherwise
   replays incremental updates. No evidence of a >=1% refresh-cache opportunity here.
2. Integer/VNNI: defer. Inputs have 1/4096 resolution and SCReLU squares; byte
   quantization loses information. Float products and lane sums round at prescribed
   points. A dpbusd replacement has no established exact-equivalence proof.
3. Test AVX-512 float output processing: one 16-lane vector replaces two 8-lane
   vectors without changing per-element operations or final lane reduction.
   Use unaligned loads (accumulators are only 32-byte aligned). Keep all original
   layout, refresh, update, net, search, and OFF arithmetic. Default-off UCI option
   NNUEWideOutput; non-AVX512 builds retain existing path.

## Failed setup attempt

profile01 queued too much stdin before sampling, blocking the sampler. Its bench log
is retained but is not profile evidence. Only that owned script and its child were
terminated. profile02 uses a bounded queue and completed successfully.
