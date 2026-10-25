# Forge Sol Job A — 20261025

**DROP from adoption under the requested screen rule.** Both advisory medians were below+1% (d13 ratio0.975968153; d16 ratio0.929814411). The isolated research patch is correctness-qualified, with no speed/Elo claim and native box/Windows results UNVERIFIED. Job C/D have not started at this checkpoint. Base is supplied1ab50b2d+h256_e12 net MD5 6d22f612c855e17c62d396d32da99ea4 (C++ source matches f4911f2). Alternate base is the supplied buffer patch SHA2569ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c; search MD59553f697fa7bed500f945bc247d70dbf. Previous work remains preserved.

Patch `forge_sol_exactint32_h256e12_20261025.patch` SHA256 **`e661a145e301d3483ccaeaba65779d1d2002067263c836250e6418b9dccd151d`**. Feature patch source commit `13672013703abcd8c4eb057c6ea6a04a394fe8e6`. Exactly one build option `FORGE_NNUE_EXACT_INT32_AVX2` and UCI option `NnueExactInt32`, both OFF by default. Configuration is atomic, fixed before first go/bench. Incremental children inherit their parent's representation; worker reads remain race-free in the tested API lifecycle. ON widens stored weights to int32, never narrows accumulators, and converts q/4096 into the unchanged float output arithmetic. Search, eval values, network format, TT and move ordering unchanged; make/unmake allocations unchanged. No refresh cache was added: only8 full refreshes occur per bench.

```text
CMakeLists.txt         |    4 +
 IDEA_SOURCE.md         |    6 ++
 README.md              |    6 ++
 include/forge/nnue.hpp |   28 +++++++++
 src/nnue.cpp           |  148 +++++++++++++++++++++++++++++++++++++++++++++++-
 src/uci.cpp            |   45 ++++++++++++++-
 6 files changed, 232 insertions(+), 5 deletions(-)
```

| Check | Result | Evidence |
|---|---|---|
| Patch dry-run + apply on both supplied bases | PASS | No offsets/fuzz; search/eval/net remain unchanged |
| Build switch default OFF | PASS | Actual compiled-out build; ON request reports unavailable, no active counters |
| Runtime OFF/ON five-depth bench, both bases | PASS | 308972 /745494 /2460422 /11901452 /31111774 for every mode |
| Startpos perft5, both bases OFF/ON | PASS |4865609 |
| Kiwipete5, both bases OFF/ON | PASS |193690690; exact user FEN |
| NNUE FMA, all three build profiles | PASS |0 over complete decoded NNUE symbol bodies; static runtime/library code outside this scope |
| UCI output | PASS |Exact lock output plus only the new OFF-default option |
| Actual active-once proof / counters | PASS |Nonzero int32 refresh/update counters ON; zero OFF; no false active for perft/UseNNUEfalse |
| Incremental vs fresh | PASS |1,000,000 unique legal positions;0 lane-bit/output mismatches |
| Independent scalar int64 vs AVX2 int32 | PASS |Same1M positions,0 mismatches; compiler scalar oracle auto-vectorization disabled |
| Special transitions | PASS |426 castles,118 EP,6025 promotions,232 nulls; in-place checks included |
| Original Release / ASan+UBSan CTest | KNOWN FAILURES |Each13/14; exactly the four original FAIL lines below, no new sanitizer finding |
| Actual int32 ASan/UBSan parity | PASS |10,000 unique positions,0 mismatches |
| TSan private-board actual-core concurrency | PASS |4threads/8000 transitions; controller Board initialized before workers as in UCI |
| Concurrent first-ever Board construction | FAIL on unchanged lock |Preexisting attacks::init race reproduced separately; no fix in this NNUE patch |
| Windows / target-box adoption | UNVERIFIED |Owner independent qualification required |
| Elapsed refresh-time share | UNVERIFIED |Table below is construction-call share, not profiler time |

Full bounds and output arithmetic establish an exact integer grid, not an Elo result. First standalone TSan attempt omitted serial Board bootstrap, raced and crashed; original trace and untouched-lock reproduction retained. The lifecycle-correct retry is a separate test, not relabeling the failure. UCI already constructs the controller Board first. Fixing concurrent direct-API bootstrap is a separate future task. Review found/fixed a false activation acknowledgement; pre-fix and unfixed-base RED outputs are retained. An initial low-depth UCI smoke preceded its first hard d11 gate; that procedural deviation is saved. Final rebuilt delivery binary began qualification with OFFd11. One initial negative fixture failed on copied-EXE permissions; corrected behavioral RED remains separate. Input pack all219 SHA rows match; its prompt row has a stale byte count5755 versus6546, without a hash mismatch.

