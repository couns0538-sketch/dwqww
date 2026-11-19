# REPORT — `carbon2` Job 29: Verification of `kF` Against `r15d` Across All Reduced-Check Paths, Multi-Thread Sanitizers, and Compiler/Net Corner Cases

- **Branch:** `for-fable-and-opus/carbon2-work` (committed and pushed after every step; no engine source modified in-tree; text files only under `forge-combo29/carbon2/job29/`, every file `< 5 MB`; **no pull request opened**).

---

## 1. Step 0 and the Builds (`sha256` of Each Executable and Patch)

- **Toolchain:** `Ubuntu clang version 18.1.3 (1ubuntu1)` (`clang++-18 --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`), `Ubuntu LLD 18.1.3` (`-flto=thin -fuse-ld=lld-18 -Wl,--thinlto-jobs=1`), `-march=sapphirerapids`, `/usr/bin/llvm-symbolizer-18`, and `libc++-18-dev` (`1:18.1.3-1ubuntu1`) for `RL` and `KL`. All patches applied cleanly to `/tmp/carbon2_job29/src_*` scratch copies with `patch -p1 --fuzz=0` (`0` offset, `0` fuzz; raw compiler/linker lines in `builds.txt`).

### 1.1 Patches (`builds.txt`)

| Patch File | Target Tree | `sha256` |
|---|---|---|
| `pc_r15.patch` (reference `r15d`) | `6b98f217...` | `d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a` |
| `job17/stack_r15d_to_final.patch.txt` (`kF`) | `r15d` | `3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30` |
| `job29/P_r15d.patch.txt` (`if (emit_info)` at `search.cpp:3241`) | `r15d` -> `src_R` | `554410930faa2743395703b547802e2228042ae6e6e03e7d0b8f00d9634c58a5` |
| `job29/P_kF.patch.txt` (`if (emit_info)` at `search.cpp:3746`) | `kF` -> `src_K` | `6185ab0e589f293f1823713e739a28b6552c8dc735d659657dcd9554c0c40433` |
| `job29/C1_uci_no_stop_on_setoption.patch.txt` (drop `stop_search()` at `uci.cpp:583`) | `src_K` -> `src_C1` | `9fc3f3d5ef4d03adb112632199dbc9cda66a238fb2dfb48a1ad76763171e5c6a` |
| `job29/C2_v3_net_sticky.patch.txt` (assign `v3_active_net_` only when null at `search.cpp:3143`) | `src_K` -> `src_C2` | `e3db0ad411653ad31ae4943c409f64e72c39f87aff132f8e8d37c31d3644895e` |
| `job29/C3_node_limit_every_1024.patch.txt` (drop `local_nodes_ < node_limit_ &&` at `search.hpp:736`) | `src_K` -> `src_C3` | `09ecdeefbc26ab4d84480b628a7833cbdc6cb01eb1a9c20debe29f03be477d13` |
| `job29/C4_no_stripe_lock.patch.txt` (drop `lock_stripe` in `store_locked_fast` at `search.cpp:624-625`) | `src_K` -> `src_C4` | `6b14614310acd5fbae0f86760ebe40cf4564eee24c88548da12f903bf9313870` |

### 1.2 Executables and Step 0 (`builds.txt`, `step0_raw.txt`, `LA.epd`)

