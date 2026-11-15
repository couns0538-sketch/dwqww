# Step 4 - ThreadSanitizer runs

## Build

`CMakeLists.txt` is not mine to change, and it appends `-O3` *after* anything in
`CMAKE_CXX_FLAGS`, which would silently override the `-O1`/`-O2` the job asks for.
A two-line compiler launcher (`tsan-cc.sh.txt`) rewrites `-O3` to `-O2` and passes
everything else through unchanged, so the source and the CMake file are untouched.
The rewrite was confirmed by running the launcher directly with `-v` and reading
the `cc1plus` line, which ends in `-O2`.

```
cmake -S /agent/repos/dwqww/forge-combo29 -B /tmp/ds/build-tsan \
      -DCMAKE_CXX_COMPILER=/tmp/ds/tsan-cc.sh \
      -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_V3=1 -fsanitize=thread -fno-omit-frame-pointer -g -O2" \
      -DCMAKE_EXE_LINKER_FLAGS="-fsanitize=thread"
cmake --build /tmp/ds/build-tsan -j4
```

`step4/flags.make.txt` shows the requested flags. `FORGE_NNUE_V3_VERIFY` is not
passed and `search.cpp` defaults it to 0, so it was off.

## The two runs

Driver: `run_tsan_positions.py` (committed). It keeps stdout and stderr in
separate files so TSan output is not mixed with search output, and it blocks on
each `bestmove` before sending the next `position`.

```
TSAN_OPTIONS="halt_on_error=0 second_deadlock_stack=1" \
python3 -I run_tsan_positions.py /tmp/ds/build-tsan/forge \
        /tmp/ds/netgen/random_h512.fnn3 /tmp/ds/positions.txt 2 8 \
        /tmp/ds/tsan-t2.out /tmp/ds/tsan-t2.err
```

and the same with `4` for Threads. `halt_on_error=0` means TSan keeps going after
a report instead of stopping the process, so one run can surface more than the
first race.

## Results

| run | positions searched | exit code | TSan reports | wall time |
|---|---|---|---|---|
| Threads 2 | 500 / 500 | 0 | 0 | 46.0 s |
| Threads 4 | 500 / 500 | 0 | 0 | 43.1 s |

Raw: `tsan-t2.stdout.log` (433486 B), `tsan-t2.stderr.log` (**0 B**),
`tsan-t4.stdout.log` (437987 B), `tsan-t4.stderr.log` (**0 B**). Both logs are
under 1 MB, so no truncation was needed. sha256 of both stderr logs is
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, the hash of
the empty file.

No `info string ERROR NNUE v3` line appeared: the net loaded in both runs, and
the first stdout line of each run is the `NNUE v3: loaded ...` message.

## Why I believe the clean result is not vacuous

A silent sanitizer is worthless if it was not armed, if the code was not
instrumented, or if the searches never overlapped. I checked all three:

1. **Sanitizer works on this machine.** A known-race C program (`race.c`, two
   threads incrementing one global) built with `gcc-13 -fsanitize=thread` reports
   `WARNING: ThreadSanitizer: data race` (`step5/tsan-positive-control.txt`).
2. **This binary is armed.** `ldd build-tsan/forge` shows `libtsan.so.2`;
   `TSAN_OPTIONS=help=1` makes the engine print the full TSan flag list to stderr,
   and the release binary prints nothing for the same environment
   (`step5/tsan-armed.txt`). Every one of the 9 object files references
   `__tsan_*` symbols.
3. **The v3 code really ran, on a helper thread.** Under `gdb`, a breakpoint on
   `forge::nnue::v3::evaluate` is hit from `Worker::static_evaluate_v3` on a
   non-main thread (`step5/gdb-v3-hit.txt`). `strace -f -e clone` on a Threads 2
   search shows the engine creating helper threads
   (`step4/strace-clone-threads-t2.txt`), and the node counts for the same
   position grow with Threads (8002 / 29550 / 53872 at depth 12 for 1 / 2 / 4),
   which is the signature of real parallel search rather than helper threads
   that are created and ignored.
4. **No search was cut short.** Both stdout logs contain exactly 500 `bestmove`
   lines and exactly 500 `info depth 8` lines, and the maximum reported depth is
   8, so the driver never sent a command while a search was running.
