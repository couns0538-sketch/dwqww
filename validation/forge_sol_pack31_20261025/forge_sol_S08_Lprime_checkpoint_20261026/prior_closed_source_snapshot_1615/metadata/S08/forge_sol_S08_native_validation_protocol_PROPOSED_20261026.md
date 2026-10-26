# S08 native validation protocol — proposed, NOT LAUNCHED

Root must coordinate resources and freeze actual command paths before launch.
No full Forge build, engine search, timing run or corpus collection was run by
this source-review pass. The earlier standalone counter/TLS fixture is separate.
S26 owns CPU4. Do not overlap S26's exclusive WAC/native phase with any build,
sanitizer run or S08 engine execution.

## Frozen source inputs and patch

Canonical engine patch: `forge_sol_S08_profcounters_20261026.patch`, SHA256
`5c6310e7881bfb592feab981e132a6cf81a6080b45631f62a37e774ced5b6879`.
It contains nine engine/CMake/C++-test paths, three new-file mode100644 headers,
and unchanged RAW-v1 hunk bodies. README/IDEA_SOURCE appends remain separate.
`forge_sol_S08_source_apply_v1_20261026/result.json` proves git apply --check,
actual GNU patch -p1 -F0, reverse check, and OFF-source projection on L/Lprime/B.
The apply copies contain only touched files and are NOT complete build trees.

Complete source candidates must be NEW isolated copies of these originals,
patched exactly once. The existing complete private `S08/Lprime` is already
patched; do not apply again. Hash source/headers/weights/CMake before and after.

- L: `files/01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src`
- Lprime: `files/01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src`
- B: `files/01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src`

All three paths are beneath the supplied full-handoff `.../files/` root. No
original tree or existing build output may be changed. Preserve every failure.

## Exact build recipe

CMake executable:
`/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake`.
CXX: `/usr/bin/x86_64-linux-gnu-g++-14`, version14.2.0, current compiler SHA256
`6b3696e4dcb85e1c949c732a02befa50e3983ecf94ce7e8e58d9d503b954b79d`.

For every complete candidate source, reserve separate NEW build directories
`L_OFF`, `L_ON`, `Lprime_OFF`, `Lprime_ON`, `B_OFF`, `B_ON` in a root-approved
output root. No copy of the tiny apply trees is a valid build source.

Each configure command is the following argv, replacing only SOURCE and BUILD:

