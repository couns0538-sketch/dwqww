# Job 39 Report — `carbon2` (`THE GROK PORTS` onto `r15d + v3`)

## Executive First Lines (`(1)` Step 0, `(2)` Prediction Graded, `(3)` Part P, `(4)` Part Q)

- **(1) Step 0 (`40a36dfb346d24eb87a90a5e022bb1e62620ee07`, `step0_raw.txt`, `builds.txt`):**
  - `r15d + v3` source tree (`/tmp/carbon2_job36/tpl_r15d_v3`, matching PC `forge/r15dsg`, LF line endings): `0 == 0` CRLF in all four files; `src/search.cpp` `sha256` PASS (`174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4`), `src/uci.cpp` PASS (`2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013`), `src/board.cpp` PASS (`2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf`), `include/forge/board.hpp` PASS (`5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77`).
  - Reused Job 36/37 SP-PGO executable (`/tmp/carbon2_job36/bld_sp_sgr15v/forge`, `sha256` PASS `bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810 == bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810`) and clean Release `r15d + v3` executable (`/tmp/carbon2_job39/bld_base_v3/forge`, `sha256 = 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`) both met **every OFF number**: no-option `bench 11` PASS (`312866 == 312866`), `bench 13` PASS (`862329 == 862329`), `perft 5` PASS (`4865609 == 4865609`); `PC20` `bench 11` PASS (`278024 == 278024`), `bench 13` PASS (`587276 == 587276`); `Set A line L` records PASS (`26741 == 26741`), nodes PASS (`107124743 == 107124743`), `sha256` PASS (`d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`); `n[1..60] line L` records PASS (`8449 == 8449`), searches PASS (`8482 == 8482`), nodes PASS (`36688357 == 36688357`), `sha256` PASS (`b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15`). Switch-off reference depth-12 sums (`PC20`, built-in eval, `Threads 1`, `Hash 16`, `ucinewgame` + `isready` before every search): `OFF_O_d12.rows.txt` (`200` FENs) = **`8,315,168`** (`0 == 0` diffs vs reused SP-PGO exe); `OFF_G_d12.rows.txt` (`353` FENs) = **`17,611,204`**.
