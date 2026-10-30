---
name: forge-engine-verify
description: Build and verify a Forge engine change on the PC - box-recipe build, lock identity (bench/perft pins), FMA, CMake + CTest, planted-bug (mutant) check, paired ABBA NPS A/B, codegen compare. Use whenever C++ engine code (src/, include/, tests/, CMakeLists.txt) changes, an option is added, or bench/NPS numbers are requested.
---

# Forge engine build + verification

Paths: lock archive `LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039`,
lock exe `D:/grok-pc-data/dwqww/.claude/worktrees/b/base/forge_lock_copy.exe` (sha256 `5d4df7f1…`, the box-recipe
build of the lock; the queue's AL1 gate base `C:\Users\Administrator\grok-pc\forge_push\bin\forge_h256_s198.exe` is a
different build, sha256 `833c47f3…`; copy an exe to the build dir before timing), tools `D:/grok-pc-data/dwqww/.claude/worktrees/b/tools/`, venv python
`PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe`. Builds go to `F:/opus_scratch/build/<job>/`.

## 1. Box-recipe build (the PC lock recipe: g++ 15.2 ucrt64, -O3 -DNDEBUG, znver5, static, FMA off)
`nice -n 19 bash $T/build_pc.sh "$PWD" /f/opus_scratch/build/<job>/<name>.exe [extra -D flags] > build.log`
- The script prints the exe sha256 and the FMA count (must be 0). `grep -ci warning build.log` should be 0.
- Two builds of the same source differ only in the PE timestamp/checksum (6 bytes at offsets ~137-139 and
  ~217-220): `cmp -l a.exe b.exe | wc -l`.

## 2. Identity (option OFF must equal the lock)
`nice -n 19 $PY -I -B $LA/2_build/uci_check.py <exe> --full` -> must print `ALL OK`:
bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690.

## 3. CMake + CTest
**Before every push that touches engine, tests, CMake or CI files, build ALL CMake targets and run the full
ctest list locally** (R3, 2026-10-27: opus-ci run 40564150654 failed because two merged tests used pre-O3 member
names; build_pc.sh only compiles the engine, so the per-merge PC checks could not see it). Helper:
`opus-r3-stack:opus_r3/R3-1/tools/run_ctest.sh <build dir> <log>` (ctest + check_known_failures.py). After the
push, follow the run (`gh run list --branch <b>`) to green; the user requires every run to succeed.

`JOBS=1 nice -n 19 bash $T/cmake_build.sh "$PWD" /f/opus_scratch/build/<job>/cmake` (JOBS<=2), then with
PATH set as in cmake_build.sh: `cd <bd> && ctest -R "<names>" --output-on-failure --timeout 900`.
Known failures: `forge_tests` has 4 known lines; CI checks them with `check_known_failures.py`.
The full matrix (release, ASan+UBSan, TSan) runs on GitHub CI after the push.

CI build types: release = CMake Release; ASan and TSan = RelWithDebInfo. All three define `NDEBUG`, so
debug-only code (`#ifndef NDEBUG` hooks such as DebugSearchDelayMs) is absent in every CI engine: tests and
`opus_round1/*/tsan_extra.sh` hooks that need it must use a test-only target (e.g. `forge_debughooks`), and a
probe for such a hook must not be passable by a timing race on a slow (sanitizer) build.

## 4. Planted bug
Copy `src include` to `/f/opus_scratch/build/<job>/mutant_src`, patch one line with a Python `replace`
(assert the pattern occurs once), build the mutant, and show the new test FAILS with a clear message.
- One fresh scratch folder per mutant and per run (no deletes): `opus-sol-S12/opus_round1/sol_S12/followup_nullalias/
  mutation_check_alias.py` builds the core objects once per mutant and links every test against them.
- Report survivors honestly; if a mutant survives, say whether it is equivalent in today's engine (why) and add a
  test that kills it if the invariant matters (S12: 5/7 → 7/7 with two extra checks).
- Sol's prepared tests were often never compiled (private members, other base). Ship them as `_v2` with the
  smallest substitution (keep his file untouched), and run them against the base as a control: his "must fail on
  base" checks must fail there and the parity checks must pass (S12: 17 fail / 126 pass on the base).

**Proving a buffer overflow / finding a stress position** (fable-review-buffix, 2026-10-28): build the test with
`-D_GLIBCXX_ASSERTIONS` added to CMAKE_CXX_FLAGS (std::array::operator[] then aborts on an out-of-range index; no
sanitizer needed on MinGW) against the fixed tree and against a mutant tree with the old size. To construct a
position with a given engine property (e.g. > 64 SEE-losing noisy moves), let the engine judge: a tiny census tool
linked from src/board.cpp + src/bitboard.cpp (`fable_review/tools/fable_census.cpp` on that branch) over a pipe,
driven by a python-chess annealer; a Python SEE overestimated the engine by 4-5 and `Board::set_fen` enforces a
piece inventory (promoted pieces <= 8 - pawns, 16 pieces, kings apart) that python-chess does not.