| Build | Source & Mode | Executable `sha256` | Step 0 (`bench 11 / bench 13 / go perft 5`, fresh process each, no options) |
|---|---|---|---|
| **`R`** | `r15d + P`, plain `-O3` ThinLTO | `db2f01bbf737244eba17b623d5c7736eff58d38a3cf2d4b54906d706f5b2510f` | `312866 / 862329 / 4865609` (`rc=0`, `stderr` empty) |
| **`K`** | `kF + P`, plain `-O3` ThinLTO | `7f99a0e96d34874a2ab2cf68d32da52c836fcea209fbe700656d3dbc72289224` | `312866 / 862329 / 4865609` (`rc=0`, `stderr` empty) |
| **`RS`** | `r15d + P`, `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all` | `3bedc8a3ca6ae6362312aff04e0e4bef8fe9c3e89889c29ddf17002939b3419a` | `312866 / 862329 / 4865609` (`rc=0`, `stderr` empty) |
| **`KS`** | `kF + P`, `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all` | `9ffbdd722872524d6455072acce02983c000043661d494e707fa59fa6ab750ab` | `312866 / 862329 / 4865609` (`rc=0`, `stderr` empty) |
| **`RT`** | `r15d + P`, `-O1 -g -fsanitize=thread` | `68c577cb637aa4dd8ee62100ca76f649c8ba67c5a2e36a1ad590928d2888a3d3` | `312866 / 862329 / 4865609` (`rc=0`, `stderr` empty) |
| **`KT`** | `kF + P`, `-O1 -g -fsanitize=thread` | `5978f248807f9541fad7c3d771626b936e0b403f8f3c1758eedc750910a872df` | `312866 / 862329 / 4865609` (`rc=0`, `stderr` empty) |
| **`C1`** | `kF + P + C1`, `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all` | `72c527e00f55b744d8ae55b9652905fc1a2c369d53ba7fc42a29747e4baa97c1` | *(Control build for Part B)* |
| **`C2`** | `kF + P + C2`, `-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all` | `8f4828bc71ed3f093cd95b093022f104cdc487149ce28239ff6f9ebc8e81ed23` | *(Control build for Part D)* |
| **`C3`** | `kF + P + C3`, plain `-O3` ThinLTO | `04d1987e09e1321ee0fbdbf03d14105d84af503030ed4d2b825811b92ead1da9` | *(Control build for Part A)* |
| **`C4`** | `kF + P + C4`, `-O1 -g -fsanitize=thread` | `17d4bb3e499d8a5fda9d2f33b24dc9752587d26d54456dab32d48354d272bfd7` | *(Control build for Part C)* |
| **`RL`** | `r15d + P`, plain `-O3` ThinLTO + `-stdlib=libc++` | `115dfc074ef8f8bd6c27d3e6bbc602eb02857b71bbe77af3fc550ff9523aba43` | *(Part E1 build; `bench 11 = 369996`)* |
| **`KL`** | `kF + P`, plain `-O3` ThinLTO + `-stdlib=libc++` | `f5d3c4fb13d47ae15790ace1cb33959f12e90e8c7802445f3d7e520f02da0530` | *(Part E1 build; `bench 11 = 369996`)* |

- **`LA.epd` (`100` FENs):** Committed before Part A (`d184305fc`): `LA[1..60]` = the `60` roots of `job21/workload_T_60_roots.txt` in order; `LA[61..100]` = the `40` FENs of searches `150, 300, ..., 6000` of `T` (`6070 / 26711499 / 937e1660561173af` verified during generation).

---

## 2. Standalone Prediction Graded (`prediction_job29.txt`, Commit `3170b1b78`)

`forge-combo29/carbon2/job29/prediction_job29.txt` was committed **alone** (`1` file changed in commit `3170b1b78`) and pushed after Step 0, `builds.txt`, and `LA.epd`, and before Part A started. It was never edited afterwards and contains no date, time, or commit id.

| Prediction Item | Pre-Committed Prediction | Measured Result | Grade |
|---|---|---|---|
| `KA` (`K` vs `R`, `2,700` rows) | `[0, 0]` differing rows | `0` differing rows | **MET** |
| `KA2` (`K` vs `R`, `540` rows, `MultiPV 2`) | `[0, 0]` differing rows | `0` differing rows | **MET** |
| `KB` (`SB` & `SB2`, masked lines) | `[0, 0]` differing lines | `0` differing lines | **MET** |
| `KC` (`SC` `T=2, 4` across `RS, KS, RT, KT`) | `[0, 0]` new reports & `[0, 0]` bad bestmoves | `0` reports, `480/480` legal bestmoves | **MET** |
| `KD` (`SD` 7-step net switching, masked) | `[0, 0]` differing lines | `0` differing lines | **MET** |
| `KE1` (`KL` vs `RL` under `-stdlib=libc++`) | `[0, 0]` differing rows/traces | `0` differing rows/traces/lines | **MET** |
| `KE2` (`net768` copy with `hidden=784`) | `[0, 0]` differing lines | `0` differing lines | **MET** |
| Sanitizer report counts (`KS, RS, KT, RT`) | `KS=0, RS=0, KT=0, RT=0` | `KS=0, RS=0, KT=0, RT=0` | **MET** |
| Controls (`CA, CB, CC, CD, CE1, CE2`) | All `6` **`FIRES`** | All `6` **`FIRES`** | **MET** |
| Part readings (`A, B, C, D, E`) | All **`KEEPS`** | All **`KEEPS`** | **MET** |