```text
CMAKE -S SOURCE -B BUILD
  -DCMAKE_BUILD_TYPE=Release
  -DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-14
  -DFORGE_NATIVE=OFF
  -DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256
  -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

OFF: omit FORGE_PROF to test its actual default; verify cache FORGE_PROF:BOOL=OFF.
ON: append exactly `-DFORGE_PROF=ON`. Build one case at a time with
`CMAKE --build BUILD --parallel 1 --verbose`. Capture every generated compile
command, flags.make and link.txt. Enforce C++20, H256, strict float on every
production TU; no native ISA toggle, fast-math, LTO, IPO or PGO. The ON recipe
adds only src/profile.cpp and FORGE_PROF=1. The OFF recipe must include neither.
S27's recipe guard must explicitly account for this ON-only TU/definition; do
not silently discard unfamiliar TUs to obtain a PASS.

Default OFF whole-executable expected SHA256:

| Source | Expected SHA256 |
|---|---|
| L/Lprime | e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b |
| B | 55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406 |

Require byte identity and no defined forge::prof symbols, Profile option or
bench_prof command literal in OFF. ON has exactly one added UCI option:
`option name Profile type check default false`; other option/ID rows stay equal.

## First runtime and node references

The FIRST execution of each fresh engine is a separate process receiving only
`bench 11` then `quit`, before any UCI setup. Require308972 nodes, rc0, empty
stderr and normal EOF. A failing first signature stops that build's qualification.

| Depth | Required nodes |
|---:|---:|
| 11 | 308972 |
| 13 | 745494 |
| 16 | 2460422 |
| 20 | 11901452 |
| 22 | 31111774 |

OFF: the ordinary bench sweep must match every reference. Exact canonical ELF
inheritance may avoid repeated non-first OFF sweeps only if root records the
identical source/ELF/recipe and the prior immutable receipt; never label an
inherited run fresh. ON: run `bench_prof D` at all five depths. Each must match
both the final summary and prof.nodes, with main+qs=nodes, TT hits+misses=probes,
all15 picker stage visits=picker_visits, overflow=false. No substitute reduced
depth is a five-reference PASS. Record all55 counters and complete output.

## UCI lifecycle and S25 output contract

Use an event-driven pipe controller with an operational watchdog, not sleeps or
movetime search limits. Threads1/Hash16/OwnBookfalse. Test Profile true go nodes
10000; exactly one55-event packet must precede bestmove. Set Profile false after
quiescence and repeat: no profile output. Re-enable, start go infinite, wait for
a completed info-depth event, then setoption Profile false: existing stop/join
must finish the old enabled search and publish its packet before bestmove; the
next search is disabled. Repeat Threads2 with fixed nodes and assert accounting
and normal termination, not deterministic SMP node counts. Reset/snapshot only
before launch/after all worker joins; never sample an active bank as complete.

Run S25 unchanged against plain bench on OFF and ON/default-false:

```text
python -B /workspace/dwqww/releases/forge_sol_pack31_20261025/S25_v2/forge_sol_S25_outcontract_20261025.py ENGINE --out NEW_S25_OUTPUT
```

For bench_prof, its explicit profile prefix is validated separately. The final
unchanged bench summary must be the last bytes before EOF when input is
`bench_prof D` then `quit`. No late profile, log, blank line or diagnostic is
permitted. Collector's explicit isready fence may produce one readyok only;
all other post-terminal bytes fail. Do not loosen S25's plain-bench grammar.

## CTest, perft, FMA and sanitizer sampling

After the first numeric gate build all registered targets and record `ctest -N`
from the actual tree. Run full `ctest --test-dir BUILD --output-on-failure -j1`.
Lprime currently registers14 original tests; B adds its bad-capture test (15).
ON adds forge_prof_tests, so expected totals are15/16 respectively when Python
is detected. Require the exact current Lprime/B four documented KNOWN findings
and zero unexpected FAIL; do not convert older L test expectations into new
Lprime/B baselines. Preserve test names/counts and current tests.cpp hash.

Require canonical perft5 startpos4865609 and Kiwipete193690690; NNUE-scoped and
whole-executable/object FMA count0 with the frozen S05 checker. Byte-identical
OFF evidence can be inherited explicitly; ON evidence is fresh.

Create a separate NEW ASan+UBSan ON build using the same compiler, C++20/H256 and
strict-float recipe, `-DCMAKE_BUILD_TYPE=RelWithDebInfo`,
`-DFORGE_ENABLE_SANITIZERS=ON`, `-DFORGE_PROF=ON`; retain sanitizer compile/link
evidence. Set ASAN_OPTIONS=detect_leaks=1:abort_on_error=1 and
UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1. Bounded sample: prof_tests,
TT/rule50/correction/runtime-PSQT test targets, plain/bench_prof11, startpos perft4,
WAC.001–025 at20000 nodes each/Threads1 with fresh state, and Threads2 startpos
fixed-node start/stop/clear/profile-toggle lifecycle. No sanitizer diagnostic is
allowed. ASan/UBSan are not race detectors; race assurance also relies on the
reviewed atomic/TLS/join lifecycle and native concurrent fixture.

## Fixed-work advisory collection and corpus shortfall

After all qualification gates, root may schedule one original limited screen:

```text
python -B forge_sol_S08_collect_profiles_20261026.py
  --engine ABSOLUTE_QUALIFIED_ON_ENGINE
  --suite /workspace/forge-sol-next-20261024/int16-review/wac300.epd
  --output NEW_PROFILE_OUTPUT --nodes 50000 --required 2000 --allow-incomplete
```

This performs first bare11, explicit bench_prof20 and all300 genuine positions,
with fresh ucinewgame/hash/history for each. Fixed work avoids timer-induced
selection from instrumentation overhead. Preserve full stdin/stdout/stderr,
per-process rc, source/exe/corpus hashes,55-counter packets and separate bench/
corpus tables. Frequencies<0.1% are ADVICE, not dead-code, speed or strength proof.
Record maximum observed counter and overflow=false; do not claim an arbitrary
infinite-run overflow bound. Only300 distinct genuine WAC positions exist;
1700 WAC/STS positions remain missing. A limited screen never satisfies the
requested2000-position acceptance requirement and must remain labelled so.
