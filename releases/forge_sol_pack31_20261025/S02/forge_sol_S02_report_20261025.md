# S02 unknown setoption warning — 20261025

**DONE, UNPROVEN beyond the recorded diagnostic and correctness checks.** One standalone feature patch; no playing-strength, Elo or performance claim. Apply to either supplied L or B directly, without S01 or the earlier relabel prerequisite.

Patch: `forge_sol_S02_unknownopt_20261025.patch`  
SHA256: `01befa9d147b5341057c85fc9f2321ad0d41c1a9cfd2d551ce38391ff0e84b9e`  
Diffstat:4files,57insertions,0deletions (CMakeLists.txt8,IDEA_SOURCE.md4,src/uci.cpp6,new regression39).

`FORGE_WARN_UNKNOWN_OPTIONS` is an independent CMake switch, defaultOFF. The final unrecognized-name branch is completely preprocessor-guarded. ON prints `info string unknown option <parsed name>`. No new UCI option is advertised. Existing known-option handling, invalid-known diagnostics and hidden tuning parameter recognition are preserved. No core source, header, evaluation value, search, network, TT or move-ordering change. The option also registers exactly one Python regression target when ON; Python3.10+ is then required by CMake. There is no added test target or diagnostic code when OFF.

## Pass checks

|Check|Result|
|---|---|
|New regression against original L and B, before implementation|RED:actualexit1 on both; only missing full unknown-name warning fails; all other controls pass|
|Final patch dry-run and actual apply on L/B|PASS,zerooffset/fuzz; fresh applied source matches native-tested source|
|DefaultOFF Release engine on each base|PASS,byte-identical to that base's original engine SHA256|
|All five OFF fixed signatures and both perfts/FMA|PASS,original frozen results reused only through exact executable SHA256; each new executable also first runs bare bench11=308972|
|ON d11/13/16/20/22 on L and B|PASS:308972/745494/2460422/11901452/31111774; fresh process per depth|
|ON startpos/kiwipete5 on L/B|PASS:4865609/193690690|
|ON FMA v2 checker on L/B|PASS,FMA0 in the unchanged NNUE evaluation body; no outlining or NNUE modification in this patch|
|ON diagnostic regression on L/B Release+ASan|PASS,one full multiword unknown warning; known/hidden options unchanged; expected invalid-known diagnostics preserved|
|UCI handshake bytes vs original, OFF and ON|PASS,no new advertised option and no banner/output changes|
|Actual CMake registration OFF/ON|PASS,L14/15targets;B15/16targets; only ON adds forge_unknown_option_regression|
|Full original suite on L/B OFF+ON, plus ASan/UBSan ON|PASS known-failure policy in all six profiles; exactly4 original FAIL lines and only forge_tests failing; no sanitizer report|
|Transport parser fixture|PASS,LF/CRLF parsed equivalently; raw bytes/newlines and SHA256 stay unchanged|
|Native Windows/PC work|UNVERIFIED,not run; transport fixture is not a native Windows qualification|

The four retained lines are the original WAC001 move/661-score checks and both unrestricted rook-underpromotion checks. No expected value or failure count was relabelled. The new target passes; this job deliberately does not inherit S01's test-only known labels.

|Base/profile|Engine SHA256|CTest result|
|---|---|---|
|L release_off|`e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`|13/14; only forge_tests fails with exact four known lines|
|L release_on|`e99321524b39f1bffb740c67904fe96805aacbb8299dcdbeb1ffeef187582cee`|14/15; only forge_tests fails with exact four known lines|
|L asan_on|`10d908b2dd1eb7574e6d63b249cea3a7b5a7316e7c9597f3f34a1b15193f77d9`|14/15; only forge_tests fails with exact four known lines|
|B release_off|`55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406`|14/15; only forge_tests fails with exact four known lines|
|B release_on|`3472c86cc4ec970e25da0fce0ed586ee618adec0559b0c95c89b0a8baaa68b6f`|15/16; only forge_tests fails with exact four known lines|
|B asan_on|`2ddb30ec4d43ed9313a5d8dc5c98e51dcb84aa302fa19572dc566714e7aeab2b`|15/16; only forge_tests fails with exact four known lines|


## Commands and provenance

Native execution used GCC14.2,C++20 (`gnu++20` CMake mode), H256, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off`. Release usesO3/DNDEBUG; ASan/UBSan usesO1/g1/DNDEBUG with both sanitizer flags. The exact compiler/link/configure/bench/perft/FMA/CTest commands and raw stdout/stderr are in dated JSON records and `forge_sol_S02_native_matrix_20261025.py`.

Only changed uci.cpp was compiled for each profile and linked against the appropriate unchanged, already validated core archive. The original suite binaries were reused. Full generated CTest harnesses substitute the fresh frontend, the saved original four-failure forge_tests executable, and own output-log destinations; every other original test command stays intact. This avoids rebuilding unchanged engine code and preserves S01's closed results. Core archive hashes and all substitutions are recorded. Default engine hashes exactly match the original base binaries, not merely their nodes.

All original protocol streams are stored losslessly with their SHA256: individual streams use base64, and an original JSON containing legacy banner text is wrapped whole as hex bytes. No old content is stripped or fabricated. `forge_sol_S02_evidence_map_20261025.json` maps flattened delivery records to their native original paths. The matrix helper records this machine's paths as execution evidence, not as a portable PC runner.

Portable reproduction after applying the patch to a work copy:

```bash
cmake -S work -B forge_sol_S02_build_20261025 -DCMAKE_BUILD_TYPE=Release -DFORGE_WARN_UNKNOWN_OPTIONS=ON '-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256'
cmake --build forge_sol_S02_build_20261025 -j2
printf 'bench 11\nquit\n' | forge_sol_S02_build_20261025/forge
python3 -B forge_sol_S02_unknownopt_test_20261025.py --engine forge_sol_S02_build_20261025/forge --expect-warning on
ctest --test-dir forge_sol_S02_build_20261025 --output-on-failure
```

Use `--expect-warning off` for the default build; optional `--reference-engine` compares the actual raw UCI handshake. CTest expects only the original four known check lines, not a wholly green suite. The test changes no host limits, affinity, caller priority or input files and starts no training or match. The engine command is finite and exits normally.

## Preserved failed approaches and review fixes

The initial CMake EOF hunk applied with an offset on B because B adds a target; all such attempt bytes are retained. Registration moved into the common early CMake block, and actual CMake target discovery confirms it works. Initial test parsing assumedLF; review identified native CRLF handling. The final parser normalizes only its parsed view, preserving actual raw protocol bytes. Final RED was rerun on both original bases and GREEN on all feature profiles. These bounded fixes did not change engine search behavior.

Idea source: the user's S02 request for visible unrecognized UCI configuration names. Original implementation and tests only, with the provenance entry added to the existing IDEA_SOURCE. No previous feature patch is resubmitted. No new source archive, engine binary, extra inference path or unrelated flag is delivered. All owned S02 native jobs have closed.