---

## 3. Master Verification Table (Parts A to E)

| Part | Builds Compared (+ Control) | Runs | Rows or Lines | `K` Differs from `R` (`KL` vs `RL` in `E1`) | Sanitizer Reports (`kF` build / `r15d` build) | Control Fired | Reading |
|---|---|---:|---|---:|---|---|---|
| **Part A**<br>(`KA`, `KA2`, `CA`) | `K` vs `R` (`MultiPV 1` & `2`);<br>ctrl `C3` vs `R` | `5` | `2,700` rows (`KA`) + `540` rows (`KA2`);<br>`2,700` rows (`CA`) | **`0 / 3,240` rows** | n/a (plain builds) | **YES** (`CA`: `P`'s `n` differs on `1,461 / 2,700` rows, incl. `1,273 / 1,300` non-`1024` `go nodes` rows) | **`KEEPS`** |
| **Part B**<br>(`SB`, `SB2`, `CB`) | `K, R, KS, RS` (`SB` & `SB2`);<br>ctrl `C1` (`SB2`) | `21`<br>(`4` `SB` + `12` `SB2` + `5` `C1`) | `899` lines/build (`SB`); `10`-line final search/run (`SB2`) | **`0 / 899` lines (`SB`);**<br>**`0 / 10` lines (`SB2`)** | **`0 / 0`** (`KS` `0` across `6` runs / `RS` `0` across `6` runs) | **YES** (`CB`: `5 / 5` `C1` runs hit ASan `heap-use-after-free` in `0.300s`) | **`KEEPS`** |
| **Part C**<br>(`SC` `T=2,4`, `CC`) | `KS, RS, KT, RT` (`Threads 2` & `4`);<br>ctrl `C4` (`Threads 4`) | `9`<br>(`8` `SC` + `1` `C4`) | `480` bestmoves (`60` x `8` runs; `~900` UCI lines/run) | **`0` illegal/missing bestmoves** (`480 / 480` legal, `0` timeouts) | **`0 / 0`** (`KS` `0`, `KT` `0` / `RS` `0`, `RT` `0`) | **YES** (`CC`: `C4` hit TSan `data race` in `0.76s` at `probe_locked_fast` vs `store_locked_fast`) | **`KEEPS`** |
| **Part D**<br>(`SD`, `CD`) | `K, R, KS, RS` + `K_only_B`;<br>ctrl `C2` (`SD`) | `6` | `891` lines/build (`SD`, `35` searches + `7` evals); `5` searches (`K_only_B`) | **`0 / 891` lines** (`(1)=(3)=(6)=(7)`, `(2)=(5)`, `(4)=K_only_B`) | **`0 / 0`** (`KS` `0` / `RS` `0`) | **YES** (`CD`: `C2` differed on `107` search lines in steps `(2)-(3)` + hit ASan `heap-use-after-free` in step `(4)`) | **`KEEPS`** |
| **Part E1**<br>(`-stdlib=libc++`) | `KL` vs `RL`;<br>ctrl `RL` `bench 11 != 312866` | `8` | `3` Step-0 cmds + `T20` (`924` searches, `13,800+` UCI lines/build) | **`0` diffs** (`369996 / 1033864 / 4865609`; `T20` `924` searches, `0` row/line diffs) | n/a (plain `-stdlib=libc++`) | **YES** (`RL` `bench 11 = 369996 != 312866`) | **`KEEPS`** |
| **Part E2**<br>(`hidden = 784`) | `K` vs `R` on `w=784` copy;<br>ctrl unchanged copy | `6` | `2` orderings (`NNUEArch=false` & `true`) + `1` good-copy load per build | **`0` differing lines or exit codes** | n/a (plain builds) | **YES** (unchanged copy loaded & activated `checksum 30ab43b4ba5db5f3` on both) | **`KEEPS`** |

---

## 4. Detailed Findings, Required Sub-Items, and Control Traces (`0` Differences / Reports on `K`, `KS`, `KT`, `KL`)

### 4.1 Differences or Sanitizer Reports on `kF` Builds (`K`, `KS`, `KT`, `KL`)
- **None (`0` differences between `K` and `R` or between `KL` and `RL` across any known answer, and `0` sanitizer reports on `KS`, `RS`, `KT`, and `RT` across all runs, including Step 0).**

### 4.2 Part A Required Counts (`partA_summary_raw.txt`, `partA_KA_R.rows.txt`, `partA_CA_C3.rows.txt`)
1. **On `R`, `go nodes N` rows where `P`'s `n == N` (`1,700` total `go nodes` rows = `100` `LA` positions x `17` `N` values):**
   - **`P`'s `n == N` on `1,675 / 1,700` rows.**
   - **The exact `25` rows where `P`'s `n != N` (all natural depth-64 mate completions or already-mated root):**
     - **`LA005`** (`1k6/4R3/3p2KN/1p1P4/6B1/P2P2R1/7P/8 b - - 0 40`, `2` rows): `N = 20480` and `N = 50000` both finish all `64` root depths at **`n = 20112`** (`depth=64`, `score=mate -2`, `bestmove b8a8`).
     - **`LA040`** (`3B3r/5K2/2k2P2/P2pP3/8/8/7q/8 b - - 0 60`, `6` rows): `N in {4095, 4096, 4097, 20000, 20480, 50000}` all finish all `64` root depths at **`n = 4056`** (`depth=64`, `score=mate 2`, `bestmove h2h7`).
     - **`LA072`** (`1Knk4/8/n2b1p1p/3b3P/8/5P2/8/8 w - - 3 56`, `17` rows, all `17` `N` values): White is already checkmated at root (`0` legal moves); `search_root` returns early before `P`'s print with **`nodes = 0`** (`p_n = -`, `depth=64`, `score=mate 0`, `bestmove 0000`).
   - `K` matches `R` identically on all `1,675` `n == N` rows, all `25` `n != N` rows, all `1,000` `go softnodes` rows, and all `540` `MultiPV 2` rows (`KA2`).
2. **Control `CA` (`C3` vs `R`):**
   - Out of `1,300` `go nodes` rows with `N % 1024 != 0` (`13` such `N` values x `100` positions), **`1,273 / 1,300` differ in `P`'s `n`** (`0 / 400` differ when `N % 1024 == 0`, plus `188 / 1,000` `go softnodes` rows differ where the `4 * S` hard cap was hit between multiples of `1,024`, for **`1,461 / 2,700` total differing rows**). Note that on small `N` (`1, 2, 3, 100`), `C3` stops at a root-iteration boundary (e.g., `LA001` `go nodes 1`: `R` `n = 1` vs `C3` `n = 55` after depth 1) because `search_root` checks `should_stop()` between depths; for larger non-multiples (`1000, 1023, 1025, 2047, 2049, 4095, 4097, 20000, 50000`), `C3` stops at the next multiple of `1,024` (`1024, 2048, 3072, 4096, 5120, 20480, 50176`). The `27` non-differing `N % 1024 != 0` rows are `LA072`'s `13` checkmated rows (`0` nodes), `LA005` `N=50000` (`n=20112`), `LA040` `N in {4095, 4097, 20000, 50000}` (`n=4056`), and `9` rows where a root iteration ended at exact node `N`.

### 4.3 Part B, C, D, and E Specific Verifications & Controls
- **Part B (`partB_summary_raw.txt`, `partB_CB_C1_uci_and_san_raw.txt`):**
  - On `SB2`, `K`, `R`, `5x RS`, and `5x KS` (`12 / 12` runs) all printed `bestmove` of `go infinite` before the first `readyok` (because `uci.cpp:583` `stop_search()` joins the infinite search before `Hash 2` resizes the TT) and all `12` produced the exact same `10` masked lines on the trailing `LA[1]` `go nodes 20000` search (`info string softnodes nodes 20000`, `bestmove h3e6`).
  - Control `CB` (`C1` without `stop_search()` at `uci.cpp:583`): **`5 / 5` runs crashed with `AddressSanitizer: heap-use-after-free` in `0.300s`** inside `forge::TranspositionTable::probe_owned_fast` (`search.hpp:246:28`) / `store_owned_fast` while `T0` resized the TT.
- **Part C (`partC_summary_raw.txt`, `partC_CC_C4_uci_and_san_raw.txt`):**
  - All `8` runs (`RS_T2, KS_T2, RT_T2, KT_T2, RS_T4, KS_T4, RT_T4, KT_T4`) produced `60 / 60` `python-chess`-verified legal `bestmove`s in `2.08s–11.40s` with `0` sanitizer bytes.
  - Control `CC` (`C4` without `lock_stripe` in `store_locked_fast`): fired **`WARNING: ThreadSanitizer: data race` in `0.76s`** between `probe_locked_fast` (`search.cpp:554:19` on `T3`) and `store_locked_fast` (`search.cpp:647:22` on `T2`).
- **Part D (`partD_summary_raw.txt`, `partD_SD_uci_and_san_raw.txt`, `partD_CD_C2_uci_and_san_raw.txt`):**
  - **`net512` (`Net B`) verbatim `NNUE v3 loaded` line:**
    `info string NNUE v3 loaded: v3 /tmp/carbon2_work/net512.fnn3 hidden 512 king_buckets 8 mirrored output_buckets 8 standalone eval_scale 400 checksum fdff70de72e4ca82 max|w1| 64 max|b1| 96 max|w2| 16 kernel avx512`
  - On `SD`, `R, K, RS, KS` all emitted `891` identical masked lines (`0` sanitizer bytes); in `K`, searches of steps `(1), (3), (6), (7)` are identical, `(2)` and `(5)` are identical, and `(4)` equals fresh `K` loading only `net512`.
  - Control `CD` (`C2` sticky `v3_active_net_`): differed on **`107` search lines** across steps `(2)` and `(3)` (first diff at step `(2)` search `#1` line `#1`, still evaluating with `net768` when `NNUEArch` was `false`) and aborted on step `(4)` search `#1` with **`AddressSanitizer: heap-use-after-free`** in `forge::nnue::v3::prepare` (`nnue_v3.cpp:816:33`) reading the freed `net768` `Net` deleted by `nnue::v3::load(net512)`.
- **Part E (`partE_summary_raw.txt`, `partE_E1_uci_raw.txt`, `partE_E2_uci_raw.txt`):**
  - **E1 (`-stdlib=libc++`):** `RL`'s `bench 11 = 369996` (`!= 312866`, matching the PC's `llvm-mingw` `libc++` count `369996`, so the control fired). `KL` equaled `RL` on `bench 11` (`369996`), `bench 13` (`1033864`), `go perft 5` (`4865609`), and across all `15` games / `924` searches of `T20` (`info_nodes_sum = 10115779`, `p_nodes_sum = 17325074`, `trace_info = d399f837ecd5f286`, `trace_pn = 53472cc32afcb8a2`, `0` search-row diffs, `0` masked UCI line diffs).
  - **E2 (`hidden = 784` at offset `20` of `net768` copy):** Both `K` and `R` printed
    `info string ERROR NNUE v3: /tmp/carbon2_job29/net768_w784.fnn3: hidden must be a multiple of 32 in 32..1024, got 784`
    and behaved identically at the next `isready` (`readyok` with `rc = 0` when `NNUEArch` is `false`; repeat error + fail-loud exit `rc = 2` when `NNUEArch` is `true`). The unchanged copy loaded and activated cleanly on both (`checksum 30ab43b4ba5db5f3`).

