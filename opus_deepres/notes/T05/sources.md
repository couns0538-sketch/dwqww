# T05 sources (one line per source read: url or repo@sha | licence tier | what it gave | card id or "no card")

Track T05: NNUE inference and memory speed on Zen 5 (incl. compiler). Worker start 22:48 PC clock (2026-11-04);
research stop at 00:03 (75 min) at the latest.

Local read-only context (our own records, not counted as web sources): listed under "Local" at the end as read.

## Local (own code and records, read-only; not counted as web sources)
- L1. Lock source src/nnue.cpp (239 lines) + include/forge/nnue.hpp + the weights include header (768 -> 256, int16 w1 / 4096
  -> float32 w1 786 KB, float accumulators 2 x 1 KB, SCReLU, 16 ordered output lanes, AVX2 / SSE / scalar output kernels;
  lazy accumulator walk-back in src/search.cpp:599-621; record_move 623-630; TT prefetch after make_move at
  search.cpp:847 and :1126; UCI go uses TTAccess::Exclusive at uci.cpp:357, so Threads=1 games are lock-free) | own | T05-01..03
- L2. D:/o30/wt/opus_30h/a/v2port.patch (FORGENN2 v2 path: 64-B aligned float tables [KB][768][256], per-worker refresh
  cache with piece bitboards, apply_columns templates, noinline static_evaluate_v2 in section .text.forge_v2, root fix)
  | own | T05-01, T05-02, V2P4_GAP
- L3. D:/o30/FINAL_REPORT.md lines 15-99, 280-300, 476-515, 548-565, 660-760 (kit v2.3 0.71x / v2.4 0.959x / v2.5 ~1.0x;
  v2p4 OFF 0.933, KB1 0.980; layout KB8 0.988 / KB16 0.969 / KB32 0.942; end to end Y8 0.893x, Z32 0.849x; BH-8 per-file
  effect up to ~5 %; int16 first layer prepared, exact, not built) | own | V2P4_GAP, T05-01, T05-02
- L4. D:/o30/wt/opus_30h/a/RESULTS.md lines 82-123, 200-220, 400-475 (speed of the v2 path by kit; discriminators D-a /
  D-b; depth probe; counters: lazy root 777,451 evaluations without a valid ancestor, 1.55M cached refreshes; root fix ->
  plain v2 KB1 vs v1 same exe 1.028; v2p4 probe OFF 0.933, KB1 0.980, KB4 replicas 0.929) | own | V2P4_GAP
- L5. D:/o30/wt/opus_30h/a/logs/checks_gpu_w2/speed_vs_lockexe_*.txt (Y8 0.8926 CI 0.8842-0.9011, depth -0.318; Z32
  0.8487 CI 0.8405-0.8571, depth -0.465; 200 positions, movetime 200, 2 rounds) | own | V2P4_GAP
- L6. Skills forge-speed-stack (FORGE_ALIGN_WEIGHTS: lock w1 at 48 mod 64, align1 vs align0 neutral within ~3 % A/A;
  find-nnz on the HalfKA path bit-identical but -12..-14 % LTO+PGO; ___chkstk_ms on > 4 KiB stack arrays; lock prefetches
  child TT after make_move, R14 adds null move + ProbCut), forge-ltopgo-pgo (MSYS2 g++ 15.2.0, -flto=1 -fprofile-generate
  / -fprofile-use, -PartialTraining; v1 workload never runs net paths; per-file offsets ~3 %), forge-o30-v2net (kit
  0.71x / 0.959x; root refresh bug) | own | V2P4_GAP, SPEED_LIST
- L7. objdump -d of the lock exe forge_ltopgo_x_al1s198_v23.exe and of v2p4 forge_ltopgo_x_o30v2p4_a2a560cb.exe (static
  disassembly, no run): lock vaddps zmm 48 / ymm 4, vsubps zmm 64 / ymm 0, prefetch 2, vpdpbusd 0; v2p4 vaddps zmm 75 / ymm
  8, vsubps zmm 107 / ymm 0, prefetch 3 -> the accumulator loops are already auto-vectorised to 512-bit (znver5), the
  output kernel is the hand-written 256-bit AVX2 one | own | SPEED_LIST
- L8. notes/TRIED_GATES.md: R7-TTX (R7TtExclusive) non-regression H1 +3.84 (2534 g); R7-PFE (R7PrefetchEarly) 1000 g
  +2.78 capped, no decision (gated by SPRT although node-identical) | own | SPEED_LIST

