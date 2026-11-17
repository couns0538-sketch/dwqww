# S-F71 (v3) — the loaded net costs +11 % per node but 6.2x the nodes; and one of my own measurements was confounded

Seat 20. Build `build-v3/forge` sha256 `227aae56ef1678479cf08d0fc3e3c73683753e89d61f12b252f0fec9e388471e`
(`-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, kernel `avx512`). PC20, Threads 1, Hash 16.
Machine: **Intel Xeon, 4 cores** — *not* the owner's Zen 5, so AVX-512 here is a different microarchitecture with
different per-port throughput. `machine_clean` clean before every run; fresh process per run.

## The measurement

`bench 13` under PC20, 8 runs per arm:

| arm | nodes | median wall | spread | **ns per node** |
|---|---|---|---|---|
| built-in net | 587,276 | 314.5 ms | 312–316 | **535.5** |
| file-7 v3 net loaded | 3,652,372 | 2,172.5 ms | 2,133–2,331 | **594.8** |

**Per-node ratio 1.1107 (+11.1 %).** `bench 13` runs a fixed depth sequence, so both arms do the same *search work*
per depth step; the node count differs because the two nets give different values. Normalising by node count is
therefore the honest comparison, and the node counts themselves are exactly stable across all 8 runs (587,276 and
3,652,372 with no variation), so the ratio is not noise.

**What this means for the owner:** the loaded net is **~11 % dearer per node** on this Xeon, and it searches **6.2x as
many nodes** to reach the same nominal depth 13. Combined, `bench 13` takes **6.9x** the wall time (2,172 vs 314 ms).
The 6.2x is a *search-shape* difference (a differently-shaped eval produces different pruning), not a cost of the net
per se — but it is the number the owner would feel.

## A confounded measurement of mine, disclosed rather than dropped
My first attempt used `go nodes 2000000` on one position and reported v3 **9.0 % faster**. That number is **worthless**:
the two arms did not reach the node limit (1,509,063 and 1,249,906 nodes), so they ran different amounts of work, and
the wall-clock ratio mixed a real per-node difference with a large search-shape difference. The per-node figure above
is the corrective measurement. Recorded because a plausible-looking "-9.0 % faster" would have been the opposite
conclusion from the truth, and only the node counts exposed it.

## Method limits
1. **One workload** (`bench 13`), one position set, one machine. `bench`'s positions are not the 200 openings.
2. **This Xeon is not the PC.** File 7 requires timing on the PC itself before anything is believed; +11 % here says
   nothing definitive about Zen 5's AVX-512, which has wider effective throughput for this kernel shape.
3. Two builds of the same source came out **byte-identical** (`227aae56…` twice), so I cannot quote a build-to-build
   spread as 19-F7 does; the run-to-run spread (312–316 ms, 1.3 %) is the only variance I can show.
4. `-pg` is not involved here — these are normal `-O3` builds and wall-clock from the engine's own `time` field.

## Status
**NEW.** The reproducible claim: under PC20 at Threads 1, `bench 13` costs **535 ns/node with the built-in net and
595 ns/node with the file-7 v3 net (+11.1 %)**, while the v3 net walks **6.2x** the nodes.