---

## WHAT THIS CHECK CANNOT SEE

The PC's clang 23 for Windows and its MinGW libstdc++, its Zen 5 processor, its trained nets, positions outside LA and T20, more than 4 threads, speed, and thread interleavings these runs did not produce: a clean ThreadSanitizer run proves nothing about schedules it did not see.

---

## Facts, Suspicions, What I Did Not Do, What I Am Not Sure About, Model Name, Stamps & Status

### Facts (Directly Evidenced by Job 29 Raw Files)
1. **All Five Parts (`A`, `B`, `C`, `D`, `E1/E2`) Read `KEEPS` with Every Positive Control Firing:** Across `3,240` Part-A search rows (`KA` + `KA2`), `SB` + `SB2` (`Part B`), `8` ASan/UBSan + TSan multi-threaded `SC` runs at `Threads 2` and `4` (`Part C`), `SD` 7-step net switching (`Part D`), `-stdlib=libc++` `RL` vs `KL` (`Part E1`), and `hidden = 784` net rejection (`Part E2`), `kF` produced **`0` behavioral differences** from `r15d` and **`0` sanitizer reports**, while all `6` controls (`CA`, `CB`, `CC`, `CD`, `CE1`, `CE2`) fired cleanly.
2. **Exact Node-Stop Equivalence Under `go nodes` and `go softnodes`:** Patch `P` exposed the exact final `result.nodes` of every search; `kF`'s `fast_single_node_stop_` (`local_nodes_ < node_limit_ && (local_nodes_ & 1023U) != 0`) stopped at the exact same node count, score, PV, and bestmove as `r15d` on all `2,700` `LA` searches (`1,675 / 1,700` `go nodes` rows stopping at `n == N` and `25 / 1,700` finishing mate/checkmate early at the identical `n < N`).
3. **Zero Added Standard-Library `std::sort` Sensitivity in `kF`:** Switching from `libstdc++` (`bench 11 = 312866`, `T20 = 824` searches) to LLVM `libc++` (`bench 11 = 369996`, `T20 = 924` searches) changed equal-score tie order identically in `r15d` (`RL`) and `kF` (`KL`), proving `kF` introduces no additional library-order dependence.

