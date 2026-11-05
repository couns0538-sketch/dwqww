# T05 speed list: NNUE inference and memory speed on Zen 5 (ranked; every estimate UNPROVEN)

Scope: the lock's residual net (768 -> 256 float, SCReLU, one output; src/nnue.cpp) and the v2 path (FORGENN2,
king buckets, 8 output buckets; D:/o30/wt/opus_30h/a/v2port.patch). Neither has an L1 hidden layer, so int8 L1 /
VNNI / find-nnz / weight permutation apply only to the separate HalfKA path (EvalFileHalfKA, rows 9-10).
Speed gates: node-identical = nps ABBA only. The gap they target: notes/T05/V2P4_GAP.md (P1-P4).
Standard probe below = `depth_probe_ab.py`: 200 game positions from the match PGNs, `go movetime 200` in one
long-lived process, rounds AB + BA, geometric-mean nps ratio with CI (the method that found the lazy-root bug; the
bench clears the hash and hides game-only costs). Two different exe files: fresh copies per slot (R5B --copies) and an
identical-command A/A first (BH-8: up to ~3-5 % per-file / arm effect on this PC).

| # | item | expected nps | bit-exact | where in Forge (file:line) | idea source licence | microbenchmark plan |
|---|---|---|---|---|---|---|
| 1 | T05-01 int16 first-layer store, accumulators float or int32 in 2^-12 units | v2 KB4 / KB8 +1-4 %, KB16 / KB32 +2-5 %, lock 0 to +1.5 % | YES (all values k * 2^-12, lock-net bound 342,331 < 2^24) | lock src/nnue.cpp:47, :59 (float w1 from int16 / 4096), :84-157; v2 nnue_v2.hpp AlignedFloats w1, apply_columns, refresh_cached; script D:/o30/wt/opus_30h/a/o30_v2int16.py | own | (a) kernel: replay recorded dirty lists of 100 game positions (o30_v2stats-style dump) through float vs int16 tables for KB1 / KB4 / KB32 layouts, cycles per update (rdtsc), one core at Idle, tables cold-started per position; (b) engine: switch 0 vs 1 exes, standard probe with KB4 + KB8 nets + the lock net |
| 2 | T05-02 one hot eval path (compiled-in net evaluated by the v2 code; lock kit + workload profile it) | v2 gate exe +2-5 % (P1 0.980, OFF 0.933-0.964), lock 0 | YES (lock net as v2 = lock pins d11-d22) | lock src/search.cpp:599-621, :1367; v2 static_evaluate_v2 (noinline, section .text.forge_v2) | own; BOLT README Apache-2.0 WITH LLVM-exception | step 0: re-probe v2p4 vs lock with fresh copies + A/A to size P1 without the per-file term; step 1: one-path build with the lock's kit, standard probe vs the lock exe (KB1 = must be ~1.00) and vs v2p4 (KB8 net) |
| 3 | T05-03 2 MB pages for the v2 tables + refresh caches | KB4 +0-1 %, KB8 +0.5-1.5 %, KB16 / KB32 +1-3 % | YES (allocation only) | S1 allocator (qa_s1lp_20261031, option LargePages); v2port AlignedFloats / RefreshCache | Stockfish PRs 6359 / 7041, GPL-3.0 ideas only (PR text) | one exe, LargePages on vs off (no per-file effect), standard probe with KB8 and KB32 nets; also tells TLB vs refresh share of the KB32 layout cost (0.942) |
| 4 | T05-04 prefetch the dirty-piece w1 columns in record_move | KB4+ +0.5-2 %, lock ~0 | YES (hint only) | src/search.cpp:623-630 (record_move), :847 / :1126 (existing TT prefetch) | own (Stockfish 7025 title only) | one switch, standard probe KB4 / KB8; do after #1 (int16 halves the bytes it hides) |
| 5 | AVX-512 output kernel: one zmm per 16 hidden units, same lane j = h mod 16, separate mul / add (no FMA) | +0.3-1 % (about half of the kernel's ~450 vector uops per evaluation, counted from the source, not measured; ~1.2M evaluations/s derived from the probe nps 2.24M x 0.55 evaluations per node in the 30-h counters) -> DROPPED alone (< 1 %); free add-on to #1 | YES only with the same lane order and no contraction (kit check vfmadd 0) | src/nnue.cpp:171-185 (AVX2 kernel; the whole lock exe has 4 vaddps ymm, consistent with this loop body, and 48 vaddps / 64 vsubps zmm from the auto-vectorised updates) | own (the 16-lane design note at src/nnue.cpp:164-167) | parity 10000 FENs x SIMD paths, then standard probe |
| 6 | large pages for worker history tables (continuation 1.38 MB, correction 128 KB, butterfly, capture: ~1.55 MB) | < 1 % (Stockfish's +1.0-1.2 % nps was for 14 MB) -> DROPPED | YES | include/forge/search.hpp:252-260, src/search.cpp:566-568 | Stockfish PRs 6359 / 7041 (GPL, PR text) | only with S1 on: one exe, standard probe |
| 7 | TT prefetch earlier (R7PrefetchEarly: child key before make_move) | unknown, likely < 1 % -> re-judge by ABBA, not SPRT | YES | src/search.cpp:844-847, :1123-1126 (prefetch after make_move); R14 SPEED2 adds null move / ProbCut sites | own (R7; 1000-game SPRT +2.78 capped, no decision) | one switch, standard probe at Hash 64 and 256 |
| 8 | integer SCReLU output (int16 activations, multiply-add in integers) | output kernel only, ~ item 5 | NO (new quantisation of w2, evaluations change) | src/nnue.cpp:159-216 | no source read (general practice) | needs a new net format + Elo SPRT; not a speed-only change -> DROPPED here |
| 9 | int8 first layer / int16 accumulators | - | NO: int8 cannot hold weights up to 14,227 (15 bits); int16 accumulators fail the bound (342,331 > 32,767 on all 256 units) | src/nnue.cpp:59 | - | none (excluded by arithmetic) |
| 10 | HalfKA path only: find-nnz phase 1 with register-form VPCOMPRESSD then a plain store; VNNI dot products | unknown (R13 two-phase find-nnz was bit-identical but -12..-14 % LTO+PGO) | YES (R13 design was) | src/nnue_halfka.cpp (branch opus-r10-halfka, not the lock) | own R13; Zen 5 data uops.info / Agner | kernel microbench on the e19 net's FT outputs: store-form vs register-form compress, cycles per block_affine; only if a HalfKA net is gated |

## Already done or not applicable (no new item)
- AVX-512 accumulator updates: done by the compiler (-march=znver5; lock exe 48 vaddps zmm / 64 vsubps zmm, 0 vsubps ymm).
- Accumulator refresh cache: v2 has one per worker and (perspective, bucket, flip), applying only the placement
  difference; the lock has no king buckets. Lazy updates: lock and v2 walk back to the nearest valid ancestor; the v2
  root fix (2026-11-04) removed the 19 % cache rebuilds. Stockfish itself removed its double incremental update
  (PR 6776 title).
- 64 B alignment: FORGE_ALIGN_WEIGHTS (lock w1 at 48 mod 64 -> 0) measured neutral within ~3 % A/A; v2 tables are
  64-B aligned already. 2 MB: item 3.
- Weight permutation (FTP1), find-nnz sparse L1, AccumTile / SharedWeights: HalfKA path, done or lost (WORKER_RULES).
- TT locking: UCI go runs TTAccess::Exclusive (src/uci.cpp:357), so Threads=1 games take no stripe locks (R7TtExclusive
  is in the lock).

## Zen 5 instruction facts (asked by the brief; HalfKA path only)
| instruction | Zen 5 | Zen 4 | Intel (ICL / ADL-P / EMR) | source |
|---|---|---|---|---|
| VPDPBUSD zmm,zmm,zmm | latency 3, TP 0.50 c, 1 uop FP01 (uops.info); Agner: 1 op, latency 4, TP 0.5, P01 | latency 4, measured TP 1.00 | latency 5, TP 1.00 (ICL / ADL-P); EMR TP 0.50 | uops.info VPDPBUSD_ZMM_ZMM_ZMM; Agner instruction_tables.pdf 2025-09-20 |
| VPCOMPRESSD zmm{k},zmm (register) | latency 4 (mask 9), TP 1.00 c, 2 uops FP12; Agner: 2 ops, latency 5 | latency 5, TP 1.33 | latency 3, TP 2.00 | uops.info VPCOMPRESSD_ZMM_K_ZMM; Agner |
| VPCOMPRESSD m512{k},zmm (store) | 8 uops, TP 3.00 c (computed 1.00), latency <= 46 | 144 uops, TP 72.50 c | 4 uops, TP 2.00 | uops.info VPCOMPRESSD_M512_K_ZMM (Agner prints no store row) |
Reading: on Zen 5 the store form is no longer the Zen 4 trap (3 c vs 72.5 c), but the register form plus a plain store
is still cheaper; the int8 dot product runs 2 per cycle, so skipping zero blocks saves less than on Zen 4.

## Compiler (one line)
BOLT on MSYS2 / Windows: NO - "BOLT operates on X86-64 and AArch64 ELF binaries" (llvm-project bolt/README.md line 12
at b53763029964ff42b806ede881612fc391344327); Forge's exes are PE/COFF from MSYS2 g++, and the lock build is LTO+PGO.
