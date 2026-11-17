# STATUS — swarm/tsan

**State: complete. Result is a clean negative with the instrument recorded.**

## What it answers

A real ThreadSanitizer run of `forge-combo29` at `Threads 4`, replacing the 27 findings across 8 seats that
the audit's provenance census attributed to a "TSan build" with no flag set, no compiler line and no hash
(trap 30). Races only. **No timing is reported from any sanitized build.**

## Provenance

| Item | Value |
| --- | --- |
| Engine tree | `forge-combo29` @ audit base `6b98f217` |
| Compiler | `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` (`/usr/bin/g++`) |
| TSan runtime | `libtsan.so.2`, package `libtsan2 14.2.0-4ubuntu2~24.04.1` |
| CMake / Python | 3.28.3 / 3.12.3 |
| Build type | `Release`, `-DFORGE_MARCH=x86-64-v4`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13` |

Exact flags:

```
CXX_FLAGS = -fsanitize=thread -fno-omit-frame-pointer -g -ffile-prefix-map=<src>=/src -ffile-prefix-map=<build>=/build -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4
LINK      = /usr/bin/g++ -fsanitize=thread -fno-omit-frame-pointer -g -O3 -DNDEBUG -fsanitize=thread <objs> -o forge
```

```
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 \
      -DCMAKE_CXX_FLAGS="-fsanitize=thread -fno-omit-frame-pointer -g \
        -ffile-prefix-map=<src>=/src -ffile-prefix-map=<build>=/build" \
      -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread"
