# T05D sources (one line per source read; W = web, L = local / own records)
Sub-track: node-identical search-side speed (TT prefetch placement, history table layout, move scoring / selection,
SearchStack layout, branch hints, other bit-exact search-overhead cuts). Worker start 00:46 PC clock.

- L1. Lock FD3A5190 source (read-only) `src_al1s198_clean`: include/forge/search.hpp (408 lines, read in full) and
  src/search.cpp (read in full: TT :184-314, MovePicker :319-556, histories :704-766, qsearch :771-870, search
  :875-1225, driver :1230-1531) | own | TT path, picker, history tables, stack layout | T05D-01, T05D-02, TABLE
- L2. R7 J3 report `opus-r7-nps:opus_r7/j3/REPORT.md` (git show, read-only) | own | perf hotspots (HCE 14.4 %, MovePicker::next
  10.9 %, TT probe 10.7 %), R7TtExclusive +3.59 % [+1.38, +5.84] d16 / +3.97 % [+1.23, +6.77] d20 wall (15 runs, PC,
  73 % busy), callgrind -1.26 % Ir; R7PrefetchEarly no gain (+0.84 % Ir); R7QuietGen / R7EvalPrefetch neutral | T05D-01, T05D-02
- L3. Lock exe disassembly `F:/odr/work/T05C/lock_v23.dis` (T05C's objdump of
  C:/Users/Administrator/grok-pc/forge_push/locks/lock_AL1_s198_ltopgo_x_20261030/forge_ltopgo_x_al1s198_v23.exe,
  sha256 re-hashed by T05D at 01:10: fd3a51903e73dc1f..., read only): 4 call sites of `__emutls_get_address` in the search path (Worker::search 0x1400ee166 inside the inlined TT
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
- W3. Alex2262/AltairChessEngine commit titles since 2024 (`mine_commits.py --grep`, 21 shown; `--show` 2639e58 "Stack
  fixes (#193)", 83c9dff "TT power of 2 size (#157)") | MIT | no number in either message (bench lines only); Forge
  already indexes the TT by multiply-high | no card (TABLE row 19)
- W4. Adam-Kulju/Patricia commit titles since 2024 (`mine_commits.py --grep`, 70 shown; `--show` 36b2889, eeb786d,
  70cc64b) | MIT | 36b2889 (PR 209 movepick) +3.29 +- 2.38, 8.0+0.08s Threads=1 Hash=16MB, SPRT [0, 3], LLR 2.96,
  N=31,038 (https://chess.swehosting.se/test/14363/); "93M nps" / "Faster attackers_to" are movegen (T05C's area) | no card
- W5. Patricia eeb786dd5a diff (gh api commit patch, engine/src/movepick.h +115 -53; read lines 1-200) | MIT | an
  ordering change (capture-history-adjusted SEE threshold at the picker's good / bad split, x2 weight on the 1-ply
  continuation, capture score terms), not node-identical | no card (TABLE row 18; possible evidence for T04B-01)
- STOP RULE reached after W3 and W4 / W5 (two sources in a row without a new card): no further web source was read.
- L7. R7 perf profile `opus-r7-nps:opus_r7/j3/logs/ci_prof1_base/perf_self_off.txt` (bench 16, quiet Linux runner,
  g++ -O3, perf cpu-clock self time) | own | MovePicker::next 10.92 %, TT probe 10.66 %, generate_pseudo_legal 5.84 %,
  memset 3.19 %, corrected_eval 2.76 %, quiet_history 2.17 %, __introsort_loop 1.54 %, TT store 0.75 %,
  update_quiet_stats 0.35 %, lock_stripe 0.32 % | T05D-02, T05D-03, TABLE evidence rows
- L8. R7 engine commit 2d9889cf (`git show --stat`, message) | own | R7TtExclusive = one-worker exclusive searches
  probe / store without lock_stripe; the R7 tree has tt.hpp / thread_data.hpp (not the lock's layout) | T05D-01
- L9. RUN_INFO.json of 8 recent crew gates under F:/forge_push/gate_* (grep only) | own | option.Hash=16 in all | TABLE row 4
- L10. `tools/forge_has.sh` greps of the lock: 'has_exclusive_access|lock_stripe|thread_local' (12 hits),
  '__builtin_prefetch|prefetch\(' (4 hits: search.hpp:125-127, search.cpp:847, :1126), 'nonpawn|...' (0),
  'correction_history_|material_correction_' (10), 'likely|__builtin_expect' (0) | own | cards + TABLE
Count: 5 web sources (W1-W5), 10 local records (L1-L10); 3 engines looked at (Caissa, Altair, Patricia; one diff
each from Caissa and Patricia). Correction for the coordinator: notes/T05/SPEED_LIST.md line 34 says R7TtExclusive is
in the lock; the lock source and exe show it is not (T05D-01, TABLE row 20).
