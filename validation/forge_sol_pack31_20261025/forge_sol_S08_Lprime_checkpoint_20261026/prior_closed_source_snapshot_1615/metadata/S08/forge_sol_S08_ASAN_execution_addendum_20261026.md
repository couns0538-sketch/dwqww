# S08 ASan+UBSan execution addendum — PREPARED, NOT EXECUTED

The authoritative Std requirement is a clean **full registered ASan+UBSan CTest
suite**, with the same four documented KNOWN findings and zero new FAIL. For
the current Lprime ON source this is15 CTest cases; qualified B ON is16 including
its bad-capture test. The older sampling-only proposal is preserved as history.
The targeted samples below supplement full CTest and never replace it.

No sanitizer configure, compiler, engine or CTest has been run for this adapter.
Root must first grant execution after all five S26 timed operations have closed.
Concurrent ordinary ON fixed-depth/node correctness on CPU4 is then acceptable
while sanitizer compilation uses CPU0, since NPS/timing are explicitly unused.

`forge_sol_S08_sanitizer_build_20261026.py` imports the immutable85acc subreaper
controller. It reuses its owned process groups, current-process subreaper,
bounded descendant waitpid cleanup, raw captures and deadline handling. It does
not copy that cleanup implementation. All old supervisors remain unchanged.

The adapter uses a separate NEW build cache, RelWithDebInfo (`-O2 -g -DNDEBUG`),
FORGE_ENABLE_SANITIZERS=ON, FORGE_PROF=ON, FORGE_NATIVE=OFF and IPO=OFF. Every
generated C++ TU must retain C++20, H256, x86-64-v3/znver5, fno-fast-math and
ffp-contract=off, plus address/undefined sanitizer and frame-pointer flags.
Every executable link recipe must include both sanitizer runtimes. Missing
debug/sanitizer flags, Release/O3, unsafe math and foreign TUs fail the audit.

Stage `first2` builds only forge then forge_prof_tests. Stage `all` resumes the
remaining fixed C++ targets needed for full CTest, plus forge_bench. Qualified
B source automatically adds its existing forge_bad_capture_tests target. The
source-freeze digest, profile, build root and completed artifact digests prevent
mixing Release and sanitizer caches. No built executable is executed by this
adapter.

An active guard samples free bytes before launch and every owned-child poll;
below8MiB it stops, reaps and preserves the partial build. A root STOP file and
the global owned deadline also pause the build. The minimum observed free space
is retained. This is an operational polling guard, not an assumed artifact-size
bound. Cache-size audit found the closest historical S25v2/S05v2 sanitizer
caches contain metadata but no Forge ELF/object payload. Their small residual
sizes do **not** estimate S08 sanitizer artifact needs; complete footprint is
UNKNOWN until the staged build measures it. No guessed capacity figure is used.

After a fresh root grant, first-stage argv is:

```text
nice -n 19 taskset -c 0 python -B forge_sol_S08_sanitizer_build_20261026.py
  --execute --s26-timing-closed
  --authorization-reference ROOT_FRESH_ASAN_BUILD_GRANT
  --source-freeze /workspace/forge-pack24-20261026/S08/forge_sol_S08_ON_build_source_freeze_20261026.json
  --window-dir /workspace/forge-pack24-20261026/S08/forge_sol_S08_ASAN_window1_20261026
  --build-dir /workspace/forge-pack24-20261026/S08/forge_sol_S08_ASAN_window1_20261026/build
  --stop-file /workspace/forge-pack24-20261026/S08/forge_sol_S08_ASAN_ROOT_STOP_20261026
  --stage first2 --max-seconds 150
```

For the later full stage use a NEW window2, the same sanitizer build-dir, a
fresh root authorization reference, `--stage all`, and `--resume-from` pointing
to window1/forge_sol_S08_ASAN_build_result_20261026.json. Resume a partial
first stage in the same manner; never reuse the Release build cache.

Mandatory native order after compilation, under root's separate runtime grant:

1. **First ASAN engine execution:** a separate process receiving only bare
   `bench 11` then `quit`, before UCI; require308972, rc0, normal EOF and no
   sanitizer/stderr diagnostics. Preserve this original capsule.
2. Record actual CTest registration and run the full suite, not a filtered
   subset: `ctest --test-dir BUILD --output-on-failure -j1` with
   ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 and
   UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1. Preserve all outputs/XML and
   assess all15 current Lprime ON cases (16 for qualified B), four KNOWN/zero new
   FAIL. No sanitizer diagnostic is allowed.
3. Additional samples: profile/counter fixture, TT/correction/runtime-PSQT
   checks, startpos perft4, WAC.001–025 at20000 nodes each with fresh state, and
   Threads2 fixed-node start/stop/clear/Profile-toggle lifecycle. No movetime or
   other clock search limits. ASan/UBSan are not race detectors; the reviewed
   atomic/TLS/join protocol and native concurrent fixture remain separate evidence.

Source/net/compiler/config/TU/link/ELF hashes, deadlines, all failures and every
partial build are retained. Artifact sizes observed after first2 determine the
actual storage plan for the remaining suite. No strength, speed or NPS claim is
authorized by these correctness checks.
