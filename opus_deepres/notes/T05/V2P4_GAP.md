# Why v2p4 runs at 0.85-0.89x the lock's nps (T05; numbers from our own records, final at 23:16 PC clock)

Exe pair: lock exe FD3A5190 (kit v2.3, workload v1) vs the v2 gate exe v2p4 a2a560cb (kit v2.5 = v2.4
-PartialTraining + workload v2n; patch v2port 926ada2c with the root fix). All numbers below are OUR records (no web
source); every speed figure is advisory (one PC, two different exe files).

**Short answer.** For the trained nets (all KB4-KB32) the biggest measured share is the LAYOUT (bigger first-layer
table + king-bucket refreshes: P2 + P3 = 6 % for KB8, 11 % for KB32), not the build (P1 = 2 % on the v2 path, maybe
less after the per-file term is stripped). The 30-h report's "what remains is the kit v2.5 build" holds for its KB1
control only. About 3 % (Y8 and Z32 alike) is not measured (P4).

## The end-to-end numbers being explained
| net on v2p4 | layout | nps v2p4 / lock exe | 95 % CI | depth at 200 ms | file |
|---|---|---|---|---|---|
| Y8 (KB8 soup) | KB8 / OB8 | 0.8926 | 0.8842-0.9011 | -0.318 ply (SE 0.093) | D:/o30/wt/opus_30h/a/logs/checks_gpu_w2/speed_vs_lockexe_o30_gpu_soupY8r3r5r10r12r14r15.txt |
| Z32 (KB32 soup) | KB32 / OB8 | 0.8487 | 0.8405-0.8571 | -0.465 ply (SE 0.095) | .../speed_vs_lockexe_o30_gpu_soupZ32_r3r5r7r8r12.txt |
Method: depth_probe_ab.py, 200 game positions from the match PGNs, `go movetime 200` in one long-lived process, 2 rounds
(AB, BA), geometric-mean nps ratio. The trees are NOT identical here (different evaluations), so the CI covers position
noise only, not tree shape.

## Decomposition into named parts
| # | part | factor | measured? | evidence (our files) |
|---|---|---|---|---|
| P1 | exe build: kit v2.5 vs the lock's kit v2.3, v2 code path at the lock's table size (lock net as KB1 / OB8 - the net named in the D-a discriminator - on v2p4 vs lock exe, identical trees) | 0.980 | MEASURED, 1 probe run, run-to-run noise ~+-3 %; two exe files, so the BH-8 per-file / arm effect (up to ~3-5 % on this PC) may sit inside | a/RESULTS.md "New gate exe with the root fix" (v2p4 probe: OFF 0.933, KB1 0.980, KB4 replicas 0.929) |
| P1' | same build effect on the v1 (OFF) path of v2p4 | 0.933 (post-fix probe); 0.964 (CI 0.942-0.986, earlier probe of the same kit) | MEASURED twice, 3 % apart = the noise level | a/RESULTS.md "FOUND AND FIXED" and "New gate exe" |
| P2 | table size + KB4 king-bucket refreshes: lock net as KB4 replicas (3.1 MB float table, identical evaluation and tree) vs as KB1 (786 KB) | 0.948 (= 0.929 / 0.980, two probe runs); bench ABBA 0.968 (CI 0.900-1.040, median 0.991) | MEASURED twice, noisy; NOT split into "bytes" vs "refresh count" (no counter run for KB4 refreshes in game positions) | a/RESULTS.md lines ~217-219 (bench ABBA), v2p4 probe |
| P3 | finer layout vs KB4 (more refreshes on lateral king moves + 2x-8x the table) | KB8 0.988 (3 runs 0.9965 / 0.9830 / 0.9829); KB16 0.969; KB32 0.942 (3 runs 0.9413 / 0.9404 / 0.9442) | MEASURED (identity nets, same trees, one exe, 3-4 runs; single runs scatter +-1-2 %); again not split into bytes vs refreshes | FINAL_REPORT lines 287-289 |
| P4 | remainder: trained-net tree shape (different trees: different qsearch share, TT hits, evaluations per node), plus probe noise | Y8 0.972, Z32 0.970 | NOT MEASURED (computed as end-to-end / product) | - |
| - | v2 code itself vs v1 code in the SAME plain exe (after the root fix) | 1.028 (CI 1.001-1.056) | MEASURED: the v2 code is not slower than v1; the lazy-root bug (19 % of evaluations rebuilt from the cache, ~8 %) is fixed | a/RESULTS.md "FOUND AND FIXED" |
| - | output buckets OB1 -> OB8 (popcount + row offset) | inside P1 (both KB1 and KB4 probe nets are OB8) | NOT MEASURED separately (expected tiny: one popcount and one table read per evaluation) | - |

