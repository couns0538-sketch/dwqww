# kimi5 job 31 report — kF on the PC's compiler: reading, then checks

## The report's first lines (per the job)

**(1) Step 0: PASSED on both builds.** r15d and kF (g++ 13.3.0, Release, PC's -D list,
`-ffp-contract=off -fno-fast-math -march=native`), a fresh process per line:
bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; with PC20: bench 11 = 278024,
bench 13 = 587276. Raw: `tests_kimi5_job31/step0/{r15d,kF}/` (5 output + 5 input files each),
script `step0/step0_j31.sh`.

**(2) Step 1: the table is `tests_kimi5_job31/step1_table.md`; DIFFERS 0, UNSURE 1.**
Full reading of the 2,450-line diff (9 files) over `include/` + `src/`
(raw: `step1_diff_include.txt`, `step1_diff_src.txt`). UNSURE row first:

| # | kF file:line | class | verdict |
|---|---|---|---|
| E1 | src/search.cpp:1199-1202 | (e) | **UNSURE** — `std::sort` with comparator `a.score > b.score` and no tie-break: the order of equal-scored moves is libstdc++-version-defined and search-visible. MinGW's libstdc++ is not g++ 13.3's. C3 below proves the substance is REAL: ties exist, their order decides trees. |

All other rows SAFE (A1-A2 sizes, B1-B3 alignment, C1-C7 intrinsics/macros, D1-D6 UB,
E2-E9 library/system, F1 the info line). F1 ANSWERED from the print code: a
node-limit-stopped search prints NO further info line — `if (aborted_) break;`
(src/search.cpp:3645) precedes `emit(...)` (:3647); abort-publish emits (:3543, :3554) are
guarded by `!stopped_by_nodes_` (:3538, :3545, :3547). That confirms job 28 §4.3 from the
code itself. The four fallback paths the PC does NOT take are named in the table; every
guard macro is defined for x86_64-w64-mingw32 (probe: `c1/clang_macros.txt`).

**(3) Prediction graded (commit "kimi5 job 31 prediction", 06:06:10Z, before Step 2): 4/4.**
Predicted DIFFERS [0,1] → 0 ✓. UNSURE [1,3] → 1 ✓. C1 equal 553/553 → equal ✓.
C2 report count 0 → 0 ✓.

**(4) C1, C2, C3 with their known answers.**

