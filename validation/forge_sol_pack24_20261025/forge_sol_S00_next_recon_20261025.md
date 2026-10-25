# S02–S07 source-grounded reconnaissance — 20261025

Read-only preparation only. No engine patch, build, benchmark, training, test-suite execution or Git mutation was performed. Paths below are relative to the pack's `files/` directory. This is not native acceptance evidence.

## Input blockers and source identities

- L is `01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src/`; B is `01b_base_h256_e12_buffix/forge_h256_e12_buffix_src/`.
- The requested alternate nets e20i, e12f and e16q are absent as actual payloads. All regular files and92 nested ZIP/tar members were MD5-scanned; none matched their documented identifiers. There are28 regular `.inc` files, including duplicates. The complete scan is `forge_sol_S00_net_presence_20261025.json`. Do not substitute another net and label it as one of these missing revisions.
- The actual WAC300 EPD is absent, despite task-path wording. All regular EPD files are two copies of the opening corpus; nested archives add only another opening-corpus copy. Tactical directories contain scripts, IDs and answer/result JSON, not the original positions. The external suite identity recorded in `12_strength/p23b_refutlmr_h256/artifacts/wac300/hashes.txt` is SHA256 `9bfb7b42cf5bbc7f3d60ff767ca3be460e0ae4d9110ef9a71ddf0bd7071d4d46`. Live WAC300 reproduction is UNVERIFIED until those bytes are supplied. Artifact parsing and generic/synthetic runner tests remain actionable.

## S02: unknown option warning

L `src/uci.cpp:190–285` already parses full option names and recognizes hidden tunables before the explicit known-option chain. Unknown names fall through silently. There is no equivalent warning currently implemented.

The smallest change is a final warning branch after the existing known-option chain, preserving `handled_tunable` behavior. A known but unadvertised tuning option is not unknown. The global default-output rule and S02's unchanged option-list requirement favor one OFF-default compile switch, with every warning statement and literal inside its preprocessor guard, rather than adding a UCI option. Default-off source must preprocess back to the old behavior. Tests should distinguish unknown multiword names, recognized names with invalid values, hidden tunables and normal known options. An enabled warning run and disabled byte/output-identity run are separate profiles.

## S03: fixed reference suite

No comprehensive fixed-reference runner exists. Existing `tests/tests.cpp:198–204` contains the six canonical perft FENs, at only selected depths3/4. `:508–516` contains mate fixtures and expected scores. `04_refs/FORGE_FIXED_REFERENCES_h256e12_20261025.md` provides the fixed five bench signatures and required depth5 start/kiwi totals.

An economical eight-position suite can use those six canonical perft positions plus two rank-reflected/color-exchanged versions, explicitly documenting the move-tree bijection and the published reference source. The mirrored counts are transferred by the mapping, not obtained from a baseline executable. Cite a published perft-results reference and preserve fixed d1–d5 numbers. A CMake validation-target option must default OFF and leave the default build/test list unchanged. A deliberately wrong fixed result or scratch perft implementation must make the runner exit nonzero; a fresh engine's first invocation remains bare bench11.

## S04: first Board initialization

L `src/bitboard.cpp:112–115` uses a plain static boolean and publishes true before filling shared tables. B has the same initialization body. The supplied `09_sol_returns/sol_return_jobA_20261025/forge_sol_exactint32_thread_test_20261025.cpp` is NOT a usable base reproducer: it calls the dropped experiment API and explicitly constructs a controller Board before starting workers. Do not add that experiment as a dependency.

Write an original Board-only barrier test: eight workers simultaneously construct their first Board and inspect deterministic move/perft/table results, without serial bootstrap. A function-local static initializer or call_once can protect the complete existing initialization. The default guard must surround new initialization behavior too. Preserve the old body when OFF. To test first-ever initialization1000 times, use1000 fresh processes; looping1000 times after one process already initialized the tables does not exercise1000 first-initialization races. The prior UCI controller-before-worker lifecycle does not prove concurrent first-ever direct API construction safe.

## S05: FMA checker and test wiring

`04_refs/check_nnue_simd_v2_fma_checker.py` is a useful interface/ISA reference but its final symbol regex scans only `forge::nnue::evaluate`. Outlining the output computation into `evaluate_values` both creates a false ISA failure and leaves that helper outside the FMA scan. Scan all complete defined NNUE symbol bodies for FMA, while locating output arithmetic specifically in the main output body or explicitly allowed output helper(s); do not satisfy output-clamp checks with unrelated update instructions. Preserve the existing AVX2 and masked-AVX512VL clamp distinctions.

The returned parity/thread/UCI tests depend on the dropped exact-int32 API. They cannot simply be compiled on L/B. Wiring them must reference their exact existing external source files and explicit prerequisite experiment/switch, or otherwise report that dependency unavailable. It must not revive the shelved implementation by silently resubmitting it. The new validation CMake switch defaults OFF; default targets and engine output remain unchanged. A planted NNUE FMA fixture should fail the new checker even when the public evaluate wrapper itself has no fused instruction.

## S06: statistics model

Exact published evidence is in `08_status/GATE_RESULTS_SUMMARY_20261025.md:6,8` and `08_status/QUEUE_PENDING.md:910,1005`.

|Gate|Pentanomial|W–D–L|Logistic Elo ± paired95% half-width|Normalized-Elo GLR [0,10]|
|---|---|---|---|---|
|G100r|[5,121,458,154,12]|220–1107–173|10.8898798 ±8.3814001|2.2190452071|
|G95|[13,128,463,137,9]|192–1117–191|0.2316238 ±8.5311018|−0.5613033194|

Existing `tools/match/windows_validate.py:195–237` implements logistic GLR, with a declared count regularizer, and gives different LLRs for these hypotheses. It cannot be reused unchanged to reproduce the published answers. For paired scores x=[0,.25,.5,.75,1], mean m and variance v, normalized Elo is `(800/ln(10))*(m-.5)/sqrt(2*v)`. Maximize multinomial likelihood separately under each normalized-Elo hypothesis and normalization. Independent constrained numerical calculations reproduce both required rounded LLRs with residuals below1e-16. Model selection must be explicit; never hardcode the reference LLRs.

`tools/match/pgn_stats.py` supplies bookkeeping ideas, not a complete statistical miner. Raw gate PGNs/logs are absent. Actual native model arguments, independent termination counts and per-opening/phase splits remain UNVERIFIED on the real gates; synthetic PGNs can test those code paths. The summary reports no G100r time losses/crashes, but that is reported evidence, not a new audit. G100 and G100r must not be pooled; capped positive estimates do not accept a gate.

## S07: depth/WAC sweep

Reusable ideas are in `12_strength/h256tools/runbench.sh`, `checks.sh` and `wac001.py`, but those scripts hardcode missing host directories and must not run unchanged. The native UCI driver should await bestmove/EOF explicitly and stop on malformed output, retain per-process source/binary/options identities, and compare OFF against the published constants, not its own output. Result parsing of existing artifacts is independent of unavailable live WAC bytes.

`12_strength/p23b_refutlmr_h256/artifacts/bench.log` records OFF `[308972,745494,2460422,11901452,31111774]` and primary RefutLmr1 ON `[311855,745052,2594099,10785772,22307140]`. `README.md:60–85` records MinR4 `[291046,717175,2438867,11617492,38241769]`, with d22 ratio38241769/31111774, about+22.9%, and the screen failure. The complete variant table is there; do not invent omitted raw runs. Existing chunk JSON includes SAN best moves/results/depth/timing, but no FENs, so it cannot reconstruct the missing suite. WAC timing/solve scores remain advisory, not playing-strength acceptance.