```text
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 661 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

## Refresh statistics

Same counts OFF/ON on each base. ON executes every update in int32. Values are fractions of refresh+update calls, not elapsed time; rounded ppm counters can be0 at deeper depths.

|Depth|OFF refresh/update|ON refresh/update|Refresh construction share|
|---|---:|---:|---:|
|11|8/238992|8/238992|0.003347280%|
|13|8/571275|8/571275|0.001400357%|
|16|8/1862090|8/1862090|0.000429623%|
|20|8/9547266|8/9547266|0.000083794%|
|22|8/23231031|8/23231031|0.000034437%|


## Per-network accumulator safety

All values are conservative supersets of attainable boards, in integer q units (real=q/4096), not empirical extrema. Full all768+4dirty bounds <2^24 and INT32_MAX prove exact float conversion and int32 headroom; runtime qualification rejects future unsupported nets. Observed million-corpus q range -78343..16160.

# Forge Job A independently recomputed accumulator bounds — 20261025
Each range is a conservative possible-prefix superset in integer q units (real=q/4096), not an observed or attainable range. All13 manifest hashes match. No speed or strength claim.
| Net | q min32 | q max32 | q min64 | q max64 | abs top32+4dirty | abs all768+4dirty | int32 / float exact-grid |
|---|---:|---:|---:|---:|---:|---:|---|
| lock_e12 | -219282 | 123238 | -379512 | 235351 | 259471 | 1662360 | PASS / PASS |
| e32_f003 | -326161 | 145444 | -509013 | 270955 | 377427 | 1978144 | PASS / PASS |
| e16_f004 | -220295 | 109619 | -383973 | 207779 | 259245 | 1523652 | PASS / PASS |
| e24_f005 | -217319 | 107759 | -331211 | 205526 | 256977 | 1438848 | PASS / PASS |
| e48_f006 | -279224 | 148321 | -506797 | 278156 | 323541 | 2218441 | PASS / PASS |
| e16_f007 | -224719 | 130291 | -351616 | 246650 | 265799 | 1526440 | PASS / PASS |
| e20_f008 | -208489 | 117191 | -355056 | 220166 | 246276 | 1591707 | PASS / PASS |
| e16_f009 | -208162 | 132569 | -341538 | 255103 | 251151 | 1557076 | PASS / PASS |
| e16_f010 | -211525 | 127195 | -318754 | 241531 | 247674 | 1477082 | PASS / PASS |
| e20_f011 | -276371 | 131597 | -516727 | 256340 | 315463 | 1569370 | PASS / PASS |
| e16_f012 | -205125 | 145004 | -345733 | 269875 | 242129 | 1539796 | PASS / PASS |
| e20_f013 | -194591 | 113024 | -331427 | 207626 | 229760 | 1516258 | PASS / PASS |
| e20_f014 | -200185 | 115181 | -303279 | 219089 | 236957 | 1530515 | PASS / PASS |

All full768+dirty4 bounds are below2^24=16777216 and int32_max=2147483647. A refresh-only AVX2 int32 path that converts q to float then divides by4096 exactly can feed the unchanged float output layer without loss. This does not justify output requantization. True int16 accumulators are excluded. Existing float accumulators need not be changed.


## Advisory-only Linux timing

One preregistered run, GCC14.2/strict FP/static/znver5 on shared Intel Xeon8573C; singleCPU0/nice19/T1/Hash16. A=untouched lock binary d90f5060; B=final feature build ON. All80 processes have fixed node counts and normal exits; no retries/outlier removal. The feature's extra layout/TLS/dispatch overhead relative to the untouched lock is included. These advisory ratios are **not a speed claim** or hardware adoption decision. Independent box and Windows ABBA remain required.

- d13: median ON/lock NPS ratio **0.975968153**; screen `DROP_BELOW_1PCT` (20 ratios from10 ABBA blocks).
- d16: median ON/lock NPS ratio **0.929814411**; screen `DROP_BELOW_1PCT` (20 ratios from10 ABBA blocks).

Feature-enabled H256 accumulator footprint grows2080 to4128 bytes, including runtimeOFF; buildOFF keeps original layout. No heap allocation was added to make/unmake. Even a positive advisory median does not accept this feature; a sub+1% screen is marked drop for that tested depth, without deleting evidence.

## Reproduce

Apply only the feature patch to either supplied source tree. Keep all original docs; the patch adds its idea sources to the existing README/IDEA_SOURCE. All implementation is original; ideas only from the user fixed-grid review and AVX2 semantics, no external engine source or tuned values.

```bash
cmake -S . -B ./forge_sol_a_build_20261025 -DCMAKE_BUILD_TYPE=Release -DFORGE_NNUE_EXACT_INT32_AVX2=ON -DCMAKE_EXE_LINKER_FLAGS=-static '-DCMAKE_CXX_FLAGS=-DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread'
cmake --build ./forge_sol_a_build_20261025 -j2
bash forge_sol_nnue_check_20261025.sh --engine ./forge_sol_a_build_20261025/forge --out ./forge_sol_a_checks_20261025
```

The dated Python checker must sit beside its Bash entry. Output directories must be new. It exits nonzero on any hard mismatch and rejects optimized Python that would disable assertions. For a build-defaultOFF profile, add `--compiled-out`; its requestedON run must explicitly remain unavailable, not masquerade as active. The actual-core parity/thread sources are separate dated tests; no tests or unrelated flags are embedded in the engine patch. No ZIP/LICENSE/AGENTS/.agents delivery is added. Native compiler commands, original transcripts, source/binary hashes, predeclared timing protocol and failed approaches live under `validation/forge_sol_jobACD_20261025/`.
