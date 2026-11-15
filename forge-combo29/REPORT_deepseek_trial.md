# REPORT - deepseek trial

Machine: Linux 6.12.113+ x86_64, 4 vCPU, Intel Xeon (AVX-512F/BW/VL, BMI2 present).
Compiler used: `g++-13` (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, target
`x86_64-linux-gnu`, C++20 (`-std=c++20`), standard library **libstdc++** from GCC 13
(`/usr/lib/gcc/x86_64-linux-gnu/13/libstdc++.so`), numpy 1.26.4, python-chess 1.11.2,
Python 3.12.3, CMake 3.28.3. Full record: `tests_deepseek_trial/step1/environment.txt`.

Source: commit `6b98f217` (tip of `for-fable-and-opus/astra-0017-v3-path`).
Branch used for this work: **`for-fable-and-opus/deepseek-trial`** (started from that
commit). No file under `forge-combo29/src`, `forge-combo29/include` or
`CMakeLists.txt` was changed; every new file is under
`forge-combo29/tests_deepseek_trial/` plus this report.

## 1. Table

| step | done / partly / not done | evidence files | result in one line |
|---|---|---|---|
| START.md committed first | done | `tests_deepseek_trial/START.md` (commit `cd03b2bcb`, before any build) | three lines: what I understood, what I do first, which branch |
| 1. optimised build with `FORGE_NNUE_V3=1` + three runs | done | `step1/configure.log`, `step1/build.log`, `step1/flags.make.txt`, `step1/bench11.txt`, `step1/bench13.txt`, `step1/perft5.txt`, `step1/configure-failed-clang.log`, `step1/COMMANDS.md` | bench 11 = **312866**, bench 13 = **862329**, perft 5 = **4865609**: all three match the PC exactly |
| 2. random FORGENN3 net | done | `step2/COMMANDS.md`, `step2/netgen-command-output.txt`, `step2/load-check.txt`, `step2/fable_nnue_v3.py.txt`, `step2/netgen-reproducibility.txt` | 6309096 bytes, sha256 `e3ef99b7...8b375`, loads and reports `kernel avx512` |
| 3. 500 legal positions, seed 20261115, 8-60 plies | done | `step3/positions.txt`, `make_positions.py`, `step3/generator-output.txt`, `step3/checkcount.txt`, `step3/COMMANDS.md` | 500 unique valid positions, 0 game-over, ply 8..60 |
| 4. TSan build + Threads 2 and 4 runs | done | `step4/configure.log`, `step4/build.log`, `step4/flags.make.txt`, `step4/tsan-cc.sh.txt`, `run_tsan_positions.py`, `step4/tsan-t2.stdout.log`, `step4/tsan-t2.stderr.log`, `step4/tsan-t4.stdout.log`, `step4/tsan-t4.stderr.log`, `step4/COMMANDS.md` | 500/500 positions both runs, exit code 0 both, **0 TSan reports**, net loaded, no `ERROR NNUE v3` |
| 5. read the TSan output | done (nothing to group) | `step5/README.md`, `step5/tsan-positive-control.txt`, `step5/tsan-armed.txt`, `step5/gdb-v3-hit.txt`, `step5/gdb-v3-helper-threads.txt`, `step5/threads-node-growth.txt` | no reports at all, so no groups: no report count, no stack tops, no frame in `nnue_v3.cpp` or `Worker::static_evaluate_v3` was ever named by the tool |
| supplementary: depth 12 instead of 8 at Threads 4 | done | `step4/tsan-t4-depth12.stdout.log`, `step4/tsan-t4-depth12.stderr.log`, `step4/tsan-t4-depth12.driver.log` | 500/500 positions, exit code 0, **0 reports**, 500 `info depth 12` lines, 796 s of searching |
| supplementary: repeat Threads 4/depth 8 after a relink | done | `step4/tsan-t4-relinked.stdout.log`, `step4/tsan-t4-relinked.stderr.log` | 500/500, exit 0, **0 reports** - same result with the binary as it stands in the tree |

## 2. Minutes used per step (own clock, UTC)

Clock start 09:06, evidence cut-off 09:56.

| step | from - to | minutes |
|---|---|---|
| reading CMake/`nnue_v3.cpp`/generator, START.md, branch | 09:06 - 09:07 | ~1 |
| step 1 (configure, build, bench 11, bench 13, perft 5) | 09:07 - 09:08 | ~2 |
| step 2 (net) | 09:08 - 09:09 | ~1 |
| step 3 (500 positions) | 09:08 - 09:09 | ~1 |
| step 4 (TSan build + both 500-position runs) | 09:08 - 09:12 | ~4 |
| step 5 + verification that the clean result is real | 09:12 - 09:16 | ~5 |
| supplementary depth-12 pass (ran in the background) | 09:12 - 09:26 | ~14 background |
| writing evidence files and this report, commits | 09:16 - 09:29 | ~13 |
| **total elapsed at the time of writing** | 09:06 - 09:29 | **~23** |

The steps were not sequential: the depth-12 pass ran in the background for 13
minutes while I read code and wrote evidence, which is why the sum of the small
steps is smaller than the elapsed time. Run times measured by the driver itself:
Threads 2 depth 8 = 46.0 s, Threads 4 depth 8 = 43.1 s, Threads 4 depth 12 =
795.7 s (13 min 16 s).

## 3. What I did not do

- I did not group TSan reports, because there were none. Step 5 is reported as
  "nothing to group", not as an analysis.
- I did not run the build under ASan or UBSan. The job says the PC already ran
  those clean and that TSan is the missing check, so I spent the hour on TSan.
- I did not test Threads 1, 3, 8 or any thread count other than 2 and 4, except
  for the depth-12 node-count comparison which also used 1 and 2.
- I did not test `FORGE_NNUE_V3_VERIFY=1`. The job asked for it to be off.
- I did not change any engine source and did not need to; the one build problem
  (Clang has no `libstdc++` dev symlink on this image) was solved by choosing
  `g++-13`, and the `-O3`-after-`-O2` ordering problem was solved with a compiler
  launcher, both recorded in `step1/COMMANDS.md` and `step4/COMMANDS.md`.
- I did not verify that the 500 positions exercise every NNUE v3 code path
  (king-bucket change, output-bucket change, mirrored flip). I only know the
  positions are legal and varied.
- I did not investigate whether the clean TSan result holds for hash sizes other
  than 16 MB, or for longer searches than depth 12.
- I did not read the `FABLE_TO_deepseek_1.md` handoff: it does not exist on
  `handoff/fable-opus-combo29-all-20261114` yet (no path on that branch matches
  `deepseek`), so there was nothing there for me to read.
- I did not run the job's exact depth-8 protocol under ASan/UBSan or under a second
  sanitizer combination; only TSan as asked.
- I wrote the engine's TSan logs with `halt_on_error=0`, so a report would not have
  stopped the process. Because there were zero reports this made no difference
  here, but it is a choice I made and it differs from the default.

## 4. What I am not sure about

- **The clean TSan result is the main thing to be sceptical about.** 0 reports
  across 1000 searches is a strong statement. I defended it in
  `step5/README.md` by showing the sanitizer catches a known race on this machine,
  that `libtsan.so.2` is linked and `TSAN_OPTIONS=help=1` is answered by the engine
  binary, that all 9 object files are instrumented, that `forge::nnue::v3::evaluate`
  is really reached, that it is reached from helper threads (three of four workers
  had `emit_info=false` at Threads=4), and that node counts grow with thread count.
  Even so, TSan only reports races whose accesses it actually observes, and a race
  that needs a rarer interleaving than depth-8/depth-12 searches produced would
  not be seen.
- **I am not sure depth 8 is a demanding enough test.** Depth-8 searches finished
  in about 90 ms each; a search that short may not overlap workers much. I ran a
  supplementary depth-12 pass at Threads 4 over the same 500 positions to widen the
  window: 500/500 positions, exit code 0, **0 reports**, 796 s of wall time, 500
  `info depth 12` lines (`step4/tsan-t4-depth12.*`). I still cannot say what depth
  would be enough.
- **The `-O2` requirement.** `CMakeLists.txt` puts `-O3` last, so I rewrote it to
  `-O2` with a wrapper on the compiler path. I verified this from the build system
  itself, not only from a hand-run compile: rebuilding `src/nnue_v3.cpp` under
  `strace -f -e trace=execve` shows the real `cc1plus` executions with three `-O2`
  and no `-O3` (`step4/optimisation-flag-proof.txt`).
- **`perft` is a `go` subcommand.** A bare `perft 5` prints nothing at all. If the
  PC prints a perft line from a bare `perft 5`, then the PC engine differs from this
  source. I recorded my empty attempt as `step1/perft5-bare-attempt.txt`.
- **Whether the numbers matching is meaningful for the race test.** Node counts
  matching the PC means the search is deterministic here, which is good, but it
  does not by itself say anything about thread safety.

## 5. Model name and version as I know it

I am DeepSeek V4.1 Flash (the model identifier given to me for this run is
`deepseek-v41-flash-1017`), running as a Cursor cloud agent. I do not have a more
precise build number than that.
