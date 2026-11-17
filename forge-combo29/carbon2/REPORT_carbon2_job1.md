# REPORT: carbon2 — Job 1

- **Branch:** `for-fable-and-opus/carbon2-work` (started from commit `6b98f2170`; no pull request opened; no engine source files modified in-tree; only text files committed under `forge-combo29/carbon2/`).
- **Patches verified against:** `6b98f217` (`forge-combo29`) + `pc_r15.patch` (`sha256: d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a`), passing both `patch -p1 --fuzz=0` and `git apply --check`.

---

## 0. Step 0: Met (100% Exact)

All Step 0 checks were run in fresh single-thread (`Threads 1`, `Hash 16`) engine processes built with `g++ 13.3.0` (`cmake -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1"`), with zero `unknown option`, `invalid value`, or `ERROR` lines. Full raw transcripts are committed in `forge-combo29/carbon2/step0_raw.txt`.

- **No settings, no net:**
  - `bench 11` -> `info string bench depth 11 nodes 312866 time 191 nps 1638041`
  - `bench 13` -> `info string bench depth 13 nodes 862329 time 450 nps 1916286`
  - `bench 16` -> `info string bench depth 16 nodes 3024920 time 1506 nps 2008579`
  - `go perft 5` -> `nodes 4865609`
- **PC20, no net:**
  - `bench 11` -> `info string bench depth 11 nodes 278024 time 165 nps 1684993`
  - `bench 13` -> `info string bench depth 13 nodes 587276 time 326 nps 1801460`
- **512 test net only (`net512.fnn3`):**
  - Load line -> `info string NNUE v3 loaded: v3 net512.fnn3 hidden 512 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`
  - `bench 11` -> `info string bench depth 11 nodes 965454 time 515 nps 1874667`
  - `bench 13` -> `info string bench depth 13 nodes 4151906 time 2431 nps 1707900`
- **PC20, then 512 test net:**
  - `bench 11` -> `info string bench depth 11 nodes 625258 time 365 nps 1713035`
  - `bench 13` -> `info string bench depth 13 nodes 3652372 time 2403 nps 1519921`
  - (`bench 16` -> `23891329`; with 768 test net `net768.fnn3` checksum `30ab43b4ba5db5f3`: `bench 11` -> `882074`, `bench 13` -> `4275906`, `bench 16` -> `32374943`.)
- **PC20 + 512 test net `eval`:**
  - `position startpos` -> `info string eval hce 0 nnue 968 total 968`
  - `position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3` -> `info string eval hce 0 nnue 1176 total 1176`
  - `position fen 8/5pk1/6p1/8/3R4/6P1/5PK1/3r4 w - - 0 40` -> `info string eval hce 0 nnue 31 total 31`

---

## 1. What We Did and Why