- **C1 PASSED.** kF built with clang 18.1.3 (Ubuntu 18.1.3-1ubuntu1; no clang 23 here, the
  job allows any version), PC's exact -D list, `-std=c++20 -O3 -DNDEBUG -ffp-contract=off
  -fno-fast-math -march=native` (clang 18 has no -march=znver5; said in table), link fix
  `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`. W1 O 200 + G 353 at depth 12, PC20,
  Threads 1, Hash 16: **all 553/553 rows equal to the job 28 kF known answers, node count
  and best move** (sums 8,315,168 and 17,611,204 — identical). Evidence: `c1/O.json`,
  `c1/G.json`, known answers `c1/ka28_O.json`, `c1/ka28_G.json`, recount in
  `compare_output.txt`, full UCI logs `c1/{O,G}_full.txt`, inputs `c1/{O,G}_input.log`,
  build `c1/clang_build_tail.txt`. A clang/libstdc++ codegen difference would have had
  ~2.6·10^7 searched nodes to show in; nothing differed.
- **C2 PASSED. Control first:** the same UBSan build plus ONE planted misaligned 64-bit
  read (`c2_control_misalign.patch.txt`, applied with `patch -p1 -F0`) reports
  `runtime error: load of misaligned address ... for type 'const uint64_t'` at
  search.cpp:3120 and aborts (`c2/c2_control_run.txt`) — the checker reaches the search.
  **Clean build** (g++ 13.3, `-O1 -g -DNDEBUG -fsanitize=undefined,alignment
  -fno-sanitize-recover=all`, PC's -D list): W1 O + G at depth 10, 553 searches:
  **0 sanitizer reports** (sums 3,301,402 / 6,401,895; best moves equal the depth-12 known
  answers on 163/200 O and 289/353 G — expected fewer at depth 10; node counts differ from
  the depth-12 answers by design). Evidence: `c2/O.json`, `c2/G.json`, `c2/{O,G}_full.txt`,
  `c2/ubs_build_tail.txt`.
- **C3 (the E1 probe) DONE — E1 is REAL.** A diagnostic build whose only change is a
  tie-break on the move encoding in the comparator at search.cpp:1199
  (`c3/c3_tiebreak.patch.txt`, applies `-p1 -F0`, re-verified today):
  bench 11 = 330,647 and bench 13 = 872,701 (pins are 312,866 / 862,329) — the pins detect
  tie order. W1 depth 12: node counts differ on **200/200 O** and **351/353 G**; best moves
  differ on 57/200 O and 93/353 G (`compare_output.txt`, `c3/*.json`, `c3/*_full.txt`).
  So equal-scored moves exist everywhere and their order builds the tree. What remains
  unknowable on Linux: whether MinGW's libstdc++ sorts ties differently from g++ 13.3 —
  the PC check is the bench pins, then the 553 W1 rows.

**(5) Repairs per DIFFERS row: none needed — there are 0 DIFFERS rows.**
For the one UNSURE row E1: **no node-count-preserving repair exists.** Any tie-break makes
the comparator total and thereby changes the trees versus g++ 13.3 (proven above: the pins
move). If the PC ever fails the pins for this reason, the repair is a port: build with
`c3/c3_tiebreak.patch.txt`, take NEW pins from that build, and re-baseline the W1 rows;
that is a portability repair, not a no-change one. Recommended only if the PC actually
differs; otherwise kF stays as it is.

## 1. Three lines in plain words
Asked: read every line the r15d→kF stack adds and mark each place a Windows x64 clang 23 /
llvm-mingw build could behave differently from my Linux g++ build, then run the checks my
machine can run. Answer: exactly one search-visible line — the un-tie-broken `std::sort`
at src/search.cpp:1199 — depends on the C++ library version; everything else is SAFE by
reading; a clang 18 build here reproduces all 553 known rows exactly, UBSan finds nothing,
and the tie order is proven load-bearing. How sure: high on everything my machine can test
(C1/C2/C3 all pass with controls); the single open point needs the PC itself (its
libstdc++ version) and is covered there by the bench pins.

## 2. Step 0 known numbers (raw output files)
`tests_kimi5_job31/step0/r15d/`: none_bench11.txt = 312866, none_bench13.txt = 862329,
none_perft5.txt = 4865609, pc20_bench11.txt = 278024, pc20_bench13.txt = 587276.
`tests_kimi5_job31/step0/kF/`: same five values. Input logs beside each; script
`step0/step0_j31.sh`; binary hashes `*/exe.sha256`.

## 3. Step table
| step | status | evidence | result |
|---|---|---|---|
| Claim + job read | done | claim commit 06:01:39Z | job 31 lowest open; 32/33 read, new, no corrections |
| Colleagues | done | their branches | deepseek5 notes read; glmflash5-work still absent |
| Trees r15d/kF | done | sha256 29/29 each | identical to job 28 trees |
| Step 0 | done | `step0/` | all 5 pins on both builds |
| Step 1 reading | done | `step1_table.md`, `step1_diff_*.txt` | DIFFERS 0, UNSURE 1 (E1) |
| Prediction | done | own commit 06:06:10Z | graded 4/4 above |
| C1 clang build | done | `c1/` | 553/553 equal |
| C2 control | done | `c2_control_misalign.patch.txt`, `c2/c2_control_run.txt` | reports + aborts |
| C2 clean UBSan | done | `c2/` | 0 reports / 553 searches @ d10 |
| C3 E1 probe | done | `c3/` | ties real; pins move; no count-preserving repair |

## 4. Findings (file:line + how to see it again)
- F-1 (E1, the one open row): kF `src/search.cpp:1199-1202`, comparator `a.score > b.score`
  in `std::sort(moves_+index_, moves_+count_, ...)`. Ties are created by design: histories
  zeroed at every search start, the +12000 check bonus :1028, zero cont rows :1010.
  See it: build kF with `c3/c3_tiebreak.patch.txt` → bench 11 prints 330647.
- F-2: the info line under `go nodes` — kF `src/search.cpp:3216` (emit), :3240, :3220;
  call sites :3543, :3554, :3633, :3647; `if (aborted_) break;` :3645; guard
  `!stopped_by_nodes_` :3538/:3545/:3547 (set :2036, cleared :3127). A node-stopped search
  prints no extra line. See it: `grep -n "stopped_by_nodes_\|aborted_" src/search.cpp`.
- F-3: every aligned 512-bit load is backed by `alignas(64)` + C++17 aligned new:
  TT `include/forge/search.hpp:131-136` (static_asserts), allocation `src/search.cpp:450`;
  NNUE `include/forge/nnue_v3.hpp:120,133`, `src/nnue_v3.cpp:522,527`; move picking uses
  unaligned loads only (`src/search.cpp:814-846`). Nothing in the diff relies on
  Linux-specific over-alignment.
- F-4: no `long`, no `1L/1UL`, no printf length letters, no POSIX-only call in the whole
  diff (greps in the step-1 commit); `__int128` path in `cluster_index`
  (`include/forge/search.hpp:305-308`) is guarded and its macro is defined for the mingw
  target (`c1/clang_macros.txt`).
- Suspicions, not proven: (S-1) the AVX-512 NNUE loops (`src/nnue_v3.cpp:395-450`,
  :1077-1120) assume `hidden % 32 == 0`; true for 256 (built-in) and 768 (PC-class), but a
  future odd-sized net would read past a w1 column end — the shape static_asserts do not
  cover divisibility by 32. (S-2) MinGW's libstdc++ version is unknown to me; if it is a
  GCC ≥ 14 import and its introsort changed, E1 fires on the PC — the bench pins catch it.

## 5. From my colleagues
Read: deepseek5's `NOTES_deepseek5.md` tail (job 30 era) — their warning that option names
must be proven to arrive was applied: every run's `setoption` lines are in the committed
`*_input.log` files (step0 and `c1/*_input.log`). `for-fable-and-opus/glmflash5-work` still
does not exist (`couldn't find remote ref`); said so since job 29. Checked: nothing of
theirs conflicted with this job; job 32/33 headers were read for corrections (none for 31).

## 6. What I did NOT do
Did not build with clang 23 / llvm-mingw / Windows (not available here — the job's
"What this check cannot see" applies verbatim); did not test Threads > 1 (job: not needed);
did not run the PC's PGO/ThinLTO recipe; did not change any engine source in the repo
(patches are text files in my folder); did not rerun job 28's full W2.

## 7. What I am NOT sure about
Whether MinGW's libstdc++ sorts equal elements exactly like g++ 13.3 (E1's last unknown;
PC bench pins decide). Whether clang 23 specifically (not 18) keeps the 553 rows equal —
likely, same libstdc++ here, but only probed on 18.1.3. S-1's divisibility assumption.

## 8. A better way
For E1 the job's check (PC bench pins) is already the cheapest possible detector — my C3
shows the pins move by +5.7% on a tie-order change, so one `bench 11` on the PC settles it
before any W1 run. One addition worth considering: since ANY tie-break changes trees, if
cross-compiler reproducibility is ever valued over keeping the current pins, adopt
`c3/c3_tiebreak.patch.txt` deliberately as a port with NEW pins (330647 / 872701 for
bench 11/13 under this build) and re-baselined W1 rows — the comparator becomes total and
every conforming standard library then produces identical trees. Check that it is better:
build r15d+kF+patch on two compilers and require 553/553 equality between THEM (today's
clang-vs-g++ test, repeated on the ported tree).

## What this check cannot see (per the job, verbatim)
The PC itself: its Windows loader, the llvm-mingw runtime, the profile step, Zen 5. A row
marked SAFE is a reading, not a test.
Additionally (from the table): clang 18 here does not know `-march=znver5`, so C1 ran
`-march=native` on an AVX-512 host and the znver5 macro claims rest on the feature probe +
hardware facts; the MinGW libstdc++ VERSION (E1) no Linux check can see; PGO and ThinLTO
are codegen only (no UB added — the D-rows and C2's zero reports).

## 9. UTC stamps
Run start 2026-11-19T06:01:00Z (cron). Every step stamped in
`tests_kimi5_job31/stamps.txt` from `date -u`. Times: see stamps.txt.
Parallel processes used: 2 at most (the two W1 lists ran one after another; builds used
`cmake --build --parallel` on this machine's cores).

## 10. Model name
Kimi K3 (runtime identifier: kimi-k3).

## Last command before the report commit
`git status --short` and `ls -R tests_kimi5_job31` — output below (pasted after running).

```
$ git status --short
 M forge-combo29/tests_kimi5_job31/stamps.txt
?? forge-combo29/REPORT_kimi5_job31.md
?? forge-combo29/tests_kimi5_job31/c1/
?? forge-combo29/tests_kimi5_job31/c2/
?? forge-combo29/tests_kimi5_job31/c2_control_misalign.patch.txt
?? forge-combo29/tests_kimi5_job31/c3/
?? forge-combo29/tests_kimi5_job31/compare_j31.py
?? forge-combo29/tests_kimi5_job31/compare_output.txt

$ ls -R forge-combo29/tests_kimi5_job31
forge-combo29/tests_kimi5_job31:
c1
c2
c2_control_misalign.patch.txt
c3
compare_j31.py
compare_output.txt
stamps.txt
step0
step1_diff_include.txt
step1_diff_src.txt
step1_table.md

forge-combo29/tests_kimi5_job31/c1:
clang_build_tail.txt
clang_macros_cmd.txt
clang_macros.txt
G_full.txt
G_input.log
G.json
G.json.meta
ka28_G.json
ka28_O.json
O_full.txt
O_input.log
O.json
O.json.meta

forge-combo29/tests_kimi5_job31/c2:
c2_control_run.txt
G_full.txt
G_input.log
G.json
O_full.txt
O_input.log
O.json
ubs_build_tail.txt

forge-combo29/tests_kimi5_job31/c3:
c3_tiebreak.patch.txt
G_full.txt
G.json
O_full.txt
O.json

forge-combo29/tests_kimi5_job31/step0:
kF
pc20.opt
r15d
step0_j31.sh

forge-combo29/tests_kimi5_job31/step0/kF:
exe.sha256
none_bench11_input.log
none_bench11.txt
none_bench13_input.log
none_bench13.txt
none_perft5_input.log
none_perft5.txt
pc20_bench11_input.log
pc20_bench11.txt
pc20_bench13_input.log
pc20_bench13.txt

forge-combo29/tests_kimi5_job31/step0/r15d:
exe.sha256
none_bench11_input.log
none_bench11.txt
none_bench13_input.log
none_bench13.txt
none_perft5_input.log
none_perft5.txt
pc20_bench11_input.log
pc20_bench11.txt
pc20_bench13_input.log
pc20_bench13.txt
```
