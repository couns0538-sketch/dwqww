# S05 — scoped FMA checker and optional CTest wiring, 2026-10-25

**Validation infrastructure delivered; strength/speed UNPROVEN.** The accepted engine remains code base `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus supplied h256_e12 network overlay `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`; the accepted buffix base is preserved. No normal `src/` or `include/` byte, network, search, evaluation arithmetic, runtime option or counter changed.

The new checker scans instruction mnemonics in all demangled `forge::nnue::` bodies, including anonymous helpers and compiler clones. It accepts the recognized 256-bit output pattern in the public evaluator or outlined `evaluate_values`. Register names and unrelated-function FMA are not mistaken for NNUE instructions. Masked-clamp recognition checks zero provenance and source/mask liveness, including call barriers and ZMM/YMM alias clobbers.

One CMake switch, `FORGE_BUILD_NNUE_VALIDATION`, defaults **OFF**. ON registers five tests: float incremental/fresh parity, warm private-worker parity, actual UCI reset/replay, the scoped FMA checker, and its disassembly fixtures. It adds no definition to the engine/core. The final patch applies to both input trees with `patch -p1 -F0` (zero fuzz; B CMake has an observed four-line offset). Existing provenance notes, buffix notes and expected test values are preserved.

| Delivered patch/tool | SHA256 | Scope |
|---|---|---|
| `forge_sol_S05_ctestwire_20261025.patch` | `59294fd6e68ad0701d73038f618acd20ec72f9073faa8c1a19baec48618f2974` | CMake + IDEA_SOURCE + five new standalone test/tool files; one OFF-default validation-only switch |
| `forge_sol_S05_fmacheck_v3_20261025.py` | `4d6eaae160541b434853077e0d5f14c77a7d32a84a8c62eea7e768f364f6f95a` | One-positional-file CLI; unstripped NNUE object or engine |

| Check | Result | Evidence/scope |
|---|---|---|
| Final patch dry-run + application, L/B | PASS | Actual final `-p1 -F0`; fresh copies match the final active sources |
| Default and ON Release engine bytes | PASS | Both switches reproduce their accepted native engine SHA exactly |
| First invocation of every new normal engine | PASS | Bare OFF d11 = 308972; six fresh Release/sanitizer profiles |
| Five Release references / both perft5 | PASS by exact binary identity | S28 original closed qualification reused explicitly for the byte-identical Release engines; no fresh four-depth/perft repetition is claimed |
| Normal NNUE FMA checks | PASS | Final checker run on all four Release engines/objects; fresh sanitizer ON engines/objects also pass |
| CTest discovery OFF / ON | PASS | OFF L14/B15 targets; ON L19/B20, exactly five new targets |
| Complete Release CTest | PASS known-four policy | L OFF 13/14; L ON 18/19; B OFF 14/15; B ON 19/20. Only original forge_tests fails with its exact four lines |
| Final checker/script replay | PASS | After the last Python-only fix: actual final checker on all four Release exe/object pairs, plus complete ON CTest L/B |
| Fresh ASan+UBSan full ON suites | PASS known-four policy | L18/19 and B19/20; all new tests pass; no new sanitizer diagnostic |
| Float parity | PASS | Per ON run: 21,306 comparisons, 20,194 move transitions; zero lane, score or parent-state mismatches |
| Special/alias coverage | PASS | 20 castles, 11 en-passant, 182 promotions, 454 null cases; 20,648 parent checks and 20,648 alias checks per run |
| Warm private-worker test | PASS | Four workers, 8,000 transitions; zero lane/score/parent/alias mismatch or worker error; serial initialization is explicit |
| Real UCI reset/replay | PASS | Three completed depth4 searches, each after ucinewgame/isready; identically reset NNUE-enabled signatures match; HCE completes separately; empty stderr, zero exit, reader EOF |
| Final checker fixtures | PASS | 17/17; outlined clean output accepted; scoped FMA and malformed recognized clamp paths rejected |
| Actual native planted helper FMA | PASS negative test | Exactly one FMA in an actually called, unused zero-vector NNUE helper. Original v2 falsely passes real exe AND object; final v3 rejects both by symbol/instruction |
| Fault-fixture search/perft controls | PASS | First bare d11, all five fixed depths and both perft5 totals remain exact; this demonstrates a checker blind spot independently of node drift |
| Original input / core / expected-value identity | PASS | Both input trees unchanged; normal src/include bytes unchanged; original tests/tests.cpp unchanged; final IDEA text removes back to original byte-for-byte |
| Historical Job A integer-backend-specific checks | UNVERIFIED / BLOCKED | Current float lock lacks exact_int32 APIs, accumulator fields and NnueExactInt32 controls; backend/stubs were not revived |
| Old packer integration with v3 | UNVERIFIED | Supplied packer still explicitly pins v2 path/hash/metadata; it was not silently relabeled or changed |
| Windows, unsupported lowerings, speed, Elo | UNVERIFIED | Linux native work only; no PC run, NPS comparison, match, strength gain or lock switch |

The locked reference sequence remains **308972 / 745494 / 2460422 / 11901452 / 31111774** at d11/13/16/20/22. Perft5 remains **4865609 / 193690690**. Both normal Release modes retain exact accepted hashes:

| Base | Release OFF and ON engine SHA256 | Fresh ON ASan/UBSan engine SHA256 |
|---|---|---|
| L | `e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b` | `61da67f15ebce9edb186d5cf76dac7096a486584d2382e54e7c6eabadcd4e23e` |
| B | `55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406` | `1564bd068a03c0293983b666a8fdfb2d56e8d2c2406485e36114bf0af7a9a8e6` |

The four original failure lines are retained verbatim: WAC move `g3g6` versus `f6h5`, WAC score `661 below 31997`, and two identical unrestricted-underpromotion expectation failures. This is not a claim that all original assertions pass.

The earlier standalone Job A tests require shelved integer-backend APIs and cannot run unchanged on the float lock. New files are expressly **float adaptations** of useful update/parity, private-worker and protocol test ideas. They do not claim integer/scalar-backend parity, atomic backend-toggle testing, integer activation counters or S04 cold-construction coverage. S04 was completed/published before this work at `a9aa56cfd52c208316c1dafc6468e85f3b5e3bc3` and is not stacked in these input copies.

The checker recognizes a bounded instruction pattern, not arbitrary binary semantics or every possible ISA lowering. It requires unstripped symbols and 256-bit min/multiply/add plus vmax or a recognized compare/masked route. Unknown lowerings can fail closed. Bench/perft, runtime parity and sanitizers remain independent gates; disassembly alone does not prove NNUE semantic equivalence.

Implementation used supplied Forge checker/test ideas and current actual APIs only. The packer’s original one-positional checker interface remains compatible. Adopting v3 into that separate packer requires an explicit new path, full v3 hash and version-metadata update; this delivery makes no claim that its old v2 hard pin invokes v3.

Failures are preserved: the supplied v2 helper-FMA false-PASS; an initial B IDEA EOF-context failure; three masked-clamp false positives; and two call/ZMM provenance false positives. Each repair has actual RED/GREEN receipts. Before the final checker-only fix, all four Release profiles were already closed with unchanged C++/CMake; exact earlier script/patch bytes are retained. The final Python files were proved equal to fresh final patch copies and actually rerun through checker/ON CTest; two sanitizer ON builds then used only final sources. No source version is silently substituted.

The intentional fault source and its generator remain private; only source identity, commands, original streams and full disassembly are delivered. It is not an engine candidate. All actual raw receipts/test logs are losslessly indexed and sealed. No source ZIP, engine executable, network replacement, unrelated flag or earlier candidate patch is resubmitted.

Run from a fresh copy (GCC14.2/C++20 and CMake3.31.6 were used here):

```bash
patch -p1 -F0 < /path/to/forge_sol_S05_ctestwire_20261025.patch
cmake -S . -B /path/to/NEW-build -DCMAKE_BUILD_TYPE=Release \
  -DFORGE_BUILD_NNUE_VALIDATION=ON \
  -DCMAKE_CXX_FLAGS="-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256"
cmake --build /path/to/NEW-build --parallel 2
printf 'bench 11\nquit\n' | /path/to/NEW-build/forge
ctest --test-dir /path/to/NEW-build -N
ctest --test-dir /path/to/NEW-build --output-on-failure
python3 -B /path/to/forge_sol_S05_fmacheck_v3_20261025.py /path/to/NEW-build/forge
```

The first engine invocation must be the bare d11 gate shown. Full-suite exit8 is expected only with the original forge_tests known-four failure; any additional failure requires investigation. Exact original commands, flags, input hashes and outputs are in the evidence index. Next action is verified publication of bounded S05, then S25/S27 according to the active job order.

Final patch diffstat: 7 files, +538 −0. CMakeLists.txt +20 −0; IDEA_SOURCE.md +6 −0; tests/forge_sol_S05_float_parity_20261025.cpp +171 −0; tests/forge_sol_S05_float_threads_20261025.cpp +114 −0; tools/forge_sol_S05_float_uci_20261025.py +71 −0; tools/forge_sol_S05_fmacheck_v3_20261025.py +89 −0; tools/forge_sol_S05_fmacheck_tests_20261025.py +67 −0.
