# S25: strict bench/UCI output contract — 2026-10-25

Status: PASS for the test-only change. No engine/backend adoption, speed or Elo claim.

## Change and fixed authority

One CMake option, `FORGE_OUTPUT_CONTRACT`, is OFF by default. ON registers the native output-contract test and its parser controls. Production `src/` and `include/` are unchanged; no engine was rebuilt. A checked-in allowlist records the ten approved UCI options, including types, defaults and spin bounds, from the pristine L `src/uci.cpp`, before observing candidate output. Options are Hash, Threads, Move Overhead, Ponder, OwnBook, Book File, Book Depth, Book Variety, UseNNUE and Clear Hash.

The base is code `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` with the supplied explicit h256_e12 network overlay SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. B additionally has buffer-fix patch SHA256 `9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c`. This does not identify the raw base commit's embedded network as that overlay.

Patch: `forge_sol_S25_outcontract_20261025.patch`, SHA256 `a8317834664d249f4d549c29d5bd30975c0fe8058d713c466f4a23aee6a3e5b2`. Diffstat: five files, 208 insertions: CMakeLists.txt 17, IDEA_SOURCE.md 10, checker 76, approved allowlist 74, parser tests 31. Both pristine L and B passed actual dry-run and application with `patch --batch --forward --fuzz=0 -p1`, before CMake/native validation; no fuzz or offset was reported. The idea note uses a shared interior anchor and preserves B's existing appended notes.

The checker first sends only `bench 11` and `quit`, captures both streams through EOF and child exit, and requires the fixed depth-11 node count 308972. A valid bench summary has one LF or CRLF terminator and zero later bytes; time/NPS numeric fields may vary. Extra blank bytes, a stats line, duplicate/malformed summaries and missing terminators fail. A fixed-node pass allows a separate `uci`/`quit` process even if the tail failed, so both contract violations are reported. The typed allowlist rejects extra, missing, duplicated, malformed or changed options. No caller affinity, process killing or host limits are used.

## Completed checks

| Check | Result | Evidence |
|---|---|---|
| Patch F0 dry-run/application, L and B | PASS | patch_results and original command streams |
| Engine C++/header byte identity | PASS | patch_results and source bindings |
| Parser controls | PASS | 12 tests, including literal blank/stat tails, duplicate/malformed output and option metadata changes |
| L Release actual checker | PASS | first bare d11=308972, then approved UCI contract |
| B Release actual checker | PASS | first bare d11=308972, then approved UCI contract |
| L ASan+UBSan actual checker | PASS | canonical sanitized main; both child exits zero, stderr empty |
| B ASan+UBSan actual checker | PASS | canonical sanitized main; both child exits zero, stderr empty |
| Default CMake registration, L/B | PASS | no flag override: cache OFF and both new targets absent |
| ON CMake registration/new CTests, L/B | PASS | both new targets present; actual 2/2 passed on each |
| Exact shelved default-OFF negative | PASS (expected RED) | fixed d11 gate passes; checker exit1 reports both violations |
| Original full C++ Release/ASan qualification | PASS, inherited | unchanged canonical sources/main hashes bound to completed S00 receipts; not freshly rerun |
| Fresh five-depth/perft/FMA sweep | NOT RUN in S25 | unchanged qualified binaries retain their earlier source-qualified proof |
| Windows qualification, speed, Elo | UNVERIFIED / not claimed | outside this test-only job |

Canonical main SHA256s:

| Profile | SHA256 |
|---|---|
| L Release | e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b |
| B Release | 55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406 |
| L ASan+UBSan | 4fa3a1c34a95633a511e00674734c68a53773db1498c6df0df27cd3e3e349e9d |
| B ASan+UBSan | f842092e75c530b3899e8fc07cc2e14dcc0e0088253b2bd437ac590648fb863d |

The four positives, the shelf negative and two ON CTest invocations exercised 14 engine processes and preserve all 28 original stream records. The original C++ test source, expectations and four known FAIL lines remain unchanged. The new CMake builds were configured and their new tests ran against copied, hash-identical qualified engine ELFs; they are not fresh complete C++ builds or fresh full CTest/ASan matrices.

## Actual negative and reproducibility

The authorized shelf patch is SHA256 `e661a145e301d3483ccaeaba65779d1d2002067263c836250e6418b9dccd151d`, applied to private L only. Every compiled engine/header source and the CMake/source documentation matched the existing native fixture; `FORGE_NNUE_EXACT_INT32_AVX2:BOOL=OFF`, with no backend define. Its ELF SHA256 is `f4365f194f6d781a3ff79b4770495f24f125ef3e65d5ef48bece5183ae993465`, not the supplied QA reference `ba6cc6756cd10cff4924df9c0ac9419e08dde395f798d0367c66b21c1f12bc63`. The recorded fixture uses `-march=znver5 -static` rather than the canonical dynamic x86-64-v3 build; full compile/link provenance and source hashes are retained. No substitution is claimed.

The negative's first bare d11 returns exactly 308972 nodes and both native processes exit0. The checker exits1 and aggregates `bench_post_summary_bytes` (134 exact bytes) plus `unexpected_option` (`NnueExactInt32`, check/default false). The stats tail's int32 refresh/update counters are both zero; the backend was never enabled. This is an output-contract negative fixture, not an engine candidate. The shelf patch is referenced rather than redelivered.

Run the standalone checker (Python standard library only):

```sh
python3 -B /path/to/forge_sol_S25_outcontract_20261025.py /path/to/forge --out /path/to/NEW_RESULTS_FOLDER
```

Keep `forge_sol_S25_options_20261025.json` next to the checker. To register the optional tests after applying the patch:

```sh
cmake -S /path/to/source -B /path/to/NEW_BUILD -DCMAKE_BUILD_TYPE=Release \
  "-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256" \
  -DFORGE_OUTPUT_CONTRACT=ON
cmake --build /path/to/NEW_BUILD --target forge -j2
ctest --test-dir /path/to/NEW_BUILD -R forge_sol_S25_ --output-on-failure -j1
```

## Evidence and continuation

Original command streams, complete native stdout/stderr, exit codes and metadata are preserved reversibly with base64 and SHA256; the native stream packets also record byte lengths and EOF completion. The raw bundle preserves original file bytes, including CMake registration/results, fixed allowlist authority, source/build binding, prior qualification receipts and all control logs. Supplied input trees and completed original evidence remain preserved. There were no failed implementation attempts in this bounded S25 run; the expected shelf RED and parser rejection controls are retained.

No active native jobs remain. Next action: root publishes this isolated S25 delivery and verifies public raw/Git bytes; only then start S27. Prior accepted source, network and experimental records remain the authority. No engine strength or performance conclusion follows from these contract tests.