```

**Why the two `-ffile-prefix-map` flags are in the flag line:** `-g` embeds the source path *and* the build
directory, so without them the sha256 changes with the checkout path — the same source built in two build
directories gave `21189c77…` and `bbe13ccc…`. **A hash that moves is not a hash.** With the maps the build is
byte-reproducible across paths, and the digests below are reproducible ones.

**clang 18 cannot link a sanitized binary on this VM and was not used:** `cannot find
/usr/lib/llvm-18/lib/clang/18/lib/linux/libtsan-x86_64.a`, `…libclang_rt.tsan_cxx-x86_64.a`,
`cannot find -lstdc++`. TSan **was** available via g++ 13.3.0, so no substitute was made.

## Binary sha256 — engine and every mutant

All built with the flag line above (`-ffile-prefix-map` set per tree), so each digest is path-independent.

| Binary | sha256 | Purpose |
| --- | --- | --- |
| **TSan engine (under test)** | `889a9b467d77a8210e38f981ef8c00d1f77e8f8b4faaf9ae19406373c0751cfa` | the run |
| TSan + plant A (off-path global) | `b065465db9bbcd5edb6d3054721a76feaca3f65483006daac6c66d9b52e73cb7` | runner liveness |
| TSan + plant B (hot search path) | `07282fb8db180905eaf8b98650969ed630a0a6ce74fad03316bddbf815f0dcbb` | proves search threads observed |
| Startup harness, shipped tree | `5350d494420eeeba5a9128c4232df23a0caf7a0881df1ba28369d3fbecfa458b` | init clean (10/10) |
| Startup harness, reverted `init()` | `70cea38b2aeee8b678ae796b078413b63d306f8c110a469d2007b3fde85838c9` | init bug reproduced (10/10) |
| Un-sanitized base | `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` | pins + Threads 1/4 comparison |

The un-sanitized base digest independently reproduces the base binary digest recorded elsewhere in this audit.

## Result

- **147 searches at `Threads 4`, 0 ThreadSanitizer reports.** Cases A–H: depth 12 ×40, nodes 200000 ×40,
  `setoption Hash` ×20, `Clear Hash` ×20, MultiPV ×10, drawn root ×1, `go infinite`+`stop` ×8, Threads
  resize ×8. All 147 answered with a `bestmove`.
- **Every observed process exited 0 with 0 post-`quit` lines** (`evidence/exit_observation.json`,
  `EXIT_OBSERVED_FOR_ALL`). Both planted builds exit **66**, so exit status is an independent second signal
  agreeing with the empty race count.
- **Planted race caught twice**, at two levels: an off-path global (`g_planted_counter` named in the report),
  and an increment on `Worker::should_stop()` reached by the real helper threads — 13–24 reports whose stack
  shows `Searcher::search`'s helper lambda → `Worker::search` → `should_stop`.
- **Startup init fixed.** `std::call_once` at `src/bitboard.cpp:139-143`. 10/10 clean runs here; reverting
  `init()` gives 10/10 runs with a `SEGV` in `forge::attacks::bishop` on a null `Magic::table`. Do not
  re-report.
- **Four pins hold under TSan** (312,866 / 862,329 / 3,024,920 / 4,865,609). They **cannot see `Threads`** —
  `bench` builds its own `Searcher(16)` with the default `threads = 1`, so a matching pin is not evidence
  about the threaded path.

## Driver defect found and fixed in this seat

The first driver sent `quit` then called `wait()` **without draining the pipe**, so anything printed at exit
was lost — exactly the trap the brief names. That run was **discarded, not relabelled**. The fixed driver
drains to EOF before reaping and records `exit_code`; `evidence/drain_selftest.log` proves the fixed path
catches a post-`quit` report (1 report) and a naive driver loses it (0 reports).
`ThreadSanitizer: reported 25 warnings` + exit 66 on the planted build is the concrete case that would have
been missed.

## Withdrawn

All TSan wall-clock, nps and rate numbers from the prior body of work, including the ~1,000× outlier
(348,278 ms / 376,680 ms). Nothing in `FINDINGS.md` is a timing from a sanitized build. The two figures quoted
from the consolidated audit — `Threads 4` costs 1.24× wall at fixed depth, and `bench` ignores `Threads` — are
cited as given and marked as such; this seat independently confirmed the second and measured node ratios (not
wall time) that are consistent with the first.

## Code-quality gate (SonarCloud)

The PR's SonarCloud check failed on **Security Rating for New Code** with 10 annotations, all in this folder's
scripts, all one class: `argv` paths and executables went straight into `open()`, `shutil.rmtree()` and
`subprocess.Popen()`. One was genuinely dangerous — `plant_selftest.py` ran `shutil.rmtree()` on an
`argv`-supplied directory.

Fixed, not suppressed. `scripts/pathsafe.py` validates every command-line path and executable: writes must be
inside an allowed root, `rmtree` targets additionally refuse `/`, `/tmp` and anything shallower than 3
components, reads must exist, executables must be regular and executable. Roots default to this folder and
widen via `FORGE_AUDIT_ROOT` so the build script can use a temp work dir explicitly. The guard self-tests its
own refusals and acceptances (`evidence/pathsafe_selftest.log`), and was verified end-to-end against
`/etc/evil.json` and a `/etc/evil` plant destination.

Side benefit: `tsan_run.py` now records `exe_sha256` in its output, so each run JSON names the binary that
produced it.

## Not tested

`-D_GLIBCXX_DEBUG` (and therefore row `07-C38`), ASan/UBSan, Ponder/`ponderhit`, clock-driven searches, and
any corpus built specifically to widen race windows. Reasons in `FINDINGS.md` §5. Also: report *counts* on
racy builds vary run to run (13–24 for plant B, 2–20 for reverted init); the *presence* of a report was stable
and no claim depends on a count.

## Reproduce

```
scripts/build_and_run.sh <forge-combo29 tree> [build-dir] [evidence-dir]
scripts/drain_selftest.py
FORGE_EXE=<tsan engine> python3 scripts/exit_observation.py out.json
```

`build_and_run.sh` refuses to be useful without the self-tests: it runs the drain self-test, the exit
observation, and a planted-race build that must report a race before the clean run is accepted.
