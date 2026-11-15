# REPORT kimik3 job 1 — make HistRework faster, bit-exact

**1. First line.** The cost of `HistRework 2` was 14.1 % of throughput before my change and 13.3 % after it
(M3 medians of the nps ratio noopt/HR2: 1.1646 before, 1.1530 after); that difference is far below the measured
noise floor (M1 self-vs-self spread 0.926–1.036), so per the job's own rule the gain is **NOT SHOWN**. Every
result stayed identical: O1 node counts 21/21, O2 2000/2000 positions in both modes (best move, score, nodes),
`go perft 5` = 4865609 on both copies. **Recommendation: do not port `speed.patch.txt`; it is neutral at best.**

**2. Step 0, expected vs printed (baseline, fresh process per line, raw files in `tests_kimik3_job1/step0/`).**

| command | expected | printed | ok |
|---|---|---|---|
| no option, bench 11 | 312866 | 312866 | yes |
| no option, bench 13 | 862329 | 862329 | yes |
| no option, go perft 5 | 4865609 | 4865609 | yes |
| BundlePreset B1, bench 11 | 280182 | 280182 | yes |
| BundlePreset B1, bench 13 | 758456 | 758456 | yes |
| BundlePreset B1, bench 16 | 3357587 | 3357587 | yes |
| TtPruneV2 true, bench 11 | 309157 | 309157 | yes |
| TtPruneV2 true, bench 13 | 736967 | 736967 | yes |

All 8 matched, so everything below counts. Build: commit `d4f43124` exported out of the git tree,
`b1_port.patch` applied with `patch -p1` (0 rejects, apply log in `step0/b1_port_apply_log.txt`), then
`cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS='-DFORGE_NNUE_HIDDEN=256'`
for BOTH copies (g++ 13.3.0, cmake 3.28.3; identical flags; CMake Release = `-O3 -DNDEBUG`).

**3. The idea (one only).** *Lazy lesser-threat maps* (`speed.patch.txt`, 3 hunks):
`include/forge/search.hpp` (member declaration), `src/search.cpp` (qsearch node entry, main-search node entry,
`threat_history_entry`). Instead of building `lesser_threats(board)` at every node where the option is on
(qsearch: only in-check nodes), the node just marks its slot stale; the maps are built on the first actual read
inside `threat_history_entry`. Why it cannot change a result: every read of `threat_maps_[ply]` goes through
`threat_history_entry(board, ss, move)`, called only at a node that (re)marked its own slot at entry with the
same board (main search marks every node, qsearch marks exactly the in-check nodes — and I verified in
`MovePicker` that a qsearch node not in check only ever runs stages QsTT/QsGenerate/QsCaptures, which never call
`quiet_history`, so no read ever happens at an unmarked node). At any read the returned value is therefore
`lesser_threats(B_node)` in both versions; `lesser_threats` is a pure function of the board, which make/unmake
restores before any read. Its own speed number: M2 medians 0.977 (B1), 0.992 (HR2 alone), 1.003 (no option) —
not distinguishable from the M1 noise; the B1 median hints at a slight LOSS (see §6 for why).

**4. The oracle.**
- **O1** (`o1/base/`, `o1/patched/`): all 21 node-count lines identical between baseline and patched —
  bench 11/13/16/20 × {no option, HistRework 2, BundlePreset B1, HistRework 1, HistRework 3} plus perft 5
  (= 4865609 both). Baseline's B1 bench 20 = 11208630, matching the job's known value. Baseline table:
  noopt 312866 / 862329 / 3024920 / 12389307; HR2 320427 / 881902 / 3041041 / 12218938;
  B1 280182 / 758456 / 3357587 / 11208630; HR1 373261 / 1043893 / 3399770 / 13180132;
  HR3 336192 / 869621 / 3052885 / 15664938.
- **O2** (`o2/`): the official `UHO_Lichess_4852_v1.epd` from github.com/official-stockfish/books (the plain
  `.epd` 404s on both `main` and `master`; I used `UHO_Lichess_4852_v1.epd.zip` from `master`, unzipped, first
  2000 lines). Mode A (ucinewgame before each position): `o2_base_A.sum` vs `o2_patched_A.sum` byte-identical,
  2000/2000. Mode B (one process, no ucinewgame, history carries over): `o2_base_B.sum` vs `o2_patched_B.sum`
  byte-identical, 2000/2000. Full raw engine output kept in `o2/*.raw` (4 × 2 MB text).