- L9. C:/Users/Administrator/grok-pc/forge_push/qa_s1lp_20261031 (QA's S1 LargePages candidate, 2026-10-31): the patch
  puts the TT and the COMPILED-IN w1 on large pages behind UCI LargePages (default false); the v2 path's tables (later
  port) are not covered. QA's ABBA CSVs (B = LargePages on), geometric-mean nps B/A: t2 Hash 64 1.0114 / Hash 256
  1.0304 (20 + 20 runs each); t4 1.0109 / 1.0272; t4r 1.0155 / 1.0319; t3retest Hash 64 1.0127 (computed here from the
  CSVs, by 23:08) | own | T05-03

- L10. Lock weights include (src/nnue_weights.inc, arrays only; parsed read-only in this job): max |w1| 14,227 (3.47),
  max |b1| 6,764; per hidden unit |b1| + 32 largest |w1| up to 342,331 (83.6) - over 32,767 on all 256 units (also with
  one king per side and no pawns on ranks 1 / 8: 340,339), below 2^24 -> int16 accumulators not provable, float / int32
  exact; int8 weights impossible | own | T05-01, SPEED_LIST rows 1 and 9
- L11. Lock greps (tools/forge_has.sh): 'large_page|MEM_LARGE|madvise|huge' 0 hits; '_mm512|__AVX512' 0 hits;
  'exclusive|lease' 40 hits (TT ExclusiveLease, uci.cpp:357 go = Exclusive); history tables search.hpp:252-260 | own | cards

## Web sources
1. https://uops.info/html-instr/VPDPBUSD_ZMM_ZMM_ZMM.html (recorded 23:03) | measurement data site (facts only, no code) | VPDPBUSD zmm,zmm,zmm: Zen 5 latency 3 (all operand pairs), throughput 0.50 c (2 per cycle), 1 uop on FP01; Zen 4 latency 4, measured TP 1.00 (computed 0.50); Ice Lake / Tiger Lake / Alder Lake-P latency 5, TP 1.00 (p0); Cascade Lake / Emerald Rapids TP 0.50 (p05). Applies to the HalfKA int8 path only (the lock and v2 nets are float, no VNNI) | SPEED_LIST (HalfKA rows), no card
2. https://uops.info/html-instr/VPCOMPRESSD_M512_K_ZMM.html (recorded by 23:05) | measurement data site (facts only) | VPCOMPRESSD m512{k}, zmm (memory destination, the find-nnz store form): Zen 5 8 uops (2 FP03 + 2 FP12 + 1 FP45), measured TP 3.00 c (computed 1.00), latency <= 46 / <= 19 / <= 18; Zen 4 144 uops, measured TP 72.50 c; Intel ICL..EMR 4 uops, TP 2.00. So the Zen 4 trap (store form ~24x slower than Intel) is gone on Zen 5 (1.5x Intel) | SPEED_LIST (HalfKA find-nnz row), no card
3. https://uops.info/html-instr/VPCOMPRESSD_ZMM_K_ZMM.html (recorded 23:05) | measurement data site (facts only) | VPCOMPRESSD zmm{k}, zmm (register destination): Zen 5 latency 4 / 9 (mask) / 4, TP 1.00 c, 2 uops on FP12; Zen 4 5 / 9 / 5, TP 1.33; Ice Lake / Alder Lake-P / Emerald Rapids 3 / 6 / 3, TP 2.00. On Zen 5 the register form (1 c) beats the store form (3 c): compress to a register, then a plain store | SPEED_LIST (HalfKA find-nnz row), no card
4. https://www.agner.org/optimize/instruction_tables.pdf ("Last updated 2025-09-20"; recorded 23:07, via pdftotext of the downloaded file, AMD Zen 5 section) | documentation (facts only, no code) | Zen 5: VPDPBUSD(S) v,v,v 1 op, latency 4, reciprocal throughput 0.5, pipes P01 (uops.info measured latency 3, TP 0.5); VPCOMPRESSB/W/D/Q z{k},z 2 ops, latency 5 (y{k},y 2 / 4; x{k},x 2 / 2), no throughput printed, no memory-destination row | SPEED_LIST (HalfKA rows), no card
5. https://github.com/llvm/llvm-project/blob/b53763029964ff42b806ede881612fc391344327/bolt/README.md (gh api, 2026-10-20 commit; recorded 23:07) | Apache-2.0 WITH LLVM-exception (README only) | line 12: "BOLT operates on X86-64 and AArch64 ELF binaries"; profiles from Linux perf (LBR) or BOLT's own -instrument mode; build instructions "assuming that you are running under Linux". So BOLT on MSYS2 / Windows PE exes: NO (input must be ELF) | T05-02 (BOLT line), SPEED_LIST
6. https://github.com/official-stockfish/Stockfish/pull/6359 (PR text only, merged 2025-10-14) + PR 7041 (PR text only, merged 2026-08-10) | GPL-3.0, ideas only (PR text) | 6359 "Use huge pages for worker data" (14 MB per worker): ~1.2 % nps on a large machine (20 runs: 288,644,510 -> 292,082,422); STC SPRT [0, 2] passed, LLR 2.95, 166,272 games W 43479 L 42993 D 79800 (~+1.0 Elo computed), fishtest 68e9f3c0d323fd15c04e3ba4; with 28 MB worker data only +0.3 % (noise). 7041 "Place continuation history on large pages": +1.04 % nps (200 runs, paired t 3.415, p 0.0008; +1.76 % over 50 runs), needs Linux THP madvise; STC [0, 2] passed LLR 3.42, 231,360 games W 60152 L 59553 (~+0.9 Elo computed), test 6a736a122cf557d58a2e1f51 | T05-03
7. Web search 23:10 "Zen 5 L1 DTLB ... L2 DTLB ... L2 cache 1MB" - result summaries of AMD's Zen 5 architecture deck (Igor's Lab copy https://igorslab.de/wp-content/uploads/2024/08/Zen-5-Architecture.pdf ; AMD Hot Chips 2024 deck https://www.hc2024.hotchips.org/assets/program/conference/day2/24_HC2024.AMD.Cohen.Subramony.final.pdf), Wikipedia Zen 5 | vendor slides / encyclopedia (facts only; the PDFs themselves NOT fetched) | Zen 5 core: L1 DTLB 96 entries, fully associative, all page sizes; L2 DTLB 4K entries, all page sizes except 1 GB (Zen 4: 72 / 3072); L2 1 MB per core, 16-way (Zen 4 8-way), 64 B/clk; no measured L2 latency found | T05-01, T05-03, V2P4_GAP
8. https://github.com/official-stockfish/Stockfish/pull/7006 (PR text only, merged 2026-08-01) | GPL-3.0, ideas only | "Update NNUE perspectives together": when both perspectives can be updated incrementally, catch up the lagging one and walk the common suffix once, decoding threat-feature changes once; STC [0, 2] passed, LLR 2.93, 69,632 games W 18217 L 17881 D 33534; no functional change. Mostly about threat / pawn-pair feature decoding, which Forge's 768-input nets do not have | no card (SPEED_LIST context only)
9. https://github.com/official-stockfish/Stockfish/pull/7115 (PR text only, merged 2026-09-09) | GPL-3.0, ideas only | "Use a local accumulator to eliminate redundant stores" - about move-scoring stores, not NNUE; STC [0, 2] passed, LLR 2.95, 89,280 games W 22920 L 22557 D 43803 | no card
Stop rule hit at 23:11: sources 8 and 9 (two in a row) gave no new card -> web research stopped here (WORKER_RULES caps).
Count: 10 web sources read (no. 6 holds two PR texts: 6359 and 7041); 0 forum threads; 0 engines deep-read.
Also seen (titles only, gh search before 23:11, not read): Stockfish PRs 6657 "Speed up update_accumulator_refresh_cache with
AVX512ICL", 6776 "Simplify out double_inc_update", 7225 "Pair int8 weight rows in accumulator updates", 7249
"Specialize some accumulator updates", 7251 "Unroll NNUE feature updates", 6233 "Speedup write_moves using
_mm512_mask_compressstoreu_epi16", 6681 "Add 1GB page support on x86 Linux", 7025 "Prefetch continuation correction
histories".

