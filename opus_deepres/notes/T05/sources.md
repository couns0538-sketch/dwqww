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

## Web sources
1. https://uops.info/html-instr/VPDPBUSD_ZMM_ZMM_ZMM.html (read 23:02) | measurement data site (facts only, no code) | VPDPBUSD zmm,zmm,zmm: Zen 5 latency 3 (all operand pairs), throughput 0.50 c (2 per cycle), 1 uop on FP01; Zen 4 latency 4, measured TP 1.00 (computed 0.50); Ice Lake / Tiger Lake / Alder Lake-P latency 5, TP 1.00 (p0); Cascade Lake / Emerald Rapids TP 0.50 (p05). Applies to the HalfKA int8 path only (the lock and v2 nets are float, no VNNI) | SPEED_LIST (HalfKA rows), no card
2. https://uops.info/html-instr/VPCOMPRESSD_M512_K_ZMM.html (read 23:04) | measurement data site (facts only) | VPCOMPRESSD m512{k}, zmm (memory destination, the find-nnz store form): Zen 5 8 uops (2 FP03 + 2 FP12 + 1 FP45), measured TP 3.00 c (computed 1.00), latency <= 46 / <= 19 / <= 18; Zen 4 144 uops, measured TP 72.50 c; Intel ICL..EMR 4 uops, TP 2.00. So the Zen 4 trap (store form ~24x slower than Intel) is gone on Zen 5 (1.5x Intel) | SPEED_LIST (HalfKA find-nnz row), no card
3. https://uops.info/html-instr/VPCOMPRESSD_ZMM_K_ZMM.html (read 23:05) | measurement data site (facts only) | VPCOMPRESSD zmm{k}, zmm (register destination): Zen 5 latency 4 / 9 (mask) / 4, TP 1.00 c, 2 uops on FP12; Zen 4 5 / 9 / 5, TP 1.33; Ice Lake / Alder Lake-P / Emerald Rapids 3 / 6 / 3, TP 2.00. On Zen 5 the register form (1 c) beats the store form (3 c): compress to a register, then a plain store | SPEED_LIST (HalfKA find-nnz row), no card