- **O3** (`o3/`): planted fault = the map of the wrong side (`opposite(...)` removed in
  `hist_rework.hpp:45`, a third copy). The oracle reports it: with HistRework 2, bench 13 = 881902 baseline vs
  868141 faulty; with B1, bench 11 = 280182 baseline vs 278313 faulty. (Also note O1's own table above contains
  the check: baseline HR2 bench 13 = 881902 ≠ any other line.) Positive control holds.
- **O4** (`o4/`): patched copy built with `-DFORGE_ENABLE_SANITIZERS=ON` (adds `-fsanitize=address,undefined
  -fno-omit-frame-pointer`). Positive control first: `scripts/san_probe.cpp` (heap overflow + signed overflow)
  aborts with both an ASan `heap-buffer-overflow` ERROR and a UBSan runtime error (`o4/san_probe.out`,
  exit 1). Then: bench 13 with B1 → nodes 758456 (matches Step 0), stderr 0 bytes; the first 200 O2 positions
  with B1 depth 9 → exit 0, stderr 0 bytes (`o4/o4_san_200.err` is the empty file).

**5. Measurements** (all `bench 16`, fresh process per run, pinned to core 2 with `taskset -c 2`, 20
interleaved pairs, order AB then BA alternating; ratio = second label / first label; raw per-run nps in `m/`).
- **M1 noise (baseline vs baseline, B1)**: median 1.004606, min 0.926150, max 1.035833. Ratios: 1.021285
  0.992975 1.003540 0.992877 1.010900 1.006461 1.006089 0.991039 0.998516 1.019857 1.018209 0.995155 0.933562
  1.029772 1.001024 0.926150 0.965152 1.035833 1.017538 1.005671.