- **(2) Prediction Graded (`prediction_job39.txt`, committed ALONE in `fcb60cc9bdc06782c977429ec7683de7722b18a7`, `1 file changed`, `Fri Nov 20 01:27:56 PM UTC 2026`, before Part P's first build at `01:30:50 PM UTC`, never edited):**
  - **(1) Ports passing all OFF numbers with switch off:** Predicted `6`; observed `6` (`6 == 6`) -> **TRUE**.
  - **(2) Bundle all-six-on `O` depth-12 node sum / all-off `O` sum (`PC20`, built-in evaluation):** Predicted `1.00`, wrong outside `[0.91, 1.10]`; observed `8,035,170 / 8,315,168 = 0.966327` (inside `[0.91, 1.10]`) -> **TRUE**.
  - **(3) Bundle checking build (`ASan + UBSan + _GLIBCXX_ASSERTIONS`) with all six on reports nothing on `Set C line L` and `n[1..20] line L`:** Predicted `yes`; observed `0 == 0` `stderr_bytes` and `0 == 0` exit code on both (`Set C line L` `51,545,138` nodes, `n[1..20] line L` `9,239,955` nodes) -> **TRUE**.
  - **Score: `3` of `3` TRUE.**
- **(3) Part P Summary (`P1..P6`, committed one port per commit `727861e7b`, `9cec5db53`, `84db72e58`, `cc04c088c`, `1b1cfc578`, `70a24f0c8`):**
  - **Every one of the 6 ports passed all 12 OFF checks (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`, `278024 == 278024`, `587276 == 587276`, `26741 == 26741`, `107124743 == 107124743`, `d5b52710... == d5b52710...`, `8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`) plus `O` d12 off (`8315168 == 8315168`, `0 == 0` diffs).**
  - Switch-ON known answers (`PC20`, built-in eval):
    - **`P1_K4_093` (`IdeaK4`):** `O` sum `8,080,229` (`200/200` differ), `G` sum `17,071,973` (`349/353` differ), `Set A line L` `25,083` records / `99,000,607` nodes / `30eeceb2c8d3b47e4d6d4d9a76b9d2dafccf8b83a5623a9b6586fc9ae17c9c96`, port notes `2`.
    - **`P2_S32_074` (`IdeaS32`):** `O` sum `8,339,315` (`200/200` differ), `G` sum `17,534,953` (`345/353` differ), `Set A line L` `26,842` records / `108,166,350` nodes / `81373ea10d0e0b8678906d694391d36b66c92564ce7fab0a1a0e4e94fb612a6f`, port notes `3`.
    - **`P3_B1_030` (`IdeaB1`):** `O` sum `8,548,042` (`200/200` differ), `G` sum `16,916,340` (`353/353` differ), `Set A line L` `26,366` records / `105,800,976` nodes / `703cbabe40efb32ac0782f2a84a984bc937f11b597ed216da4a75438daa0c2fd`, port notes `2`.
    - **`P4_S13_016` (`IdeaS13`):** `O` sum `8,077,984` (`200/200` differ), `G` sum `17,460,346` (`344/353` differ), `Set A line L` `26,212` records / `104,043,062` nodes / `1f50071a233c8f86fab955f95eda851cc594090b1ffdf150d6debd87337077cd`, port notes `4`.
    - **`P5_S10_081` (`IdeaS10`, seat `081` chosen per Job 38):** `O` sum `8,314,153` (`17/200` differ), `G` sum `17,536,908` (`98/353` differ), `Set A line L` `26,130` records / `104,621,754` nodes / `429d5042b167d0b350399308014a755d057043e3cfa5561db2ee1e70e8ffd60e`, port notes `4` (plus 1 choice line).
    - **`P6_B8_078` (`IdeaB8`):** `O` sum `8,262,696` (`200/200` differ), `G` sum `17,342,378` (`282/353` differ), `Set A line L` `25,818` records / `105,263,539` nodes / `36da9820f07dd4e851b8ef64a253b011969c6d9e39f2cd5c380541ef208b7da8`, port notes `4`.
- **(4) Part Q Summary (`bundle_grok.patch.txt`, `1,102` lines, `sha256 = d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec`, commit `a3929857a22c06d1158be04710f7ca36a46c3afe`):**
  - **All switches OFF:** Passed every OFF number (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`, `278024 == 278024`, `587276 == 587276`, `Set A line L` `26741 == 26741` / `107124743 == 107124743` / `d5b52710... == d5b52710...`, `n[1..60] line L` `8449 == 8449` / `8482 == 8482` / `36688357 == 36688357` / `b6bf7600... == b6bf7600...`, `O` d12 off `8315168 == 8315168` with `0 == 0` differing positions).
  - **Per-switch identity (`O` d12, each switch ON alone vs single port P-c):** `200 == 200` position-by-position equal (`nodes`, `bestmove`, `score`) for all 6 switches (`IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaS13`, `IdeaS10`, `IdeaB8`).
  - **All six ON together (`PC20`, built-in eval):** `O` d12 sum = **`8,035,170`** (`200/200` differ, ratio `0.966327`); `G` d12 sum = **`16,356,627`** (`353/353` differ, ratio `0.928763`); `Set A line L` = **`27,991` records**, **`28,117` searches**, **`111,242,459` nodes**, `sha256 = c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce` (`0` thrown).
  - **Checking build (`-O1 -g -fsanitize=address,undefined -fno-sanitize-recover=all -D_GLIBCXX_ASSERTIONS`, Job 37 harness `job37/run_partA_checking.py` used unchanged):** No-option pins `312866 == 312866`, `4865609 == 4865609`, `stderr_bytes` `0 == 0`; with all six ON (`PC20`), `Set C line L` (`100` attempts) `stderr_bytes` PASS (`0 == 0`) & Release `sha256` match PASS (`9f9b7e19d465f265ee5ace8c0f90ac733cd55245c97b152f4016a1230ab6b735 == 9f9b7e19d465f265ee5ace8c0f90ac733cd55245c97b152f4016a1230ab6b735`), and `n[1..20] line L` (`20` attempts, `net768.fnn3`) `stderr_bytes` PASS (`0 == 0`) & Release `sha256` match PASS (`0d794e83ca5d2f34197556fd9d78733500a328f56a56a17a09edc28b238c0ac7 == 0d794e83ca5d2f34197556fd9d78733500a328f56a56a17a09edc28b238c0ac7`).
  - **Q4 Table:** Full 6-row PC switch table in Section 4.4 below and `forge-combo29/carbon2/job39/q4_switch_table.md`.

---

## WHAT THIS CANNOT SEE

The PC's net, Windows, and strength: node counts say that a switch acts and what it costs, not whether it gains. No
match in this job; the PC plays the bundle with its own net.

---

## 1. Step 0 — `r15d + v3` Tree, Reused Job 36 Exe & Clean Release Exe OFF Numbers (`step0_raw.txt`)

- **Commit:** `40a36dfb346d24eb87a90a5e022bb1e62620ee07` (`2026-11-20 13:26:54 +0000`)
- **Reused Job 36/37 SP-PGO executable declared:** `/tmp/carbon2_job36/bld_sp_sgr15v/forge` (`sha256 = bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810`, `forge.profdata` `sha256 = e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc`).
- **Clean Release `r15d + v3` executable (no profile step, Job 36 Release flags):** `/tmp/carbon2_job39/bld_base_v3/forge` (`sha256 = 09d6fe1ea4dcbea333f297962dede9521a2a6ea49d5cc48b2f4f38ae8078f84c`).

```text
  src/search.cpp CRLF count                   : PASS (0 == 0)
  src/search.cpp sha256                       : PASS (174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4 == 174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4)
  src/uci.cpp CRLF count                      : PASS (0 == 0)
  src/uci.cpp sha256                          : PASS (2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013 == 2c00871f131d1816cabd7011e5bc345902a501f839c08f307db5b0f09cf52013)
  src/board.cpp CRLF count                    : PASS (0 == 0)
  src/board.cpp sha256                        : PASS (2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf == 2da64b7d06f608a5351b7dd5e75d19582cd80a7153b0c1ae1ae6dc2e28b8f3cf)
  include/forge/board.hpp CRLF count          : PASS (0 == 0)
  include/forge/board.hpp sha256              : PASS (5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77 == 5fa32c92d35d1000fb1e111985469f4beb17dd11d9c23bab03fb39311a109d77)
  reused exe sha256 vs recorded               : PASS (bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810 == bfabc2841504b4866d201546777a0912cebd53ad4d5c213f5206f7862e611810)
  reused profdata sha256 vs recorded          : PASS (e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc == e22424266d8f829892498c15d659f8fdbd3068ad9e5a3fa652dc4aedcc863bcc)
  clean_rel_r15d_v3 no-option bench 11        : PASS (312866 == 312866)
  clean_rel_r15d_v3 no-option bench 13        : PASS (862329 == 862329)
  clean_rel_r15d_v3 no-option perft 5         : PASS (4865609 == 4865609)
  clean_rel_r15d_v3 PC20 bench 11             : PASS (278024 == 278024)
  clean_rel_r15d_v3 PC20 bench 13             : PASS (587276 == 587276)
  clean_rel_r15d_v3 Set A line L records      : PASS (26741 == 26741)
  clean_rel_r15d_v3 Set A line L nodes        : PASS (107124743 == 107124743)
  clean_rel_r15d_v3 Set A line L sha256       : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  clean_rel_r15d_v3 n[1..60] line L records   : PASS (8449 == 8449)
  clean_rel_r15d_v3 n[1..60] line L searches  : PASS (8482 == 8482)
  clean_rel_r15d_v3 n[1..60] line L nodes     : PASS (36688357 == 36688357)
  clean_rel_r15d_v3 n[1..60] line L sha256    : PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)
  OFF O position count                        : PASS (200 == 200)
  OFF G position count                        : PASS (353 == 353)
  OFF O clean_rel vs reused_sp_pgo diffs      : PASS (0 == 0)
```

---

## 2. Prediction Graded (`prediction_job39.txt`, commit `fcb60cc9bdc06782c977429ec7683de7722b18a7`)

| Item | Prediction (`fcb60cc9b`, `01:27:56 PM UTC`, `1 file changed`) | Observed (`P1..P6_summary.txt`, `partQ_summary.txt`) | Comparison | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| `(1)` Ports passing all OFF numbers with switch off | `6` | `6` (`P1_K4_093`, `P2_S32_074`, `P3_B1_030`, `P4_S13_016`, `P5_S10_081`, `P6_B8_078`) | PASS (`6 == 6`) | **TRUE** |
| `(2)` Bundle all-six-on `O` d12 node sum / all-off `O` sum | `1.00` (wrong outside `[0.91, 1.10]`) | `8,035,170 / 8,315,168 = 0.966327` | PASS (`0.91 <= 0.966327 <= 1.10`) | **TRUE** |
| `(3)` Checking build with all six on reports nothing on `Set C line L` and `n[1..20] line L` | `yes` | `Set C line L` `stderr_bytes = 0`, `n[1..20] line L` `stderr_bytes = 0` (`exit_code = 0` on both) | PASS (`0 == 0` and `0 == 0`) | **TRUE** |

---

## 3. Part P — Six Ports Onto `r15d + v3`, One at a Time (`P1..P6`)

### 3.1 Choice of Seat `081` for `P5` (`IdeaS10`)
- Per `FABLE_TO_carbon2_39.md` (`lines 109-110`), seat **`081`** was ported because Job 38 proved `081` faithfully implements `IDEAS.md` S10 (`Evaluator::pawn_structure_cp`, 4-ply non-pawn/non-capture shuffle check, 1-ply `restricted_quiet_score` probe for the pawn-ahead side, `defender_holds` reversal/repetition check, and `896/1024` pull toward `0`), whereas `031` (`+0.00 +/- 0.00 Elo`) and `s10_variant` (`-33.08 +/- 10.12 Elo`) omitted pawn-structure evaluation and left `defender_holds` tautological when `stm == winner`.
- In `P5_S10_081`, `081`'s dead `v3_state_->stack[ss->ply + 5].valid = false` was replaced with `v3_state_->valid_flags[static_cast<std::size_t>(ss->ply + 5)] = 0` in `restricted_quiet_score` and after `unmake_null_move` in `idea_s10_applies` (`port_notes.txt:20-21`), and verified under `net768.fnn3` in Q3 (`BUNDLE_CHK_ALL_ON_n20_L.rows.txt`, `20` games, `2,103` records, `9,239,955` nodes, `0 == 0` `stderr_bytes`, bit-for-bit equal to Release `0d794e83ca5d2f34197556fd9d78733500a328f56a56a17a09edc28b238c0ac7`) as well as `-DFORGE_NNUE_V3_VERIFY=1` (`src/search.cpp:3412`) with zero fresh-accumulator reference mismatches.

### 3.2 Per-Port OFF Numbers (`P1_K4_093_summary.txt` .. `P6_B8_078_summary.txt`)

Every port applied cleanly to fresh `r15d + v3` (`git apply --check -p1`: `PASS (0 == 0)`) and met every OFF check with its switch off:

| Port (`commit`) | Patch File (`sha256` prefix) | No-Opt `bench 11 / 13 / perft 5` | `PC20` `bench 11 / 13` | `Set A line L` (`records / nodes / sha256`) | `n[1..60] line L` (`records / searches / nodes / sha256`) | `O` d12 OFF (`sum / diffs`) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`P1_K4_093`** (`727861e7b`) | `P1_K4_093.patch.txt` (`05cf682e...`) | PASS (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`) | PASS (`278024 == 278024`, `587276 == 587276`) | PASS (`26741 == 26741`, `107124743 == 107124743`, `d5b52710... == d5b52710...`) | PASS (`8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`) | PASS (`8315168 == 8315168`, `0 == 0`) |
| **`P2_S32_074`** (`9cec5db53`) | `P2_S32_074.patch.txt` (`4bd067f2...`) | PASS (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`) | PASS (`278024 == 278024`, `587276 == 587276`) | PASS (`26741 == 26741`, `107124743 == 107124743`, `d5b52710... == d5b52710...`) | PASS (`8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`) | PASS (`8315168 == 8315168`, `0 == 0`) |
| **`P3_B1_030`** (`84db72e58`) | `P3_B1_030.patch.txt` (`e551a303...`) | PASS (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`) | PASS (`278024 == 278024`, `587276 == 587276`) | PASS (`26741 == 26741`, `107124743 == 107124743`, `d5b52710... == d5b52710...`) | PASS (`8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`) | PASS (`8315168 == 8315168`, `0 == 0`) |
| **`P4_S13_016`** (`cc04c088c`) | `P4_S13_016.patch.txt` (`94440264...`) | PASS (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`) | PASS (`278024 == 278024`, `587276 == 587276`) | PASS (`26741 == 26741`, `107124743 == 107124743`, `d5b52710... == d5b52710...`) | PASS (`8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`) | PASS (`8315168 == 8315168`, `0 == 0`) |
| **`P5_S10_081`** (`1b1cfc578`) | `P5_S10_081.patch.txt` (`b38dba36...`) | PASS (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`) | PASS (`278024 == 278024`, `587276 == 587276`) | PASS (`26741 == 26741`, `107124743 == 107124743`, `d5b52710... == d5b52710...`) | PASS (`8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`) | PASS (`8315168 == 8315168`, `0 == 0`) |
| **`P6_B8_078`** (`70a24f0c8`) | `P6_B8_078.patch.txt` (`b8bf053c...`) | PASS (`312866 == 312866`, `862329 == 862329`, `4865609 == 4865609`) | PASS (`278024 == 278024`, `587276 == 587276`) | PASS (`26741 == 26741`, `107124743 == 107124743`, `d5b52710... == d5b52710...`) | PASS (`8449 == 8449`, `8482 == 8482`, `36688357 == 36688357`, `b6bf7600... == b6bf7600...`) | PASS (`8315168 == 8315168`, `0 == 0`) |

### 3.3 Per-Port Switch-ON Known Answers (`PC20`, Built-In Evaluation) & Port Notes Counts

Switch-off reference sums: `OFF_O_d12 = 8,315,168` (`200` FENs), `OFF_G_d12 = 17,611,204` (`353` FENs), `Set A line L = 26,741` records / `107,124,743` nodes / `d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2`.

| Port | Switch (`true`) | `O` d12 Sum (`delta` vs OFF) | `O` Differing (`nodes_differ`) | `G` d12 Sum (`delta` vs OFF) | `G` Differing (`nodes_differ`) | `Set A line L` (`records / searches / nodes / thrown`) | `Set A line L` `record_text_sha256` | `port_notes.txt` Lines |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`P1_K4_093`** | `IdeaK4` | `8,080,229` (`-234,939`) | `200 / 200` (`200`) | `17,071,973` (`-539,231`) | `349 / 353` (`349`) | `25,083 / 25,202 / 99,000,607 / 0` | `30eeceb2c8d3b47e4d6d4d9a76b9d2dafccf8b83a5623a9b6586fc9ae17c9c96` | `2` |
| **`P2_S32_074`** | `IdeaS32` | `8,339,315` (`+24,147`) | `200 / 200` (`200`) | `17,534,953` (`-76,251`) | `345 / 353` (`345`) | `26,842 / 26,968 / 108,166,350 / 0` | `81373ea10d0e0b8678906d694391d36b66c92564ce7fab0a1a0e4e94fb612a6f` | `3` |
| **`P3_B1_030`** | `IdeaB1` | `8,548,042` (`+232,874`) | `200 / 200` (`200`) | `16,916,340` (`-694,864`) | `353 / 353` (`353`) | `26,366 / 26,495 / 105,800,976 / 0` | `703cbabe40efb32ac0782f2a84a984bc937f11b597ed216da4a75438daa0c2fd` | `2` |
| **`P4_S13_016`** | `IdeaS13` | `8,077,984` (`-237,184`) | `200 / 200` (`200`) | `17,460,346` (`-150,858`) | `344 / 353` (`344`) | `26,212 / 26,339 / 104,043,062 / 0` | `1f50071a233c8f86fab955f95eda851cc594090b1ffdf150d6debd87337077cd` | `4` |
| **`P5_S10_081`** | `IdeaS10` | `8,314,153` (`-1,015`) | `17 / 200` (`17`) | `17,536,908` (`-74,296`) | `98 / 353` (`98`) | `26,130 / 26,245 / 104,621,754 / 0` | `429d5042b167d0b350399308014a755d057043e3cfa5561db2ee1e70e8ffd60e` | `4` (+ `1` choice line) |
| **`P6_B8_078`** | `IdeaB8` | `8,262,696` (`-52,472`) | `200 / 200` (`200`) | `17,342,378` (`-268,826`) | `282 / 353` (`282`) | `25,818 / 25,946 / 105,263,539 / 0` | `36da9820f07dd4e851b8ef64a253b011969c6d9e39f2cd5c380541ef208b7da8` | `4` |

*(Total `port_notes.txt` entries: `19` difference lines + `1` S10 choice line = `20` entries in `forge-combo29/carbon2/job39/port_notes.txt`.)*

---

## 4. Part Q — The Six-Port Bundle (`bundle_grok.patch.txt`, commit `a3929857a22c06d1158be04710f7ca36a46c3afe`)

- **Bundle Patch:** `forge-combo29/carbon2/job39/bundle_grok.patch.txt` (`1,102` lines, LF, `sha256 = d0ae7f01f33be912ffe07ca2efdbc0f147c0386a77864a5a3547e0af21c001ec`; `git apply --check -p1`: `PASS (0 == 0)`).
- **Bundle Release Exe:** `/tmp/carbon2_job39/bld_BUNDLE_rel/forge` (`sha256 = e9a195774fcea00849fb39f80b1eafa1609402bb564bf887055b50920f5da4fc`).
- **Bundle Checking Exe:** `/tmp/carbon2_job39/bld_BUNDLE_chk/forge` (`sha256 = 21b258bfdcbf798af48d12d4b9cb09bd98c47cdb6edfe6a6261fe0d661acf53a`).

### 4.1 Q2a & Q2b — Bundle OFF Numbers & Per-Switch Position-by-Position Identity (`partQ_summary.txt`)

```text
  BUNDLE_all_off no-option bench 11           : PASS (312866 == 312866)
  BUNDLE_all_off no-option bench 13           : PASS (862329 == 862329)
  BUNDLE_all_off no-option perft 5            : PASS (4865609 == 4865609)
  BUNDLE_all_off PC20 bench 11                : PASS (278024 == 278024)
  BUNDLE_all_off PC20 bench 13                : PASS (587276 == 587276)
  BUNDLE_all_off Set A line L records         : PASS (26741 == 26741)
  BUNDLE_all_off Set A line L nodes           : PASS (107124743 == 107124743)
  BUNDLE_all_off Set A line L sha256          : PASS (d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2 == d5b527108ec685795a8411ebe92adce25adb84d21fc13cdab79b46433d9e94b2)
  BUNDLE_all_off n[1..60] line L records      : PASS (8449 == 8449)
  BUNDLE_all_off n[1..60] line L searches     : PASS (8482 == 8482)
  BUNDLE_all_off n[1..60] line L nodes        : PASS (36688357 == 36688357)
  BUNDLE_all_off n[1..60] line L sha256       : PASS (b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15 == b6bf7600d07e4fbb33d88c25f2804fd59e37201bde4838d1593f3ebba1a0cd15)
  BUNDLE_all_off O d12 sum vs Step0 OFF       : PASS (8315168 == 8315168)
  BUNDLE_all_off O d12 differing positions    : PASS (0 == 0)

  BUNDLE only IdeaK4 O d12 equal positions    : PASS (200 == 200)
  BUNDLE only IdeaK4 O d12 sum vs P1_K4_093   : PASS (8080229 == 8080229)
  BUNDLE only IdeaS32 O d12 equal positions   : PASS (200 == 200)
  BUNDLE only IdeaS32 O d12 sum vs P2_S32_074 : PASS (8339315 == 8339315)
  BUNDLE only IdeaB1 O d12 equal positions    : PASS (200 == 200)
  BUNDLE only IdeaB1 O d12 sum vs P3_B1_030   : PASS (8548042 == 8548042)
  BUNDLE only IdeaS13 O d12 equal positions   : PASS (200 == 200)
  BUNDLE only IdeaS13 O d12 sum vs P4_S13_016 : PASS (8077984 == 8077984)
  BUNDLE only IdeaS10 O d12 equal positions   : PASS (200 == 200)
  BUNDLE only IdeaS10 O d12 sum vs P5_S10_081 : PASS (8314153 == 8314153)
  BUNDLE only IdeaB8 O d12 equal positions    : PASS (200 == 200)
  BUNDLE only IdeaB8 O d12 sum vs P6_B8_078   : PASS (8262696 == 8262696)
```

### 4.2 Q2c — Bundle All Six Switches ON (`PC20`, Built-In Evaluation)

- **`O` depth 12 (`BUNDLE_ALL_ON_O_d12.rows.txt`, `200` FENs):** `sum_nodes = 8,035,170` (`off = 8,315,168`, `delta = -279,998`, `ratio = 0.966327`), `200 / 200` positions differ (`200 / 200` nodes differ).
- **`G` depth 12 (`BUNDLE_ALL_ON_G_d12.rows.txt`, `353` FENs):** `sum_nodes = 16,356,627` (`off = 17,611,204`, `delta = -1,254,577`, `ratio = 0.928763`), `353 / 353` positions differ (`353 / 353` nodes differ).
- **`Set A line L` (`BUNDLE_ALL_ON_SetA_L.rows.txt`, `200` attempts):** `finished = 200`, `thrown = 0`, `records = 27,991`, `searches = 28,117`, `nodes = 111,242,459`, `record_text_sha256 = c0da7ec87c6e6928320d0e8db3a15e12051d3f31b3391f09d4d5ef4590c58bce`.

### 4.3 Q3 — Bundle Checking Build (`ASan + UBSan + _GLIBCXX_ASSERTIONS`, All Six Switches ON)

The checking harness (`CheckingEngine` + `run_v3_with_stderr` in `forge-combo29/carbon2/job37/run_partA_checking.py`) was imported and used **unchanged** (already calibrated by `CP-A` and `CP-U` in Job 37 Part A, so no new planted control was needed per `FABLE_TO_carbon2_39.md:139-140`).

```text
  BUNDLE_chk no-option bench 11               : PASS (312866 == 312866)
  BUNDLE_chk no-option perft 5                : PASS (4865609 == 4865609)
  BUNDLE_chk no-option pins stderr_bytes      : PASS (0 == 0)
  BUNDLE_chk ALL_ON Set C stderr_bytes        : PASS (0 == 0)
  BUNDLE_chk ALL_ON Set C exit_code           : PASS (0 == 0)
  BUNDLE_chk vs rel ALL_ON Set C records      : PASS (12977 == 12977)
  BUNDLE_chk vs rel ALL_ON Set C nodes        : PASS (51545138 == 51545138)
  BUNDLE_chk vs rel ALL_ON Set C sha256       : PASS (9f9b7e19d465f265ee5ace8c0f90ac733cd55245c97b152f4016a1230ab6b735 == 9f9b7e19d465f265ee5ace8c0f90ac733cd55245c97b152f4016a1230ab6b735)
  BUNDLE_chk ALL_ON n[1..20] stderr_bytes     : PASS (0 == 0)
  BUNDLE_chk ALL_ON n[1..20] exit_code        : PASS (0 == 0)
  BUNDLE_chk vs rel ALL_ON n[1..20] records   : PASS (2103 == 2103)
  BUNDLE_chk vs rel ALL_ON n[1..20] nodes     : PASS (9239955 == 9239955)
  BUNDLE_chk vs rel ALL_ON n[1..20] sha256    : PASS (0d794e83ca5d2f34197556fd9d78733500a328f56a56a17a09edc28b238c0ac7 == 0d794e83ca5d2f34197556fd9d78733500a328f56a56a17a09edc28b238c0ac7)
```

### 4.4 Q4 — Six-Switch Table for the PC (`q4_switch_table.md`, line numbers in `bundle_grok.patch.txt`-patched `r15d + v3`)

| Switch (`option name`) | Default | Tuner Range (Check + Spin Sub-options) | Cost per Node When ON (What It Computes) | Every Place Where It Reads State Another Switch Writes |
| :--- | :--- | :--- | :--- | :--- |
| **`IdeaK4`** (`P1`, seat `093`) | `false` (`IdeaK4_Shrink = 24`) | `IdeaK4`: `{false, true}`; `IdeaK4_Shrink`: `[0, 200]` | At non-PV, non-check, non-excluded nodes (`depth <= RfpDepth`), performs two stack loads (`(ss - 1)->static_eval`, `(ss - 3)->static_eval`) and one comparison + subtraction (`rfp_margin -= IdeaK4_Shrink`). `O(1)`, zero board scans or allocations. | 1. `src/search.cpp:2538-2542` (`IdeaK4` <- `IdeaS10`): Reads `(ss - 1)->static_eval` and `(ss - 3)->static_eval`, which `IdeaS10` overwrites (`eval = ss->static_eval = eval * IdeaS10_Shrink / 1024` at `2466`) when `IdeaS10` fired at `ply - 1` or `ply - 3`.<br>2. `src/search.cpp:2545` (`IdeaK4` <- `IdeaS10`): Compares `eval - rfp_margin >= beta` using `eval` shrunk by `IdeaS10` (`2466`) and `improving` (`2478-2480`, reading `IdeaS10`-shrinkable `(ss - 2)`/`(ss - 4)->static_eval`). |
| **`IdeaS32`** (`P2`, seat `074`) | `false` (`IdeaS32_OwedSlack = 0`) | `IdeaS32`: `{false, true}`; `IdeaS32_OwedSlack`: `[0, 64]` | Clears `returned_on_hash` and `hash_proof_depth` on `search`/`search_child`/`qsearch_child` entry; writes them on non-PV TT cutoffs; at NMP fail-highs (`depth < 14`), checks `(ss + 1)->returned_on_hash && (ss + 1)->hash_proof_depth < depth - IdeaS32_OwedSlack`, running one reduced verification `search_child(depth - reduction)` when shallow. | 1. `src/search.cpp:2550, 2558` (`IdeaS32` <- `IdeaS10`): NMP entry guard and `reduction` read `eval` and `ss->static_eval` after `IdeaS10` shrinks them (`2466`).<br>2. `src/search.cpp:2590-2613` (`IdeaS32` <-> `IdeaS10`): When `!shallow_hash` (`2590`), `s10_pull(null_score)` (`IdeaS10`) pulls `null_score` before checking `>= beta` (falling through to verification if `pulled < beta`); when `shallow_hash` forces verification (`2602`), `IdeaS10` pulls `null_score` (`2608`).<br>3. Reads TT entries whose depths/scores were stored under all active switches. |
| **`IdeaB1`** (`P3`, seat `030`) | `false` (`IdeaB1_Scale = 96`, `IdeaB1_Fade = 4`) | `IdeaB1`: `{false, true}`; `IdeaB1_Scale`: `[0, 500]`; `IdeaB1_Fade`: `[0, 64]` | Executed only when `MovePicker` scores quiet moves: per quiet move, `fading_board_prior` (`src/search.cpp:369-413`) computes mover attacks at `move.from` (`occ`) and `move.to` (`occ_to`), two `popcount`s each against enemy occupancy and enemy king zone, plus one integer division faded by `|main_history[us][from][to]|`. | 1. `src/search.cpp:1022, 1156, 1185, 1231` (`IdeaB1` <- all switches via `main_history_`): Reads `plain = main[move.from][move.to]`, whose updates depend on cutoffs/PV moves shaped by `IdeaK4`, `IdeaS32`, `IdeaS13`, `IdeaS10`, and `IdeaB8`.<br>2. `src/search.cpp:1016-1022` (`IdeaB1` + `IdeaS13` + `IdeaB8`): Sums additively in `QuietScorer::score` with `IdeaS13` (`break_prep_order`) and `IdeaB8` (`threat_role_bonus`). |
| **`IdeaS13`** (`P4`, seat `016`) | `false` (`IdeaS13_Lookback = 4`, `IdeaS13_ReduceDivisor = 1024`) | `IdeaS13`: `{false, true}`; `IdeaS13_Lookback`: `[2, 12]` (even plies); `IdeaS13_ReduceDivisor`: `[256, 16384]` *(inert as written in `016` — see Facts #3)* | Stores `ss->pawn_key = board.pawn_key()` (`O(1)`); `16 KiB`/worker `BreakPrepHistory` lookup per non-pawn quiet in `MovePicker`; on pawn fail-highs (`2980-2983`), walks `back = 2, 4 .. Lookback` updating `BreakPrepHistory` when `previous->pawn_key == ss->pawn_key`. | 1. `src/search.cpp:1016-1022` (`IdeaS13` + `IdeaB8` + `IdeaB1`): Sums additively in `QuietScorer::score` with `IdeaB8` and `IdeaB1`.<br>2. `src/search.cpp:2980-2983` (`IdeaS13` <- `IdeaS10`, `IdeaK4`, `IdeaS32`, `IdeaB1`, `IdeaB8`): `credit_break_prep` runs on `best_score >= beta` before `best_score = s10_pull(best_score)` (`2999`), reading child `score`s pulled by `IdeaS10` and ancestor `current_move`/`moved_piece` chosen under `IdeaB1`/`IdeaB8` ordering (`IdeaS10`'s probe saves/restores `current_move` and `moved_piece` at `2258, 2279`). |
| **`IdeaS10`** (`P5`, seat `081`) | `false` (`Margin = 25`, `Flat = 40`, `Look = 4`, `Shrink = 896`, `Depth = 5`) | `IdeaS10`: `{false, true}`; `Margin`: `[0, 500]`; `Flat`: `[0, 400]`; `Look`: `[1, 16]`; `Shrink`: `[0, 1024]`; `Depth`: `[1, 32]` | `O(1)` early outs on almost all nodes; **only after `Look = 4` consecutive non-pawn non-capture moves** (`depth >= 5`, `|eval| >= 25`), queries cached `Evaluator::pawn_structure_cp`, runs 1-ply `restricted_quiet_score` (`static_evaluate` over legal non-pawn quiets, clearing `v3_state_->valid_flags[ss->ply + 5]`), and `defender_holds`. | 1. `src/search.cpp:2447-2454`: Reads `eval` (including TT score tightening from active switches) and `(ss - 1 .. ss - Look)->current_move`/`moved_piece`.<br>2. **Writes `eval = ss->static_eval = eval * IdeaS10_Shrink / 1024` (`2466`)**, which is read downstream by **`IdeaK4`** (`2538-2545`), **`IdeaS32`** (`2550, 2591, 2608`), and **`IdeaB8`** (`note_threat_swing` at `1919-1921`). |
| **`IdeaB8`** (`P6`, seat `078`) | `false` (`IdeaB8_Weight = 1024`, `IdeaB8_Swing = 48`) | `IdeaB8`: `{false, true}`; `IdeaB8_Weight`: `[0, 4096]`; `IdeaB8_Swing`: `[0, 500]` | Per-position cached `find_role_threat` (`threat_role_key_ == board.key()`, `Knight..Queen` cheaper-attacker scan); when a threat exists, `quiet_threat_role` (`attacks_after_quiet`) indexes `ThreatRoleHistory` (`[2][7][7][5]`, `980` B/worker) in `QuietScorer`, `quiet_history`, `update_quiet_stats`, PV bonus, and `note_threat_swing`. | 1. `src/search.cpp:1919-1921` (`IdeaB8` <- `IdeaS10`): `note_threat_swing` computes `gained = -(ss + 1)->static_eval - ss->static_eval`, reading `IdeaS10`-shrunk static evals whenever `IdeaS10` fired on parent or child.<br>2. `src/search.cpp:1016-1022, 1726, 2690, 2766, 2889`: Sums with `IdeaS13` and `IdeaB1` in `MovePicker`, and unlike `IdeaB1`/`IdeaS13` also enters `Worker::quiet_history` (`1726`), feeding `history` in history pruning (`2766`) and LMR (`2889`). |

---

## 5. Facts, Suspicions, Read and Not Tested, What I Did Not Do, What I Am Not Sure About

### Facts (Directly Verified by Executed Builds, Hashes, and Raw Files)
1. **Switch-off exactness (`7` executables):** All `6` individual port builds (`P1..P6`) and the combined `bundle_grok.patch.txt` Release build reproduce every Step 0 OFF number (`312866`, `862329`, `4865609`, `PC20` `278024` / `587276`, `Set A line L` `26,741` / `107,124,743` / `d5b52710...`, `n[1..60] line L` `8,449` / `8,482` / `36,688,357` / `b6bf7600...`, and `O` d12 `8,315,168` with `0/200` differing positions).
2. **Per-switch bundle isolation (`Q2b`):** Enabling each of the `6` switches alone in `bundle_grok.patch.txt` matches its standalone port (`P1..P6`) on `200` of `200` `O`-set positions (`nodes`, `bestmove`, and `score`).
3. **Audit finding in `016` (`IdeaS13`, documented in `port_notes.txt` and Q4):** Both on `6b98f217` (`src/search.cpp:2003` after `make_move` at `1974`) and in our faithful port (`src/search.cpp:2891` after `make_move` at `2861`), `016` calls `break_prep_order(board, move)` **after** `board.make_move(move, undo)`. Because `board.piece_at(move.from)` is `Empty` (`piece_type(Empty) == 0 <= Pawn`), `prep` is always `0` in LMR: `016`'s `+4.40 Elo` swarm result tested pure `BreakPrepHistory` quiet ordering, and `IdeaS13_ReduceDivisor` is inert unless `prep` is hoisted above `board.make_move`.
4. **`CuckooRep` wrapper state safety (`P2` & `P6`):** On `r15d + v3`, `Worker::search_child` and `Worker::qsearch_child` (`B4 CuckooRep`, active in `PC20`) can return `DrawScore` early on `upcoming_repetition` without entering `Worker::search` / `Worker::qsearch`. Clearing `returned_on_hash` / `hash_proof_depth` (`IdeaS32`) and `role_eval_ready` (`IdeaB8`) on wrapper entry (`src/search.cpp:3032-3089`) prevents stale sibling stack flags from leaking across early `CuckooRep` returns.
5. **Sanitizer & v3 accumulator cleanliness (`Q3`):** The bundle checking build (`ASan + UBSan + _GLIBCXX_ASSERTIONS`) produced `0 == 0` `stderr_bytes` on `Set C line L` (`100` attempts, `12,977` records, `51,545,138` nodes) and `n[1..20] line L` (`20` attempts, `net768.fnn3`, `2,103` records, `9,239,955` nodes), matching the Release bundle build's `record_text_sha256` bit-for-bit on both runs (`9f9b7e19...` and `0d794e83...`).

### Suspicions (Apart from Facts)
1. **Hoisting `prep` above `board.make_move` in `IdeaS13`:** Activating `IdeaS13`'s intended `-1` ply LMR relief (`prep / IdeaS13_ReduceDivisor`) by computing `prep` before `board.make_move` could either help pawn-break preparation lines or add tree bloat at `250k` nodes; because `016` never tested that LMR relief in its `1,106`-game match and Job 39 runs no matches, leaving `016`'s tested behavior untouched while flagging it for the PC is safer than silently changing the rule.
2. **Quiet-ordering overlap (`IdeaB1` + `IdeaS13` + `IdeaB8` + `r15d` `HistRework=2`):** Under `PC20`, three new quiet-ordering terms stack on top of `HistRework=2` and `ThreatHistory=true`; if the bundle shows wall-time overhead at `2,000` soft nodes or clock TC, `IdeaB1` (`fading_board_prior` slider attack generation per quiet) and `IdeaB8` (`find_role_threat` + `attacks_after_quiet`) carry almost all of the per-node compute cost among the six switches.

### Read and Not Tested (Apart)
1. **`grok-016`'s `REPORT.md` (`origin/for-fable-and-opus/grok-016:forge-combo29/grok/016/REPORT.md`):** Read to confirm `016`'s author intended LMR reduction relief in prose (`can take one ply off their reduction`) even though the code placed `break_prep_order(board, move)` after `board.make_move`; we did **not** build or test a modified `S13_hoisted` variant in matches because Job 39 runs no matches.
2. **`FORGE_PAWN_HISTORY=1` compile branch:** Read in `src/search.cpp` while placing `IdeaB1`, `IdeaS13`, and `IdeaB8` hooks around `#if FORGE_PAWN_HISTORY`; not compiled with `-DFORGE_PAWN_HISTORY=1` because `r15d + v3`'s default and PC recipe compile with `FORGE_PAWN_HISTORY=0`.

### What I Did Not Do
1. **No engine matches or SPRTs** were run (per `FABLE_TO_carbon2_39.md`: *"No match in this job; the PC plays the bundle with its own net"*).
2. **No SP-PGO profile-guided build** was run for Part P/Q executables (per `FABLE_TO_carbon2_39.md:123`: *"no profile needed for rows"*), and **no new planted sanitizer controls** were created because Job 37's `run_partA_checking.py` harness was reused unchanged (`FABLE_TO_carbon2_39.md:139-140`).
3. **No multi-threaded (`Threads > 1`) stress run** (such as `TSan`) was executed, though every added state variable (`break_prep_history_`, `threat_role_history_`, `threat_role_*` cache, `SearchStack` fields, `pawn_cache_`, `v3_state_`) is strictly per-`Worker` with zero mutable globals written during search.

### What I Am Not Sure About
1. **How `IdeaS10` behaves with the PC's newer stand-alone v3 net:** `IdeaS10` compares the v3 net's `eval` sign and magnitude against the hand-crafted evaluator's `pawn_structure_cp(board)` (`|pawn_cp| >= 25` and `(pawn_cp > 0) == (eval > 0)`), and fired on only `17/200` `O` positions and `98/353` `G` positions under built-in eval; with the PC's net (`K+Q v K` at `1,867..2,263`), its firing rate in shuffling middlegames/endgames may shift.
2. **Net wall-time cost of `IdeaB1 + IdeaB8 + IdeaS10` on Windows (`forge/r15dsg`):** While node counts on `O` (`0.9663x`) and `G` (`0.9288x`) decreased with all six switches on, per-node NPS impact on the PC's Windows PGO binary under its v3 net can only be measured on the PC.

---

## 6. Final Repository Status & Directory Listing (`git status --short && ls -R forge-combo29/carbon2/job39`)

```text
 M forge-combo29/carbon2/job39/stamps.txt
?? forge-combo29/carbon2/job39/REPORT_carbon2_job39.md
forge-combo29/carbon2/job39:
builds.txt
BUNDLE_ALL_ON_G_d12.rows.txt
BUNDLE_ALL_ON_G_d12.rows.txt.meta
BUNDLE_ALL_ON_O_d12.rows.txt
BUNDLE_ALL_ON_O_d12.rows.txt.meta
BUNDLE_ALL_ON_SetA_L.rows.txt
BUNDLE_ALL_ON_SetA_L.rows.txt.meta
BUNDLE_CHK_ALL_ON_n20_L.rows.txt
BUNDLE_CHK_ALL_ON_n20_L.rows.txt.meta
BUNDLE_CHK_ALL_ON_SetC_L.rows.txt
BUNDLE_CHK_ALL_ON_SetC_L.rows.txt.meta
bundle_grok.patch.txt
BUNDLE_ONLY_IdeaB1_O_d12.rows.txt
BUNDLE_ONLY_IdeaB1_O_d12.rows.txt.meta
BUNDLE_ONLY_IdeaB8_O_d12.rows.txt
BUNDLE_ONLY_IdeaB8_O_d12.rows.txt.meta
BUNDLE_ONLY_IdeaK4_O_d12.rows.txt
BUNDLE_ONLY_IdeaK4_O_d12.rows.txt.meta
BUNDLE_ONLY_IdeaS10_O_d12.rows.txt
BUNDLE_ONLY_IdeaS10_O_d12.rows.txt.meta
BUNDLE_ONLY_IdeaS13_O_d12.rows.txt
BUNDLE_ONLY_IdeaS13_O_d12.rows.txt.meta
BUNDLE_ONLY_IdeaS32_O_d12.rows.txt
BUNDLE_ONLY_IdeaS32_O_d12.rows.txt.meta
j39_lib.py
OFF_G_d12.rows.txt
OFF_G_d12.rows.txt.meta
OFF_O_d12.rows.txt
OFF_O_d12.rows.txt.meta
P1_K4_093_on_G_d12.rows.txt
P1_K4_093_on_G_d12.rows.txt.meta
P1_K4_093_on_O_d12.rows.txt
P1_K4_093_on_O_d12.rows.txt.meta
P1_K4_093_on_SetA_L.rows.txt
P1_K4_093_on_SetA_L.rows.txt.meta
P1_K4_093.patch.txt
P1_K4_093_summary.txt
P2_S32_074_on_G_d12.rows.txt
P2_S32_074_on_G_d12.rows.txt.meta
P2_S32_074_on_O_d12.rows.txt
P2_S32_074_on_O_d12.rows.txt.meta
P2_S32_074_on_SetA_L.rows.txt
P2_S32_074_on_SetA_L.rows.txt.meta
P2_S32_074.patch.txt
P2_S32_074_summary.txt
P3_B1_030_on_G_d12.rows.txt
P3_B1_030_on_G_d12.rows.txt.meta
P3_B1_030_on_O_d12.rows.txt
P3_B1_030_on_O_d12.rows.txt.meta
P3_B1_030_on_SetA_L.rows.txt
P3_B1_030_on_SetA_L.rows.txt.meta
P3_B1_030.patch.txt
P3_B1_030_summary.txt
P4_S13_016_on_G_d12.rows.txt
P4_S13_016_on_G_d12.rows.txt.meta
P4_S13_016_on_O_d12.rows.txt
P4_S13_016_on_O_d12.rows.txt.meta
P4_S13_016_on_SetA_L.rows.txt
P4_S13_016_on_SetA_L.rows.txt.meta
P4_S13_016.patch.txt
P4_S13_016_summary.txt
P5_S10_081_on_G_d12.rows.txt
P5_S10_081_on_G_d12.rows.txt.meta
P5_S10_081_on_O_d12.rows.txt
P5_S10_081_on_O_d12.rows.txt.meta
P5_S10_081_on_SetA_L.rows.txt
P5_S10_081_on_SetA_L.rows.txt.meta
P5_S10_081.patch.txt
P5_S10_081_summary.txt
P6_B8_078_on_G_d12.rows.txt
P6_B8_078_on_G_d12.rows.txt.meta
P6_B8_078_on_O_d12.rows.txt
P6_B8_078_on_O_d12.rows.txt.meta
P6_B8_078_on_SetA_L.rows.txt
P6_B8_078_on_SetA_L.rows.txt.meta
P6_B8_078.patch.txt
P6_B8_078_summary.txt
partQ_summary.txt
port_notes.txt
prediction_job39.txt
q4_switch_table.md
REPORT_carbon2_job39.md
run_partQ.py
run_port_verify.py
run_step0.py
stamps.txt
step0_raw.txt
```

---

**Model:** `Gemini 4 Carbon` (`carbon2`)
