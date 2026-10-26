# B shared-core ASan/UBSan profile — prepared, not executed

This is a new build profile/cache. `BUILD_SHARED_LIBS=ON` shares one instrumented
`libforge_core.so` among the13 executables. RelWithDebInfo is explicitly overridden
to `-O2 -g0 -DNDEBUG`: `-g0` removes DWARF storage, not sanitizer instrumentation.
All21 translation units still require ASan+UBSan, frame pointers, C++20, H256,
x86-64-v3/znver5 and strict floating point. The eight core TUs additionally require
PIC. Existing source/CMake files and all previous tools/artifacts remain unchanged.
No binary identity or inherited native pass is claimed for this profile. Its
actual artifact footprint is unmeasured; 30MB is not promised.

The adapter imports the frozen43c B adapter and its immutable85acc owned-group
subreaper/cleanup and8MiB active STOP/deadline guard. It permits CPU0/nice19 only,
maximum600 seconds, and exclusive new receipts. `first2` builds forge and
forge_prof_tests; `all` covers all13 fixed targets. A resume must bind the same
profile, source freeze/cache, reaped command ledger, coreSO and executable hashes.
Every configure/build/readelf command has a preserved owned-process receipt.
A pre-Popen guard pause has no child to reap and remains resumable; a spawned
unreaped child fails that check.

All21 TUs and14 link recipes are audited, with shared/PIC/SONAME flags on the
core and both sanitizer link flags on all executables. Before any future runtime,
`readelf -W -d` records NEEDED/RPATH/RUNPATH/SONAME and binds each runtime artifact
hash. No `ldd` or engine execution is used. Loader paths, when present, must point
only to the private build; the core SONAME is exactly libforge_core.so. The source
of nearest_pawn_tests uses only inline geometry helpers, so that one executable
may legitimately omit the core NEEDED entry under --as-needed. Every executable
still has its sanitizer compile/link audit; the shared core must depend on both
ASan and UBSan. Its14-artifact manifest is complete only after stage all and all
dynamic audits finish.

After the separate root grant and independent review, ready build argv is:

```text
nice -n 19 taskset -c 0 python -B /workspace/forge-pack24-20261026/S08/forge_sol_S08_B_asan_shared_build_20261026.py
  --execute --s26-timing-closed --authorization-reference ROOT_FRESH_SHARED_ASAN_GRANT
  --source-freeze /workspace/forge-pack24-20261026/S08/forge_sol_S08_B_v2_source_freeze_20261026.json
  --window-dir /workspace/forge-pack24-20261026/S08/forge_sol_S08_B_ASAN_SHARED_NODWARF_window1_20261026
  --build-dir /workspace/forge-pack24-20261026/S08/forge_sol_S08_B_ASAN_SHARED_NODWARF_window1_20261026/build
  --stop-file /workspace/forge-pack24-20261026/S08/forge_sol_S08_B_ASAN_SHARED_NODWARF_ROOT_STOP_20261026
  --stage all --max-seconds 600
```

A later authorized resume uses a NEW window, the same build directory and
`--resume-from` the closed forge_sol_S08_B_shared_ASAN_build_result_20261026.json.
No automatic native first invocation occurs. Root must bind both forge and
libforge_core.so hashes and execute a separate FIRST bare bench11 before UCI.
Future runtime children must receive only the exact private build as
LD_LIBRARY_PATH and have LD_PRELOAD removed; do not globally export either.
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 and
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 retain the prior checks. Use the
approved execution context permitting LeakSanitizer thread inspection; prior
sandbox EPERM diagnostics are preserved and are not worked around by disabling
leak checks. Full16 registered CTest and the separately approved native samples
remain necessary. NNUE disassembly checks must inspect the shared core/object;
the executable alone no longer contains all core implementations.

Preparation performed pure tests only. One initial full-recipe test accidentally
removed PIC from its sorted bench row rather than a core row; that test-fixture
failure is retained. The corrected core-row test and the receipt-ledger/prelaunch
resume regression each have preserved RED/GREEN evidence. No compiler, native
engine, CTest, shared object loader or project Git operation was launched.
