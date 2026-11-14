# Narrow mate-alpha guard and round-4 soak

Updated 2026-11-14T21:20:57.323Z. Cloud VM only. Branch `for-fable-and-opus/astra-r4-mate-alpha-guard`. Task start 2026-11-14T19:48:28.579Z. Current phase: Successor soak: sanitizer self-play.

**Guard acceptance: complete.** Default pins: **312866 / 862329 / 4865609**. Engine delta is27 added lines,0 removed, behind an OFF-by-default compile gate and a false-default UCI option. No CMakeLists change.

## Source and behavior

Base `8e805fb482a97b7182f3fa4c12f26ce7e1d88c19`; four source-only audit fixes were reapplied separately, yielding audited baseline `12c791d5451b158fd6ed1b506b4869b15c8a5b4e`:

| Source commit | Reapplied commit | Files |
|---|---|---|
| `e349e3e859f2cc3d9b0eae08a5dd74e3b0e45705` | `5ad7ac6e4aa15bcfb35bf54a7d826521423bcf64` | forge-combo29/src/search.cpp |
| `bf4154454ddc7b226bc1734bfc84d75569cdfc07` | `bafb2d5bf3a542da5c51608bc9babf87f79cfa69` | forge-combo29/include/forge/search.hpp |
| `1ebc9b48084ac26db00a71b50fafccd2bfc8baa4` | `8c4fb7d14fa5519d13e32914a4d97866a8b51a56` | forge-combo29/src/eval_params.cpp |
| `efb3eaa37a84198cc8c0ac1c35d0dc5cf384376d` | `12c791d5451b158fd6ed1b506b4869b15c8a5b4e` | forge-combo29/src/board.cpp |

The guard changes only quiet and capture static-evaluation futility predicates when the current alpha is a mate score. LMP, history pruning, SEE filters, TT rules, quiescence and reported-score code remain unchanged. Changing MateAlphaGuard clears searcher/hash state.

Enable with `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`, then `setoption name MateAlphaGuard value true`. With the compile switch undefined or0, the option is absent. GCC14.2, x86-64-v4, AVX-512/BMI2, strict floating-point flags were used. Exact configure/build commands are in `tests_astra_mateguard/logs/`.

| Engine file | SHA256 |
|---|---|
| src/search.cpp | `91dca7e1484670e7f065d4e593e45b8c3a3fca6baf6afd73e2edc84edd7ef637` |
| src/uci.cpp | `3724b9b6da8ae0c63e7d59f75ed671875a42df3bbc2ac2a6c995f3e8de321fe1` |
| include/forge/search.hpp | `faa4fba15aa6c89932aa4dd86cbf594b536e20b90ff8e44159c1795424c5622b` |

The baseline/undefined/zero Release binaries are byte-identical on this VM: `06a2b1d582c05bb4a762ef76f64ec171a8a2ca031230b27fe3a5d2bc8ed8bace`. Compiled1 candidate: `710cfcf73fcc3b9897281113759ed18565feb167eb0effe7023cbbe1706037dc`. This is Linux build evidence, not a claim about an unrun owner-PC build.

## Acceptance checks

| Check | Observed result | Evidence |
|---|---|---|
| Default behavior | All3 compile modes:312866/862329/4865609; normalized default output identical | [Release checks](tests_astra_mateguard/release-validation/) |
| Existing16 options alone | All48 baseline/undefined/zero invocations match the source report | [Option table](tests_astra_mateguard/option-counts/summary.json.txt) |
| Hash toggle | Real warm/cold search restores cold behavior; true→false default-NNUE bench13=862329 | [Toggle output](tests_astra_mateguard/release-validation/toggle.stdout.txt) |
| Original fixture, NNUEfalse, depth13 | Off mate17/25568nodes; A mate11/36063nodes;10 fresh repeats identical except time/nps; exact root mate8 | [Repeats](tests_astra_mateguard/release-validation/summary.json.txt) |
| Live internal trigger | Same FEN/ancestry, mate alpha31982: predicate948<=31982 is true; d1c1 actual child search returns31987, first at depth4 | [Observational proof](tests_astra_mateguard/original-root-final/TRACE_REPORT.md) |
| Frozen40 KRK, depth14,T1/T2/T4 | 120 positive mate reports;0illegal/lost-win/shorter-root or chosen-move-distance violations | [KRK report](tests_astra_mateguard/krk-validation/REPORT.md) |
| Unchanged t23 suites, Aon | Release+ASAN/UBSAN:120 cases,0failures/reports | tests_astra_mateguard/logs/t23-* |
| ASAN/UBSAN Aon, depth10 | 200searches,200legalmoves,0faults/reports | [Output](tests_astra_mateguard/logs/asan-depth10-200.txt) |
| TSan Aon, depth9,T2/T4 | 8games/1499searches,0reported races or chess faults | tests_astra_mateguard/logs/acceptance-tsan-* |
| Paired on/off games | 2000/2000 accepted; W-L-D 567-572-861 | [Match evidence](tests_astra_mateguard/matches/) |

