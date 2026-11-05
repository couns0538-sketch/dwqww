# T05D sources (one line per source read; W = web, L = local / own records)
Sub-track: node-identical search-side speed (TT prefetch placement, history table layout, move scoring / selection,
SearchStack layout, branch hints, other bit-exact search-overhead cuts). Worker start 00:46 PC clock.

- L1. Lock FD3A5190 source (read-only) `src_al1s198_clean`: include/forge/search.hpp (408 lines, read in full) and
  src/search.cpp (read in full: TT :184-314, MovePicker :319-556, histories :704-766, qsearch :771-870, search
  :875-1225, driver :1230-1531) | own | TT path, picker, history tables, stack layout | T05D-01, T05D-02, TABLE
- L2. R7 J3 report `opus-r7-nps:opus_r7/j3/REPORT.md` (git show, read-only) | own | perf hotspots (HCE 14.4 %, MovePicker::next
  10.9 %, TT probe 10.7 %), R7TtExclusive +3.59 % [+1.38, +5.84] d16 / +3.97 % [+1.23, +6.77] d20 wall (15 runs, PC,
  73 % busy), callgrind -1.26 % Ir; R7PrefetchEarly no gain (+0.84 % Ir); R7QuietGen / R7EvalPrefetch neutral | T05D-01, T05D-02
- L3. Lock exe disassembly `F:/odr/work/T05C/lock_v23.dis` (T05C's objdump of forge_ltopgo_x_al1s198_v23.exe, read
  only): 4 call sites of `__emutls_get_address` in the search path (Worker::search 0x1400ee166 inside the inlined TT
  probe, 0x1400f2152; Worker::qsearch 0x1400facc5; TranspositionTable::store 0x1400fe605); emutls -> pthread_getspecific
  = GetLastError + once check + TlsGetValue + pthread_spin_lock (`xchg` with memory = locked, a full fence) +
  pthread_spin_unlock + SetLastError | own | T05D-01 (the lock still pays the TLS path R7TtExclusive removed)
- L4. notes/TRIED_GATES.md rows R7-TTX (option.R7TtExclusive=true, 2534 g, +3.84, H1 NON-REGRESSION SPRT [-10,0]) and
  R7-PFE (option.R7PrefetchEarly=true, 1000 g, +2.78, LLR 0.06, cap no decision); gate101 speedmp2 1500 g -6.95 cap | own | T05D-01, T05D-02
- L5. R14 FINAL_REPORT `opus-r13-status:opus_r14/FINAL_REPORT.md` lines 22, 33, 45, 49: SPEED2 de20653c = TT prefetch
  after null move + ProbCut make, speedmp2 MovePicker hoist, table piece_type; advisory ABBA d16 +3.0 % / d20 +2.8 %
  (A/A noise up to +2.6 %); not timed by QA | own | T05D-02 (SPEED2 has no TLS change)
- W1. Witek902/Caissa commit titles since 2024 (`tools/mine_commits.py --grep`, 58 shown; `--show` b02c47f, a51c9f1,
  fe4db18, 41a5023, 29823f0) | MIT (copy with notice) | b02c47f "Speedup: Prefetch correction histories" SPRT
  5.0+0.05s Threads=1 Hash=8MB [0,2] LLR 2.95, N=49,432, +2.40 +- 1.60, penta [259, 5534, 12790, 5872, 261]
  (https://furybench.com/test/6332/); a51c9f1 node counting +1.82 +- 2.87 at 8 threads [-4,0] (SMP only); 29823f0
  ProbCut in a noinline method to halve NegaMax's ~5 KB frame (no number) | T05D-03, TABLE
- W2. Caissa b02c47fa354528cdf45c2f179883b65a0a1db9f2 diff (gh api commit patch, 59 lines; Search.cpp +11, Common.hpp
  +12, TranspositionTable.cpp +1 -7) | MIT | the child's 4 correction entries (pawn, non-pawn white / black,
  continuation correction) are prefetched in the move loop right after the child position exists | T05D-03
- L6. Lock exe frames: Worker::search reserves 0x1318 = 4,888 B per call through ___chkstk_ms (frame > 4 KiB: a page
  probe loop with `orq $0,(%rcx)` per call); Worker::qsearch 0xf18 = 3,864 B (no probe); MovePicker::next is scalar
  (0 vpmax / vpcmp; unrolled selection with data-dependent jg + cmov) | own | TABLE (evidence for T05C-02), T05D-02
