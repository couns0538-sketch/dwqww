# S12 deferred native qualification, 2026-10-26

Status: every native step below is UNVERIFIED. Do not execute while S10/S11
ordered work is active. This document grants no CPU lease. No advisory timing
may overlap another native workload. This is a correctness/performance candidate,
not an accepted integration or an Elo result.

Inputs: unchanged L/Lprime/B from forge_sol_S12_source_binding_20261026.json.
Use review-v2 patch SHA256
66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d.
The v1 patch 88a789a6... is preserved as a superseded source-review attempt.
It is not an additional feature and must not be applied before v2.

First bounded native action after a new root grant: adapt the already qualified
S11 build-only adapter's input binding to the S12 six-file source diff; retain its
owned-process subreaper, j1, pinned CPU/nice19, closed-child/owned-RSS checks,
source hashes before/after, strict compile/link token audits, and original full
target discovery. No new build framework is needed. Create a NEW full private
LP candidate source copy, apply v2 with zero fuzz, and build the default OFF
configuration in a NEW /tmp output. A build failure stops that arm and preserves
all stdout/stderr. Never mutate the accepted integration tree or supplied input.

Exact CMake/compiler argv for the adapter (paths are local future output paths):

```bash
/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake \
  -S /tmp/forge_sol_S12_native_20261026/LP_candidate_source \
  -B /tmp/forge_sol_S12_native_20261026/LP_buildoff_release/build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/x86_64-linux-gnu-g++-14 \
  '-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256' \
  '-DCMAKE_CXX_FLAGS_RELEASE=-O3 -DNDEBUG' \
  -DBUILD_SHARED_LIBS=OFF -DFORGE_NNUE_LAZY_ACC=OFF \
  -DFORGE_ENABLE_SANITIZERS=OFF -DFORGE_NATIVE=OFF \
  -DFORGE_EXPOSE_TUNABLES=OFF -DFORGE_BUILD_VALIDATION_TOOLS=OFF \
  -DFORGE_BUILD_TUNING_TOOLS=OFF \
  -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/cmake \
  --build /tmp/forge_sol_S12_native_20261026/LP_buildoff_release/build --parallel 1 --verbose
```

The argv must execute via the owned bounded adapter, not an unbounded interactive
shell. Maximum build wall clock 900s, compiler RLIMIT_AS <=4GiB, owned RSS <=4GiB,
minimum start free disk 128MiB, stop floor32MiB. Compiler/build source-recipe
closure must be audited before an ELF is run. Artifact manifest includes every
original target, core archive, compile_commands.json, and custom test/helper.

Repeat baseline and candidate for LP/B, and candidate build-switch ON/runtime
OFF and ON. Do not include S11's material-key optimization or S09's heads as an
implicit dependency. Source-copy field set must differ in exactly six declared
files. The patch also applies to L, as the completed source-only checks show;
native L qualification is optional only if parent explicitly chooses it.

FIRST execution of EACH new main engine ELF: send exactly `bench 11\nquit\n`,
without UCI, setoption, helper, CTest or timing first. Require308972 nodes and
normal owned-process closure. For an enabled build this first run remains runtime
OFF. Then record binary SHA256 and inspect full UCI output. Build-switch OFF UCI
must match baseline, while build-switch ON may add only the OFF NnueLazyAcc option.

Five bench totals, never inferred from a candidate baseline: d11=308972,
d13=745494,d16=2460422,d20=11901452,d22=31111774. Check all for buildOFF,
buildON/runtimeOFF, and buildON/runtimeON; sequential fresh processes and fixed
Threads1 Hash16. For ON send these lines before each bench:

```text
setoption name NnueLazyAcc value true
bench 13
quit
```

The first ON search that really evaluates NNUE must print exactly one process-
once `info string NnueLazyAcc active`. ON per-search statistics precede the
terminal bench line. A repeated ON bench in the same process must not announce
active again. OFF, perft-only, or UseNNUE=false must not claim active/copies.