### Suspicions
1. Because `uci.cpp` funnels every `setoption`, `ucinewgame`, `position`, `go`, and `bench` command through `stop_search()` on the single UCI loop thread before mutating `Searcher` or `nnue::v3` globals, `store_owned_fast`'s reliance on table stability during a 1-thread search and `v3_active_net_`'s per-search refresh at `search.cpp:3143` cannot be violated through the UCI protocol unless `stop_search()` itself is removed (as in `C1`) or the per-search refresh is removed (as in `C2`).

### What I Did Not Do
- Did not modify any engine source file in-tree, commit any binary or `.fnn3` file, switch branches, or open a pull request.
- Did not test `Threads > 4`, builds without AVX-512, `#else` branches of non-PC `-D` switches, or wall/CPU speed in this job.

### What I Am Not Sure About
- Whether rare OS thread interleavings outside the schedules explored by `RT_T2`, `KT_T2`, `RT_T4`, and `KT_T4` on `SC` could expose any benign or non-benign race at higher thread counts (`Threads > 4`), as noted in `WHAT THIS CHECK CANNOT SEE`.

### Model Name
- `Gemini 4 Carbon`

### First & Last Lines of `forge-combo29/carbon2/job29/stamps.txt`
- **First line:** `Thu Nov 19 05:59:27 PM UTC 2026 | job 29 received (FABLE_TO_carbon2_29.md); claim committed`
- **Last line:** `Thu Nov 19 06:27:57 PM UTC 2026 | All Job 29 experiments complete; writing REPORT_carbon2_job29.md`