Product check: Y8 = P1 0.980 x P2 0.948 x P3(KB8) 0.988 = 0.918 -> measured 0.893 -> remainder P4 = 0.972.
Z32 = 0.980 x 0.948 x P3(KB32) 0.942 = 0.875 -> measured 0.849 -> remainder P4 = 0.970.
With the bench-ABBA value of P2 (0.968) instead: Y8 0.937 -> P4 0.952; Z32 0.894 -> P4 0.950.
So about 2 % (P1) + 5 % (P2) + 1 % / 6 % (P3) + 3-5 % unexplained (P4) - the measured parts explain about 60-80 % of
the gap (Y8: 8.2 of 10.7 points with the probe P2, 6.3 with the bench P2; Z32: 12.5 / 10.6 of 15.1); P4 has the same size and sign for both nets, which points at a common cause (tree shape of the
trained nets or a probe-to-probe offset), not at the layout.

## What would close each part (ranked in notes/T05/SPEED_LIST.md)
- P1 / P1' (build): the profile must cover the code the gate runs. (a) Make the v2 code the ONLY path: load the
  compiled-in net into the v2 structures (KB1 / OB1) at start-up - proven identical (lock net as v2 = lock pins
  d11-d22) - so the frozen v1 workload profiles the code that games run; no option-only cold path. (b) Otherwise QA's
  kit with a workload that runs the v2 path in the gate's proportions. (c) Before any fix: fresh-copies A/A (R5B
  --copies) for both exes so the per-file term (BH-8) is stripped from P1. (d) BOLT (post-link layout) is NOT available:
  "BOLT operates on X86-64 and AArch64 ELF binaries" (llvm-project bolt/README.md line 12 @ b5376302); our exes are PE.
- P2 (table bytes): int16 first-layer store (a/o30_v2int16.py, prepared, exact, never built): a KB4 table drops from
  3.1 MB to 1.5 MB, one perspective's bucket from 786 KB to 393 KB, so the two perspectives' hot buckets (786 KB) fit the
  1 MB L2 of a Zen 5 core again (Zen 5: L2 1 MB per core 16-way, L1 DTLB 96 entries, L2 DTLB 4K entries - AMD deck via
  search summaries, sources.md no. 7). Exact with float or int32 accumulators (every value is an integer multiple of 2^-12).
  Also: large (2 MB) pages for the v2 weights (a KB32 float table spans 6,144 4-KiB pages), and a software prefetch of
  the dirty-piece columns when the move is recorded (the lazy update reads them later).
- P3 (refreshes): the per-worker refresh cache is already in v2 (only the difference to the cached placement is
  applied); int16 halves its bytes too. Fewer seams: a map whose bucket borders are crossed less often by kings, or no
  KB16 / KB32 at all (they cost 3-6 % for no play gain the 30-h job could see).
- P4: measure before fixing - Y8 vs the lock net written as KB8 replicas on the SAME v2p4 exe (one exe, two nets,
  identical code) isolates the tree effect from the layout. A tree effect is not a speed bug.
- Split P2 / P3 into bytes vs refresh work before choosing between int16 (bytes) and map design (refreshes): run the
  30-h counters (a/o30_v2stats.py + a/stats_run_o30.py, test build, 100 game positions, depth 12, hash kept) with the
  lock net as KB4 / KB8 / KB32 replicas and count refresh_cached calls and columns applied per refresh; then T05-03's
  LargePages on / off probe tells the TLB share.
- P1' (the v1 path of v2p4 at 0.933-0.964) does not touch v2 gates, but it shows the kit v2.5 build moved shared code;
  any gate that runs v2p4 without a v2 net carries it.

## Status of this note
Final for this round. Measured parts: P1, P1', P2 (twice, noisy), P3. Not measured: P4, the OB8 cost alone, the
bytes / refresh split of P2-P3, the per-file share of P1. External facts used: Zen 5 L2 / TLB sizes and BOLT
(notes/T05/sources.md no. 5 and 7). Cards: T05-01 (P2 / P3 bytes), T05-02 (P1), T05-03 (P2 / P3 TLB), T05-04 (P2 latency).