Fable accepted the live semantic trace and selected A in [reply0006](https://github.com/couns0538-sketch/dwqww/blob/a085a3418ea4e632da971bb6253babb1540eaf5a/forge-combo29/soak_all/FABLE_REPLY_0006.md). Earlier depth4 success removes the old same-ancestry depth5 re-searches; the different-ancestry TT-first depth5 visit is excluded from the proof. The trace does not mutate search state and full normalized stdout matches the uninstrumented binary.

The KRK oracle is the retained retrograde implementation sharing Forge move/attack primitives; it is not an external tablebase and does not model repetition or the fifty-move rule. These root checks do not establish universal TT-bound soundness or exact mate distances for every search. [Supplemental seeded tests](tests_astra_mateguard/supplemental/) deliberately use artificial TT/history contexts and are not substituted for the original-root trace.

Depth13 on40 frozen roots, NNUEtrue: off/A/B positive mates35/35/34, exact hits21/29/28, mean excess0.685714/0.257143/0.264706 UCI moves, summed nodes740045/897857/1088994. Means use positive mate reports only. NNUEfalse measurements and every raw row are retained in the KRK report. B remains a diagnostic comparison; A is the production delta.

## Games

Official fastchess, same compiled1 binary on both sides, MateAlphaGuard on/off, nodes20000 per move, Threads1,Hash16,OwnBookfalse,UHO random openings with fixed seeds and color-swapped pairs, recover,no adjudication. Raw tool version, binary/book hashes, full engine trace, events, PGN and real command output are preserved. Counts only; no strength or speed conclusion.

| Batch | Seed | Games | W | L | D | Identical pairs | Five pair bins |
|---|---:|---:|---:|---:|---:|---:|---|
| 0001 | 20261114201 | 400 | 114 | 116 | 170 | 126/200 | 0,2,198,0,0 |
| 0002 | 20261114202 | 400 | 119 | 121 | 160 | 114/200 | 0,2,198,0,0 |
| 0003 | 20261114203 | 400 | 112 | 112 | 176 | 124/200 | 0,1,198,1,0 |
| 0004 | 20261114204 | 400 | 111 | 111 | 178 | 127/200 | 0,1,198,1,0 |
| 0005 | 20261114205 | 400 | 111 | 112 | 177 | 128/200 | 0,1,199,0,0 |
| Total | — | 2000 | 567 | 572 | 861 | 619/1000 | 0,7,991,2,0 |

Pair bins are LL,LD,DD-or-WL,DW,WW from option-on’s perspective. Identical pairs have the same full UCI move/FEN/legal sequence and board-color result/termination. All accepted batches have zero recorded crashes, illegal moves, disconnects, stalls or aborted games.

Excluded attempt: the first400-game batch overlapped TSan, used concurrency2, and reached its420-second deadline after314 completed games and2 timeout-aborted games. Eight stop/quit warnings occurred during timeout shutdown;0crash/illegal/disconnect markers were recorded. The entire batch was repeated with the same seed at concurrency4. All314 previously completed games match that retry exactly; they are not additional games. Full failed-attempt evidence remains in `matches/incomplete-0001`.

## Successor soak

Budget: 2026-11-14T20:43:34.458Z to 2026-11-15T00:43:34.458Z (at most240minutes).

| Batch | Conditions | Games | Searches | Sanitizer reports | Result |
|---|---|---:|---:|---:|---|
| soak-asan-off-t1-n2000 | asan-off | 120 | 17546 | 0 | pass |
| soak-asan-off-t1-n20000 | asan-off | 12 | 1768 | 0 | pass |
| soak-asan-off-t2-n2000 | asan-off | 180 | 24615 | 0 | pass |
| soak-asan-off-t2-n20000 | asan-off | 16 | 2982 | 0 | pass |
| soak-tsan-off-t2-n0 | tsan-off | 7 | 742 | 0 | pass |
| soak-tsan-off-t4-n0 | tsan-off | 7 | 899 | 0 | pass |
| soak-asan-hindsight-and-guard-t1-n2000 | asan-hindsight-and-guard | 128 | 17588 | 0 | pass |
| soak-asan-hindsight-and-guard-t1-n20000 | asan-hindsight-and-guard | 12 | 1653 | 0 | pass |
| soak-asan-hindsight-and-guard-t2-n2000 | asan-hindsight-and-guard | 195 | 25850 | 0 | pass |
| soak-asan-hindsight-and-guard-t2-n20000 | asan-hindsight-and-guard | 24 | 3134 | 0 | pass |

Self-play games count normal terminal/capped games; fault-aborted games are separate in raw summaries and totals. Searches include searches in fault-aborted games when the harness finishes. A final SUMMARY with TSan exit66 is completed but failed, not discarded. Sanitizer counts are report-marker occurrences, including DEADLYSIGNAL; all raw diagnostics are retained and any distinct races require source-line grouping. These recorder corrections do not alter the engine or expected results.

Equality against e04556dd: not yet run on this tree. Existing test-folder suite: not yet run on this tree; the acceptance t23 subset above is separate.

Existing-suite compilation: {"enabled":{"commands":50,"passed":50,"executables":47,"helperObjects":3,"artifactBytes":36375672},"asan":{"commands":50,"passed":50,"executables":47,"helperObjects":3,"artifactBytes":797963480},"sourceFilesVerified":99,"sourceHashesUnchanged":true,"failures":0,"runtimeTestsRun":0}. Compilation counts do not establish runtime test results. [Plans and build manifest](tests_astra_mateguard/existing-suite-plans/BUILDS.md).

## Retained failures and limits

- Initial harness error: the real toggle session retained UseNNUEfalse and printed907205, but its bench check expected the NNUEtrue862329. Failed assertion/output are preserved. The corrected command explicitly sets UseNNUEtrue and passes862329; no expected value or engine code was changed.
- The old source’s four t16 options/clamp fixture comparisons remain documented on soak/combo29-all. New-tree suite results will report actual exits without stripping advertisements or modifying expected files.
- The previous eight-hour window was interrupted by a credit limit; it is not represented as eight continuous testing hours. Original source/evidence,92fault files,12000completed games and omitted LMR matches are preserved at [old soak checkpoint](https://github.com/couns0538-sketch/dwqww/tree/98035496dfef4f7658f2d8b477ccc65f9091508c/forge-combo29/soak_all).
- No owner-PC execution, no strength/speed conclusion, no universal race-freedom claim. New speed branches are outside this soak.

Exact commands, output, hashes and retained failures are under `tests_astra_mateguard`. Text larger than16MiB is split without loss; manifests give ordered chunks and whole-file hashes. VM tools are archived as inert `.mjs.txt`; no executables, archives or generated network files are committed. [Progress](tests_astra_mateguard/PROGRESS.txt) and [earlier report chronology](tests_astra_mateguard/report-chronology-before-render.md) are retained.

**Final engine delta commit: `a9fddb1f5c70c88943cddb1d92acf3d33d1aff0d`.**

Checkpoint 2026-11-14T21:20:57.323Z: Successor soak: sanitizer self-play. Audited baseline Release build completed, GCC14.2 x86-64-v4; Threads1 Hash16 OwnBookfalse pins312866 /862329 /4865609. Baseline binary SHA256 06a2b1d582c05bb4a762ef76f64ec171a8a2ca031230b27fe3a5d2bc8ed8bace. Exact commands and output are under tests_astra_mateguard/logs. Preparation encountered missing partial-clone metadata and a whitespace-trimmed patch serialization error; both tool failures and corrected commands are retained, with no engine workaround. Successor asan-hindsight-and-guard completed: {"seed":202611143010,"threads":2,"nodes":20000,"first_game":0,"max_games":1000000,"seconds":180,"Hash":16,"OwnBook":false,"UseNNUE":true,"MultiPV":1,"ContHist4PlyRead":false,"NonPawnCorrection":false,"LmrDeeperShallower":false,"MateAlphaGuard":true,"HindsightDepth":true,"depth":0,"games":24,"moves":3134,"searches":3134,"opening_moves":192,"faults":0,"illegal":0,"missing":0,"badscore":0,"mates":12,"stalemates":0,"repetitions":10,"fifty":2,"ply_caps":0,"insufficient":0}. Sanitizer reports 0. Accepted completed self-play totals {"games":701,"faultAbortedGames":0,"searches":96777,"faults":0,"sanitizerReports":0}. All raw inputs/outputs retained; incomplete attempts excluded from totals.

ENGINE_DELTA_COMMIT a9fddb1f5c70c88943cddb1d92acf3d33d1aff0d