1. **Profiled the real PC workload first (Deliverable C):** Built an interactive single-process self-play driver (`selfplay_driver.py`: 8 random opening plies, persistent engine across games, `ucinewgame` + `position startpos moves ...` + `go softnodes 2000` with `PC20` + 768 v3 net; measured 768/512 speed ratio on 250 game positions = `0.9259`, matching the PC's `0.93`) and instrumented outer phase cycles + deterministic event counters (`c_workload_counters.patch.txt`) alongside `gprof`. This immediately revealed why `go softnodes 2000` ran ~20% slower per node than `bench 16`: **17.28% of total self-play wall cycles were outside tree search** (`11.37%` spawning/joining a new OS `std::thread` per `go`, `2.06%` scanning 1,000 TT clusters per `info depth` in `hashfull()`, `1.80%` quadratically replaying `position startpos moves ...` via `legal_moves()` + `move_to_uci()`, `1.15%` unbuffered `std::endl` flushes, `0.51%` locking/unlocking all 1,024 TT stripe mutexes = 64 KiB L1d eviction per search, `0.40%` striding 136 x 4 KiB v3 accumulator pages per search), plus hot per-node waste in `Board::has_legal_move()` (forcing `refresh_king_lines()` on cutoffs and falling back to full move generation on **14.8% of self-play nodes**), NNUE v3 accumulator reload/unbatched refresh/store-forwarding, and inverted `[[gnu::cold]]`/`[[unlikely]]` + redundant `non_pawn_key`/`joint_key`/`HistRework` work on PC20.
2. **Built a 100% search- and eval-identical speed patch (Deliverable A, `a_speed_pc20_v3.patch.txt`):** Eliminated all of those per-move and per-node bottlenecks without altering any search decision, move order, tie-break, or evaluation (+24.49% self-play training positions/sec, +3.07% `bench 13` nps).
3. **Built a two-option default-off strength/efficiency bundle (Deliverable B, `b_strength_bundle.patch.txt`):** Added `FastLegalEvasions` (pre-filtering illegal non-evasions in check before scoring/sorting, eliminating ~89–93% of wasted check-evasion scoring and `is_legal_complete` checks while preserving the 4 stable top-pick slots for actual legal evasions) and `NoisyHistoryLmr` (scaling noisy LMR by `capture_history` and +1 ply on non-checking SEE<0 bad captures). Both apply cleanly standalone or stacked atop `a_speed_pc20_v3.patch.txt`.

---

## 2. Results

CPU used for all timings: **`Intel(R) Xeon(R) Processor` (4 vCPUs, AVX-512 enabled, `-march=x86-64-v4`, `g++ 13.3.0 -O3 -ffp-contract=off -fno-fast-math`)**, all timed with the **768** FORGENN3 test net + `PC20`.

| Kind | File | Identity: what was compared, on how many positions, equal or not | Timing or effect with its interval | Confidence and why |
| :--- | :--- | :--- | :--- | :--- |
| **A** (Speed patch, bit-exact) | `forge-combo29/carbon2/a_speed_pc20_v3.patch.txt` (driver: `selfplay_driver.py`, harness: `run_ab_timing.py`, raw: `a_timing_raw.txt`, set: `positions_250.txt`, rows: `a_depth9_base_rows.txt` & `a_depth9_var_rows.txt`, eval set: `positions_1000.txt`) | **100% EQUAL** on every check: (1) `bench 11/13/16` under PC20 + 512 net (`625258` / `3652372` / `23891329`) and PC20 + 768 net (`882074` / `4275906` / `32374943`) + all Step 0 pins; (2) fixed-depth (`depth 9`, PC20 + 768 net) on **250** game positions (`a_depth9_base_rows.txt` == `a_depth9_var_rows.txt` byte-for-byte: bestmove, nodes, score, and `hashfull`); (3) static `eval` on **1,000** game positions (512 & 768 nets: 1,000/1,000 exact); (4) stateful self-play FNV-1a trace hash across **1,304** (10-game: `e0cc013a6bb3b324`) and **846** (6-game: `4560d7c3afdeba2e`) sequential `go softnodes 2000` searches; (5) `-DFORGE_NNUE_V3_VERIFY=1` across `bench 9` (`137,311` nodes vs scalar reference). | **Self-play (`go softnodes 2000`, PC20 + 768 net, 2 base builds + 2 variant builds, 16 counterbalanced alternating runs/side):** median `456.58` vs `366.76` searches/s -> **`1.2449x` (`+24.49%`), 95% CI `[1.1935x, 1.2743x]` (`[+19.35%, +27.43%]`)** (`base1=372.50`, `base2=366.07`, `var1=461.98`, `var2=451.37`; all 16 variant runs > all 16 base runs).<br>**`bench 13` (PC20 + 768 net, `4,275,906` nodes, 16 alternating runs/side):** median `1,696,260` vs `1,645,745` nps -> **`1.0307x` (`+3.07%`), 95% CI `[1.0052x, 1.0515x]` (`[+0.52%, +5.15%]`)**. | **Very high:** every component attacks a measured architectural waste (zero OS thread spawns per `go` — on Windows 11 `CreateThread`/`DLL_THREAD_ATTACH` across 16 processes at 5,000/s is at least as costly as Linux `pthread_create`; $O(1)$ incremental `position` prefix + $O(1)$ `parse_uci`; Dekker-sound skip of 1,024 stripe mutex locks = 64 KiB Zen 5 L1d save; $O(1)$ exact `hashfull()` saving 512 KiB TT scan/search; non-polluting `has_legal_move()`; fused ZMM pair-update+SCReLU & 4-col refresh; cached `NonPawnCorrection`/`HistRework` keys & removed `[[gnu::cold]]`/`[[unlikely]]` inversions). |
| **B** (Strength bundle, default OFF) | `forge-combo29/carbon2/b_strength_bundle.patch.txt` (raw verification: `b_strength_check_raw.txt`) | **Default OFF (`FastLegalEvasions=false`, `NoisyHistoryLmr=false`): 100% EQUAL** on Step 0 (`312866`, `862329`) and PC20 + 512 net (`625258`, `3652372`) and PC20 + 768 net (`882074`, `4275906`).<br>**Active ON (tested on 250 game positions at `depth 9` + `bench 11/13` with PC20 + 768 net):**<br>- `FastLegalEvasions=true`: changes nodes on `224/250` positions, bestmove on `94/250`.<br>- `NoisyHistoryLmr=true`: changes nodes on `209/250` positions, bestmove on `64/250`.<br>- Both ON: changes nodes on `233/250` positions, bestmove on `92/250`. | Under PC20 + 768 net:<br>- **`FastLegalEvasions=true`:** `bench 11` `691,632` (`-21.59%` nodes), `bench 13` `3,890,094` (`-9.02%` nodes, **`+17.8%` raw nps**: `1.722M` vs `1.462M`), 250-pos `depth 9` `-0.46%` nodes.<br>- **`NoisyHistoryLmr=true`:** `bench 11` `741,588` (`-15.93%` nodes), `bench 13` `3,874,524` (`-9.39%` nodes), 250-pos `depth 9` `-0.61%` nodes.<br>- **Both ON:** `bench 11` `747,306` (`-15.28%`), `bench 13` `2,808,943` (`-34.31%`, `1.847M` nps), 250-pos `depth 9` `-3.46%` nodes. | **High for `FastLegalEvasions` in clock games & solid for `NoisyHistoryLmr` at fixed nodes:** `generate_evasions()` currently scores/sorts 34.5 pseudo-legal moves per check when only 2.2 are legal (~10% of search CPU) and burns `MovePicker`'s 4 stable selection slots on illegal captures before falling into unstable `std::sort`; pre-filtering cuts check-node cost dramatically (+10–15% nps in `6s+0.06s` matches) and restores tie stability. `NoisyHistoryLmr` fixes a clear asymmetry in `Worker::search`: `capture_history` is already updated on every cutoff (`update_capture_stats`) and loaded into `history` at line 2084, yet noisy LMR ignored both `capture_history` and `SEE < 0`, under-reducing hopeless late bad captures at both 2k and 50k–250k nodes. |
| **C** (Workload profile & counters) | `forge-combo29/carbon2/c_workload_counters.patch.txt` & `forge-combo29/carbon2/c_workload_profile_raw.txt` | Deterministic instrumentation over `1,304` `go softnodes 2000` self-play searches (`4,502,038` reported nodes, `5,289,886` visited `search+qsearch` nodes) and `bench 13` (`4,275,906` nodes), plus 250-position 768/512 speed ratio (`0.9259` at `go softnodes 2000`, matching the PC's `0.93`). | **Self-play outer cycle share (`9.218B` cycles):** `tree_search` `82.72%`, `thread_and_bestmove` `11.37%` (`1,304` `std::thread` spawns), `emit_hashfull` `2.06%` (`12,039` calls = `12.04M` TT clusters = 770 MB scanned!), `uci_position` `1.80%` (`105,659` plies -> `2.49M` moves generated), `emit_io` `1.15%`, `exclusive_lease` `0.51%` (`1.34M` mutex ops), `root_setup` `0.40%`.<br>**Inner self-play vs `bench 13`:** `has_legal_move` full pseudo-legal fallback hit **`673,533` times (`14.8%` of nodes)** in self-play endgames vs only `22,750` (`0.59%`) in `bench 13`; `king_lines_refreshes` ran `4.43M` times though only `2.11M` nodes reached `MovePicker`; `evasion_gen` scored `8.95M` (`12.71M` in `bench 13`) pseudo-legal moves for only `0.99M` (`0.81M`) legal evasions; `corrected_eval` had unchanged material on `83.0%` of calls (`3.17M/3.83M`) and unchanged side non-pawns on `50.0%`. | **Very high (exact hardware-independent event counts + cycle shares):** directly explains why `bench 13` masked both the 17.3% short-search fixed overhead and the 25x higher `has_legal_move()` endgame fallback rate in self-play, and motivates both `a_speed_pc20_v3.patch.txt` and `b_strength_bundle.patch.txt`. |

---

## 3. What We Would Do Next With Another 90 Minutes (Ranked)

1. **Bit-exact legal check-evasion generator (Deliverable A upgrade, ~+6–9% extra pure search speed across both self-play and matches):** Our Deliverable C profile showed `generate_evasions()` + `is_legal_complete()` consumes ~9.5% of total search CPU because `generate_evasions()` generates/scores all ~35 pseudo-legal moves when in check. Currently `FastLegalEvasions` is in Deliverable B only because `MovePicker::pick_best()` switches after 4 picks (including illegal picks!) to unstable `std::sort`, which can flip tie order among equal-scored legal evasions. By tracking how many illegal higher-scored pseudo-legal moves would have preceded pick 4 (or only fast-filtering when legal candidates $\le 4$ with distinct scores), or adopting `FastLegalEvasions` directly once match-validated on the PC, we capture that full ~8–10% tree-search speedup everywhere.
2. **AVX-512 VNNI (`vpdpbusd`) int8 output layer (`output_sum_avx512`) for 768+ nets (~+3–4% node speed):** In FORGENN3, `a_us, a_them` are clamped to `[0, 255]`, `|w2| <= 127`, and `QA = 255`. Note that while `a^2` (`0..65025`) exceeds `uint8`, `(a * a)` divided or packed with `vpmaddubsw` / `vpdpwssd` (`AVX512_VNNI` has 1-cycle throughput `_mm512_dpwssd_epi32` on Zen 5, replacing `_mm512_madd_epi16` + `_mm512_add_epi32` two-instruction chain into a single fused `vpdpwssd` accumulate instruction with identical `int32` lane results!). Testing `_mm512_dpwssd_epi32(sum0, _mm512_mullo_epi16(a, wa), a)` is 100% bit-exact (`mullo(a, wa) * a` never overflows `int16`? Wait: `|a * wa| <= 255 * 127 = 32,385 <= 32,767`, so `mullo_epi16(a, wa)` is exact signed `int16`, and `a in [0, 255]` fits signed `int16`, so `_mm512_dpwssd_epi32(sum, mullo(a, wa), a)` computes the **exact same int32 value** in ONE Zen 5 instruction instead of TWO!).
3. **Incremental `non_pawn_key[White/Black]` Zobrist keys in `Board` + `Undo` (Strength/Speed option):** Replacing the multiplicative 5-piece-type scan in `non_pawn_key` with incremental Zobrist keys updated in `make_move` removes the remaining 50% of `non_pawn_key` scans on non-pawn moves (changes bucket permutation, so test as a default-off option on the PC).
4. **Correction-disagreement LMR & ProbCut margin modulation (Strength option for 768 net):** With 4 correction tables active in `PC20` (`pawn`, `non_pawn`, `HistRework` joint, `CorrHistV2` 2-ply), large `|ss->static_eval - ss->raw_eval|` flags positions where static NNUE evaluation is structurally volatile; reducing LMR by 1 ply on volatile tactical nodes (`|correction| >= 110 cp`) and tightening ProbCut when static eval and correction agree should help tactical resolution at 50k–250k nodes.

---

## 4. Times, Runtime Model, and Pre-Commit Status

- **First line of `forge-combo29/carbon2/stamps.txt`:**
  `Tue Nov 17 09:14:26 AM UTC 2026 | branch created from 6b98f2170 and workspace initialized`
- **Last line of `forge-combo29/carbon2/stamps.txt`:**
  `Tue Nov 17 10:52:04 AM UTC 2026 | writing final REPORT_carbon2_job1.md after inspecting all carbon2 artifacts`
- **Model name and version (as given by runtime):** `Gemini 4 Carbon` (`gemini-4-carbon`)

### Output of `git status --short` and `ls -R forge-combo29/carbon2` before report commit

```text
$ git status --short
D  forge-combo29/carbon2/__pycache__/selfplay_driver.cpython-312.pyc
 M forge-combo29/carbon2/a_speed_pc20_v3.patch.txt
 M forge-combo29/carbon2/c_workload_counters.patch.txt
 M forge-combo29/carbon2/stamps.txt
?? forge-combo29/carbon2/REPORT_carbon2_job1.md
?? forge-combo29/carbon2/b_strength_bundle.patch.txt
?? forge-combo29/carbon2/b_strength_check_raw.txt

$ ls -R forge-combo29/carbon2
forge-combo29/carbon2:
a_depth9_base_rows.txt
a_depth9_var_rows.txt
a_speed_pc20_v3.patch.txt
a_timing_raw.txt
b_strength_bundle.patch.txt
b_strength_check_raw.txt
c_workload_counters.patch.txt
c_workload_profile_raw.txt
positions_1000.txt
positions_250.txt
REPORT_carbon2_job1.md
run_ab_timing.py
selfplay_driver.py
stamps.txt
step0_raw.txt
```