## Dead ends (one line each) and PENDING (written 23:17 PC clock)
- Agner's instruction_tables.pdf through the web fetcher: binary PDF, no text; the saved copy was converted with pdftotext locally (worked, no. 4).
- Stockfish PRs 7006 / 7115: threat-feature decoding and move-scoring stores - nothing for Forge's 768-input float path.
- No outside engine with a measured float -> int16 first-layer table number (MISSING; the stop rule ended the search).
- int16 accumulators: excluded by the bound (342,331 > 32,767 on all 256 units of the lock net); int8 first layer: excluded (15-bit weights).
- AVX-512 output kernel (bit-exact with the 16-lane order) and large pages for the ~1.55 MB of worker histories: each < 1 % expected -> dropped (SPEED_LIST rows 5, 6).
- BOLT: ELF only -> no for Forge's PE exes.
- Zen 5 L2 latency: not found; the Zen 5 deck itself was not fetched (facts from search summaries).
- tools/licence_at.py reads llvm-project's LICENSE.TXT as MIT; it is Apache-2.0 WITH LLVM-exception (corrected in licences.md).
- PENDING (crew measurements, no engine runs in this job): P4 (Y8 vs KB8 replicas on one exe), bytes vs refresh split of P2 / P3 (30-h counters on KB4 / KB8 / KB32 replicas), per-file share of P1 (fresh copies + A/A).