### Pre-Commit `git status --short && ls -R forge-combo29/carbon2/job29` (Literal Last Command Before Report Commit)

```text
 M forge-combo29/carbon2/job29/stamps.txt
?? forge-combo29/carbon2/job29/REPORT_carbon2_job29.md
forge-combo29/carbon2/job29:
builds.txt
C1_uci_no_stop_on_setoption.patch.txt
C2_v3_net_sticky.patch.txt
C3_node_limit_every_1024.patch.txt
C4_no_stripe_lock.patch.txt
LA.epd
partA_CA_C3.rows.txt
partA_KA2_K.rows.txt
partA_KA2_R.rows.txt
partA_KA_K.rows.txt
partA_KA_R.rows.txt
partA_summary_raw.txt
partB_CB_C1_uci_and_san_raw.txt
partB_SB2_uci_and_san_raw.txt
partB_SB_uci_and_san_raw.txt
partB_summary_raw.txt
partC_CC_C4_uci_and_san_raw.txt
partC_SC_T2_uci_and_san_raw.txt
partC_SC_T4_uci_and_san_raw.txt
partC_summary_raw.txt
partD_CD_C2_uci_and_san_raw.txt
partD_SD_uci_and_san_raw.txt
partD_summary_raw.txt
partE_E1_uci_raw.txt
partE_E2_uci_raw.txt
partE_summary_raw.txt
P_kF.patch.txt
P_r15d.patch.txt
prediction_job29.txt
REPORT_carbon2_job29.md
stamps.txt
step0_raw.txt
```