## 5. NPS (advisory only)
`nps_ab.py <exe_A> <exe_B> <runs> <depth...>` (copy in `opus_round1/sol_S29/nps_ab.py`): ABBA order, fresh
processes, nodes must match; reports wall and CPU-time NPS with 95% CI. On the loaded PC use nice 19 and quote
CPU-time NPS; the quiet CI runner is the cleaner measurement. Same-binary option ON/OFF: drive via UCI
`setoption` + `bench` (bench uses the global options). Never claim speed from one run.
- Per-side options: `opus-sol-SIT/opus_round1/sol_SIT/nps_ab_opts.py --opts-b Name=true <A> <B> 10 16 20`.
- **Speed-eligibility rule** (S11, S49): a speed change counts only if the 95% CI lower bound is ≥ +2% at d16 AND
  d20 (PC rule; the quiet runner is the proxy). Always quote the lower bounds next to the point estimates; a gain
  whose CI excludes 0 but whose lower bound is below +2% is "real but the rule is not met" (S14 zero-fill: +2.0 to
  +2.7%, lower bounds +0.85 to +1.90%). Run an A/A control (lock vs lock copy) on the same runner.
- Count before timing: if a change only saves work at a countable event (e.g. S12's null-edge alias: copies avoided
  per bench), multiply count × cost per event first. S12 predicted ~0.07% and the runner showed zero within ±0.4%.

**Same-exe option A/B (R7 J3, branch opus-r7-nps `opus_r7/j3/tools/`)**: `nps_opts_ab.py <exe> --runs N --depths 16 20
--set off= --set aa= --set tt=R7TtExclusive=true --json out.json` (fresh process per run, rotated order, bench 1 warm-up,
CPU time of the bench window via GetProcessTimes), then `nps_ci.py a.json [b.json] --ref off --sets tt aa` (geometric
mean of paired ratios with a 95% t-interval; pool files). Include the A/A set (`aa=`): on the loaded PC it read
-0.02% [-2.24, +2.25]. Pin it with `run_pinned.py --mask 0x0FFF` (keeps CPUs 12-15 free for self-play).
`identity_opts.py <exe> --full --opt Name=value ...` is uci_check with options set first.
**Profiles on a quiet runner**: `.github/workflows/opus-r7-prof.yml` (push to opus-r7-nps touching
`opus_r7/j3/ci/**`): callgrind bench 13 (self/inclusive), perf bench 16, FORGE_PROF counters, and per option set in
`opus_r7/j3/ci/prof_options.txt` the bench-13 nodes (must match) and callgrind instruction totals.
**MinGW gotcha**: `thread_local` is emulated (`__emutls_get_address` call per access) in the PC build; the TT's
`lock_stripe()` paid it on every probe/store (R7TtExclusive removes it: +3.6-4.0% NPS on the PC).

**NNUE width cost without training a net** (S-C4): the hidden size is compile-time (`-DFORGE_NNUE_HIDDEN`).
`opus-sol-SC4/opus_sc4_widen_inc.py` zero-pads the lock net to any wider H. That is function-preserving: the
H1024 build passes every lock pin, and nodes match in every A/B run. Build it with
`opus-sol-SC4/build_pc_hidden.sh` (`FORGE_HIDDEN=<H>`). Measured float path, CPU NPS vs H256 at d16/d20:
H512 −9.5/−9.8%, H768 −15.7/−17.6%, H1024 −22.8/−23.7%, about +10% node time per extra 256 units.
Per-stage NNUE costs: S37's `forge_nnue_microbench` (search-case static eval ≈ 403 ns AVX2, HCE 57%).

## 5b. NNUE v3 / NNUEArch changes (FB1, 2026-10-28)
See [[forge-nnue-v3]] for the full recipe: box build with `FORGE_EXTRA_SRCS="src/nnue_v3.cpp src/search_v3.cpp"`,
OFF identity, `forge_nnue_v3_tests <dir> 1000000` on the x86-64-v3 and znver5 test trees (0 mismatches, every
kernel == scalar), tool parity against `fable_nnue_v3.py compare` and `fable_nnue_train.py parity`, ON bench node
counts equal between the AVX2 and AVX-512 exes, NPS with `fable_nnue_nps.py` (trained or widened nets only).
`g++`/`cmake` need `/c/msys64/ucrt64/bin` on PATH; an absolute g++ path exits 1 with no message.

## 6. Codegen (when "hot code unchanged" matters)
`opus_round1/sol_S29/codegen_compare.sh` / O3's tooling: compare objdump of hot functions vs the lock.

Report every number with its log path; keep logs under `opus_round1/<job>/logs/`.