Both node oracles: startpos perft5=4865609; kiwipete5=193690690 for
`r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1`.
FMA=0 in all executed NNUE paths and whole engine disassembly. No SIMD/nnue.cpp
changes are expected, but inspect actual ELF rather than inferring zero.

Run full CTest, actual discovery LP14/B15, retaining only the four documented
known diagnostic lines. Additional failure or skipped target blocks acceptance.
Existing tests retain default OFF; dedicated actual-Worker native regression
exercises ON. Compile it against each actual core using identical compiler,
ISA, H256, float, optimization, and feature definitions as that core:

```bash
/usr/bin/x86_64-linux-gnu-g++-14 -std=c++20 -O3 -DNDEBUG \
  -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_LAZY_ACC=1 \
  -I/tmp/forge_sol_S12_native_20261026/LP_candidate_source/include \
  /tmp/forge_sol_S12_prepared_20261026/forge_sol_S12_lazyacc_native_regression_20261026.cpp \
  /tmp/forge_sol_S12_native_20261026/LP_buildon_release/build/libforge_core.a \
  -pthread -o /tmp/forge_sol_S12_native_20261026/LP_lazyacc_native_regression \
  -Wl,-Map,/tmp/forge_sol_S12_native_20261026/LP_lazyacc_native_regression.map
```

Audit the actual map binds exactly the intended archive; run only after new main
bare11 gate. Build this same original test against baseline with feature define
absent/0: it must fail actual copy-elision and skip-counter assertions while the
parity assertions remain valid. That RED native step is not yet performed.
Never reinterpret the pure Python model RED result as this native RED result.

Actual-Worker cases: null-null, null-real, real-null, unevaluated real/null replay,
sibling overwrite, same-ply eval, root restart/Worker clear, invalid owner PSQT
and poisoned child PSQT, en passant, white/black castling and underpromotions,
capture promotion, UseNNUE=false. Add a separate actual UCI Threads2 stop/join/
option-toggle/newgame stress using the existing owned UCI controller; verify
isolated per-worker owners and absence of sanitizer diagnostics/data races.

Parity: reuse S09's frozen original 1M FEN corpus SHA256
0d6594d3fb7dba38064eddc2a0f673d23c6551c052186cc5989047b86e762eb6
from the closed S09 corpus storage result. Rehash the retained raw corpus or
losslessly recovered equivalent before native use.
No new corpus generation. Compare baseline/OFF/ON actual API integer results and
fresh versus resolved incremental accumulator words; retain raw byte streams in
<100MiB gzip chunks. Root already knows the reusable original oracle. Null edges
must be deliberately exercised; FEN-only fresh evaluations cannot prove copy
elision or alias lifetime. Do not reuse the S11 material-key oracle blindly.

ASan/UBSan separate full static O2g builds of LP/B featureON, complete CTest and
ON dedicated regression/Threads2/perft. Keep LeakSanitizer ON. ASan runtime must
NOT inherit the compiler's RLIMIT_AS4GiB: use owned RSS<=4GiB and the existing
bounded process protocol instead. Runtime work/hard ceiling 600s, stop only
owned descendants, retain original failures; no live configuration edits.

Required report per each of the five benches and OFF/ON mode: actual root and
fallback refreshes, physical incremental updates, zero-dirty edges, copies
avoided, alias hits, NNUE eval count. BuildON/runtimeOFF SearchInfo counters are
available to a small actual benchmark API helper without changing OFF UCI stdout.
Do not call construction-call ratio an elapsed refresh CPU share. Counter-run
times are not advisory speed measurements. None of these counts has been run
for S12 yet.

Only after correctness gates and an exclusive compute lease: reuse existing
paired ABBA controller, >=10ABBA blocks per d13/d16, fixed settings and no outlier
deletion. Keep compiled-feature OFF versus ON and pristine baseline separate;
new layout/counter overhead may cost more than avoided copies save. Report no
speed claim until own-box and Windows decision protocol. No match/Elo claim.