- **M2 patched vs baseline**: B1: median 0.976853, min 0.958939, max 1.038512. HR2 alone: median 0.991606,
  min 0.880341, max 1.046735. no option: median 1.002520, min 0.858704, max 1.061317. (Full ratio lists in
  `m/m2_*.txt`; every run's nps and node count is recorded there.) The no-option M2 is the same-binary control:
  its pairs swung 0.859–1.061 around median 1.003, i.e. the two HistRework M2 medians (0.977, 0.992) sit inside
  this machine's pair noise, with B1 leaning to a slight real loss.
- **M3 cost of the switch (ratio noopt-nps / HR2-nps within one binary)**: baseline: median 1.164554, min
  1.065178, max 1.282186 → HR2 costs the baseline 14.1 % of nodes/s. Patched: median 1.153048, min 1.096687,
  max 1.220147 → 13.3 %. Before-vs-after difference ≈ 0.9 % of throughput — below the M1 spread → **not shown**.

**6. Ideas not bit-exact, and why the measured ceiling is ~0.05 % (the important part).** No non-bit-exact
variant was kept. After M2 showed no gain I measured where the cost actually is (evidence in `diag/`):
- A traced copy (local only, counters in `diag/trace_*.err`) on bench 16 B1: nodes 3357587; eager build sites
  871361 main + 85360 qsearch-in-check = 956721; lazy builds actually needed 710383; `threat_history_entry`
  reads **16053915**. So lazy skips only 25.7 % of builds, and there are **22.5 reads per build** — the build is
  not the cost center; the read path is.
- A microbenchmark (`scripts/ubench.cpp`, `diag/ubench.out`, anti-hoisting memory barriers, pinned): one
  `lesser_threats` build costs **≈ 5 ns**. All 956721 eager builds of a bench-16-B1 run together cost ≈ 4.8 ms
  of ≈ 3000 ms = **0.16 % of runtime**. Lazy's best possible gain (skipping 26 % of them) is ≈ 0.04 % — forever
  below any noise floor. The B1-leaning loss of v1 is consistent with `threat_history_entry` growing a cold
  branch and losing inlining into the 16-million-call read path; a fixed variant (cold build in a separate
  noinline function) was designed but, by this cost model, cannot beat ≈ 0.2 % either, so I did not spend the
  remaining minutes measuring it.
- A "no-build" diagnostic variant (empty maps, results change on purpose) measured nps 3 % LOWER at a different
  node count (3158350 vs 3041041): the changed tree contaminates the comparison — I report it as a failed
  diagnostic, not as evidence.
- Conclusion: the job's hypothesis ("maps are built at every node whether or not used") is true but only worth
  ≈ 0.16 % here; HR2's real cost (14 % per M3, matching the ~10 % Fable sees on the PC) sits elsewhere — most
  likely the 16M threat-table reads + blend, the per-eval `joint_key`/`non_pawn_material` work, and cache
  footprint of the extra tables. I could not verify this split: `perf` does not exist on this machine.

**7. Repository files I opened** (engine tree = commit d4f43124 + b1_port.patch): `CMakeLists.txt`,
`include/forge/hist_rework.hpp`, `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`.
In the dwqww repo: `forge-combo29/soak_all/FABLE_TO_kimik3_1.md`, `opus_r13/p1/b1/b1_port.patch`
(via `git show`). Downloaded from the official source only: the Stockfish book zip named in §4.

**8. Step times (UTC, from recorded stamps; "~" = bounded by the neighbouring stamps, not independently
stamped).** 15:53 job file read. 15:54:31 env check (4 cores, g++ 13.3.0). ~15:54–15:55 fetch commit +
patch branch, export, apply patch, configure both. ~15:55–15:56 baseline build + Step 0. ~15:56 patch v1 +
patched build + O1 launched. 15:56–15:57 book fetch (zip), O3 faulty copy + control, san probe. ~15:57
sanitizer build; 15:57–15:58 O1 compare (21/21), O2 mode A, O4 bench13 (12 s) + O4 200 positions (23 s).
15:58:30 O2 relaunch of 3 failed drivers (my shell bug, see §9), 15:58:54 all O2 done. 15:58:59 M series
start; 16:01:45 M1 done; 16:07:18 M2 done; 16:09:30 M3-base done; 16:10:06 all M done. ~16:08–16:12 trace
counters, failed no-build diagnostic, microbenchmark. ~16:13–16:30 evidence copy, this report, commit, push.

**9. What I did NOT do.** No perf profile (tool absent) — the 14 % is not attributed beyond the build-side
exclusion (0.16 %) and the read/build ratio (22.5). I did not measure the noinline variant of the lazy patch
(§6). I did not run O2 on random legal positions (the official book was available and used). The first O2
launch failed for 3 of 4 drivers (a `cd x && cmd &` shell-precedence bug put them in the wrong directory; the
error logs are in `o2/*_B.log` history); I relaunched them and they completed — mode A baseline output was from
the first launch, unaffected. The faulty copy's first build silently reused the patched copy's build directory
(a copied CMake cache points at the old source dir); I caught it because the build was impossibly fast,
reconfigured fresh, and verified the fault is really in the binary via O3's differing node counts.

**10. What I am not sure about.** (a) Whether v1 is truly slightly slower or the 0.977 B1 median is this VM's
noise — the no-option control pairs swung wider (0.859–1.061) than that median's distance from 1. (b) The
14 %-cost attribution (reads vs joint-key vs cache) is reasoned, not measured. (c) The 5 ns/build figure is a
hot-loop average over 8 bench positions; in-search builds may cost more under cache pressure — even 10× more
would leave lazy's ceiling at 0.4 %, still not shown. (d) M3's 14.1 % has a wide pair spread (1.065–1.282);
the median is stable across the two binaries (1.165, 1.153), so the cost itself is real.

**11. A better way.** (i) *Measure the cost split before writing the patch.* Ten minutes with the traced
counters + microbenchmark (both committed as evidence) would have shown up front that the eager maps are 0.16 %
of runtime and that any build-side idea is capped far below noise — the job's "start there" would have been
refuted before spending M1/M2 runs on it. Suggest every speed job begins with a counters pass (sites vs would-be
savings vs reads) and a microbenchmark of the target function; Fable can check it by re-running the two small
scripts on the PC. (ii) For attribution variants like my no-build diagnostic: keep the searched tree identical
(freeze all history scores at 0 instead of changing what is computed) or the nps comparison is uninterpretable —
I learned this by doing it wrong. (iii) On a VM this noisy, 20 pairs with alternating order still leaves
±8 % pair swings; a cheaper protocol is 5 warmup pairs, then 20 pairs, and report the median of pair ratios
only (as done) — budgeting more pairs beats longer benches.

**12. Model.** Kimi K3 (Moonshot AI), exact version unknown to me; running as Cursor cloud agent "kimik3".
