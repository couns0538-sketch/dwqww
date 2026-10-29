# Forge Astra round 2 — development report, 2026-10-29

**B1–B5 have native Release qualification and published evidence. B6 passed its native preset matrix; B5 sanitizer qualification and B6 final checkpoint validation are pending in this checkpoint.** No Elo gain, speed gain, merge or adoption is claimed. Full CTest was run: the reports below retain its actual failures and exit status rather than calling an exception-qualified run fully passing.

Every job branch starts independently from `origin/forge-bundle-int`, exact base **`b7c177222038e9332965a95ec53ea3b94e90dbc9`**. The branches are **not cumulative**. `astra2-report` contains this handoff, not an integrated engine. Existing workspace changes and prior experiments were preserved; no main update, force-push or branch/file deletion is part of this round.

IDEA_SOURCE: the user's round-two specifications and this repository's original Forge implementations and documented formats. SmpV2 and SingularV2 use same-repository Forge Fable sources; no code or tuned constants from another engine were imported.

## Commits and decisions

| Job | Independent branch | Implementation commit | Published evidence commit | Current decision |
|---|---|---|---|---|
| B1 | `astra2-smpv2-mate` | [`931bd49552a7233bde84b8a207c7a503f8bf862c`](https://github.com/couns0538-sketch/dwqww/commit/931bd49552a7233bde84b8a207c7a503f8bf862c) | [`23e940b659848f0b1611582cdd70e11b362c80f8`](https://github.com/couns0538-sketch/dwqww/commit/23e940b659848f0b1611582cdd70e11b362c80f8) | Reviewed correction; ready for independent review and separate SMP strength qualification |
| B2 | `astra2-tm-softhard` | [`97da33b7e74fe280cb3ddbe2108efee1d40f9fb1`](https://github.com/couns0538-sketch/dwqww/commit/97da33b7e74fe280cb3ddbe2108efee1d40f9fb1) | [`45314a5e105cef5d306ff41abca2706e4ada78bb`](https://github.com/couns0538-sketch/dwqww/commit/45314a5e105cef5d306ff41abca2706e4ada78bb) | Budget invariant verified; complete suite retains an additional independently reproduced baseline SMP mate failure |
| B3 | `astra2-nnue-loader` | [`951a57787edf529cb9fb4f76125fa3b22d5c86b0`](https://github.com/couns0538-sketch/dwqww/commit/951a57787edf529cb9fb4f76125fa3b22d5c86b0) | [`9a09e7658f343acf231e3d20fe32db491eb7d94b`](https://github.com/couns0538-sketch/dwqww/commit/9a09e7658f343acf231e3d20fe32db491eb7d94b) | Test coverage ready; v2 protection already existed, so no engine repair |
| B4 | `astra2-uci-strict` | [`2beaad887ffdc20315a5be9322b53234ed90cece`](https://github.com/couns0538-sketch/dwqww/commit/2beaad887ffdc20315a5be9322b53234ed90cece) | [`d35d41fbe217bc00cedf642dd22aafcd895b53f2`](https://github.com/couns0538-sketch/dwqww/commit/d35d41fbe217bc00cedf642dd22aafcd895b53f2) | Native protocol tests pass; actual fastchess `-strict` invocation UNVERIFIED |
| B5 | `astra2-singularv2` | [`fde944ae38e6bbfef0b38f2c4a207e08285fcc1d`](https://github.com/couns0538-sketch/dwqww/commit/fde944ae38e6bbfef0b38f2c4a207e08285fcc1d) | [`bdd8854f42d423861e26ba40134dbb1a10ff00b4`](https://github.com/couns0538-sketch/dwqww/commit/bdd8854f42d423861e26ba40134dbb1a10ff00b4) (qualification checkpoint) | Release qualification complete; full sanitizer qualification pending |
| B6 | `astra2-bench-tool` | `01d57eb0a6049fda690bd3093e88df64ec2a64bc`; atomic-save revision `9db64dfa0299b97b74453f2d2ddf9ffb5b7e5631` | `9db64dfa0299b97b74453f2d2ddf9ffb5b7e5631` | Nine fake tests and 15 native OFF/B1/B2 cells PASS; final atomic-writer OFF matrix pending |
| B7 | `astra2-report` | This report's commit | This report's commit | Recoverable cross-branch handoff; root will finalize B5/B6 before publication |

## Native checks and exact OFF identity

Common recipe: GCC **14.2**, C++20, CMake **Release**, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`. Bench uses a fresh process per depth/configuration, **Threads=1, Hash=16, OwnBook=false**.

| Depth | Required OFF nodes | B1 final OFF / ON | B2 OFF / ON | B3 OFF | B4 OFF |
|---:|---:|---:|---:|---:|---:|
| 11 | 312866 | 312866 / 312866 | 312866 / 312866 | 312866 | 312866 |
| 13 | 862329 | 862329 / 862329 | 862329 / 862329 | 862329 | 862329 |
| 16 | 3024920 | 3024920 / 3024920 | 3024920 / 3024920 | 3024920 | 3024920 |
| 20 | 12389307 | 12389307 / 12389307 | 12389307 / 12389307 | 12389307 | 12389307 |
| 22 | 34048354 | 34048354 / 34048354 | 34048354 / 34048354 | 34048354 | 34048354 |

B1 ON here means SmpV2 ON at Threads=1; it does not measure SMP strength. B2 fixed-depth benchmarks do not exercise clock allocation. B3 has no engine option/change; B4 changes protocol metadata/diagnostics, not search values.

| Job | Build / focused checks | Complete CTest result | Startpos perft5 | NNUE FMA count |
|---|---|---|---:|---:|
| Baseline | Release PASS | 54/55; `forge_tests` only | 4865609 | 0 |
| B1 reviewed | Release PASS; 99/99 native checks; UCI lifecycle PASS | **56/57, exit 8**; `forge_tests` only | 4865609 | 0 |
| B2 | Release PASS; 32433/32433 native checks; clock/ponder UCI PASS | **55/57, exit 8**; `forge_tests` and `forge_tt_mate_tb_tests` | 4865609 | 0 |
| B3 | Release PASS; 41/41 focused loader checks | **55/56, exit 8**; `forge_tests` only | 4865609 | 0 |
| B4 | Release PASS; protocol 150/150 Release and 155/155 debug-hook checks | **56/57, exit 8**; `forge_tests` only | 4865609 | 0 |
| B5 | Release PASS; 96/96 native checks; N1/manual UCI regression PASS | **56/57, exit 8**; `forge_tests` only | 4865609 | 0 |
| B6 | Nine fake methods PASS, including injected checkpoint failure; 15 native cells PASS | New CTest registration 1/1 PASS; no engine change | Baseline reused | Baseline reused |

All original bench numbers, milliseconds and observed NPS—including superseded runs—are preserved in immutable tables and their adjacent raw process streams:

- [B1: all 25 qualification bench records](https://github.com/couns0538-sketch/dwqww/blob/23e940b659848f0b1611582cdd70e11b362c80f8/astra2_evidence/B1/BENCH_RESULTS.md).
- [B2: all 10 OFF/ON qualification bench records](https://github.com/couns0538-sketch/dwqww/blob/45314a5e105cef5d306ff41abca2706e4ada78bb/astra2_evidence/B2/BENCH_RESULTS.md).
- [B3: all 5 qualification bench records](https://github.com/couns0538-sketch/dwqww/blob/9a09e7658f343acf231e3d20fe32db491eb7d94b/astra2_evidence/B3/BENCH_RESULTS.md).
- [B4: all 5 qualification bench records](https://github.com/couns0538-sketch/dwqww/blob/d35d41fbe217bc00cedf642dd22aafcd895b53f2/astra2_evidence/B4/BENCH_RESULTS.md).
- B5/B6 observed records: PENDING final links. Any native/UCI/tool bench records must be linked in the final update too.

These timings are observations, not controlled ABBA speed comparisons. No NPS percentage gain is asserted.

## B1 — actual SmpV2 selector and review corrections

The bundle did not contain SmpV2. The port uses the actual Forge FB2-J5 source at `bf6839e9e65108db76f028532dc15f9587a41fe7`, not the bundle's older SmpBestThread selector. UCI `SmpV2` defaults **false**; options are snapshotted before workers start.

The historical selector failed **21 of 66** regression checks. The final selector requires a helper replacing a protected main/current mate or TB result to be strictly deeper in capped depth and carry an equal-or-better valid proven score. Both winning and losing TB score bands are protected while TB encoding is active; sentinels are rejected. A helper at N+1 cannot displace a main result that completed requested depth N just because of helper skew. SmpV2 selection takes precedence over SmpBestThread so the original main result reaches the guard.

User review changed the initial attempt: the **main worker retains its normal partial-iteration PV policy**, including ON at Threads=1. Only helpers retain their completed tuple on abort. The brittle fixed-depth/move/score assertion was removed; five fresh node-cap ON/OFF comparisons now test main behavior without hardcoded chess choices. Review RED was **87 checks / 4 failures**; final native GREEN is **99/99**. Prior attempts and their results remain explicitly labeled as pre-review evidence.

Actual Syzygy-file validation remains UNVERIFIED. SearchInfo has no independent proof-provenance tag; the guard uses Forge's existing reserved score conventions. [Exact source, logs, hashes and qualification](https://github.com/couns0538-sketch/dwqww/tree/23e940b659848f0b1611582cdd70e11b362c80f8/astra2_evidence/B1).

## B2 — soft limit never exceeds hard limit when enabled

`TmSoftHardClamp`, default **false**, fixes the bundle's allocator and its scaled iteration deadline. It does not import the separate J4 TimeManV2 experiment. The real trigger was time=100, increment=10000, overhead=10: original soft/hard **90/54 ms**, or **90/72 ms** with movestogo=1. ON clamps nominal and scaled soft time at hard time; OFF preserves the existing formulas. Tests cover large increments, tiny times, movestogo=1, ponder and integer-domain boundaries.

Unchanged allocator RED: **32424 checks / 8152 failures**, reproduced against pinned original headers. Corrected full native test: **32433/32433**. The focused inline arithmetic additionally passed **32424 checks under UBSan/float-cast-overflow**; this is **not a complete engine sanitizer run**.

The full CTest result is still **55/57**, not a pass. Its extra two-thread mate test returned a centipawn score instead of finding the mate. A candidate rerun passed; all 20 alternating baseline/candidate pairs (40 runs) passed; an adaptive untouched-baseline replay then reproduced the same failure class on run 12. This establishes baseline existence, **not** root cause or comparative failure rate. The original failing run was retained, and no expected value was weakened. [Original failure, every replay, commands and qualification](https://github.com/couns0538-sketch/dwqww/tree/45314a5e105cef5d306ff41abca2706e4ada78bb/astra2_evidence/B2).

The invariant does not eliminate scheduler delays or clock-polling latency; it is not proof against all time forfeits.

## B3 — existing v2 loader protection verified

Per the user's clarification, this job stays on the bundle's **FORGENN2 v2** loader. That loader already checks file size/header before reading weights. The engine source is unchanged, and the Release engine binary is byte-identical to the baseline. V3 work is deferred.

A dedicated regression covers empty/truncated files, extra payload bytes, invalid magic/version/width and a sparse oversized file. It checks exact read counters of 0 or 160 bytes, descriptive failure and removal of previously loaded/active state. The positive control loads its complete valid payload. Result: **41/41** against the untouched baseline core. There is no manufactured before-fix failure or invented loader repair. [Original logs, deterministic fixture hashes and source identities](https://github.com/couns0538-sketch/dwqww/tree/9a09e7658f343acf231e3d20fe32db491eb7d94b/astra2_evidence/B3).

## B4 — complete option metadata and precise diagnostics

All **64 registered tunables** are advertised with the registry's existing types, ranges and defaults. Unknown names emit `info string unknown option <name>`. After an active preset, an accepted actual value change emits `info string override <name> after preset`; invalid/refused/no-op assignments and buttons do not make false override claims. Preset OFF clears tracking. Debug-only options are advertised only in their matching build.

These are unconditional protocol requirements; hiding them behind a default-OFF feature would defeat strict option discovery. Search/evaluation/tuning values are unchanged. Native regression went from **150 checks / 90 failures** on base to **150/150 Release** and **155/155 debug-hook checks**. Two existing protocol expectations were explicitly updated for the newly requested unknown-option messages, with their prior intent retained.

No native fastchess runner was available. An actual fastchess `-strict` run remains **UNVERIFIED**, although the native protocol tests verify discovery and accepted settings directly. [Source, original RED/GREEN transcripts and qualification](https://github.com/couns0538-sketch/dwqww/tree/d35d41fbe217bc00cedf642dd22aafcd895b53f2/astra2_evidence/B4).

## B5 / B6 finalization slots

B5 source: `SingularV2` spin **default 0**, range 0..1, ported from this repository's Fable FB2-J3 `1efc0b2c9e09d38642eabd1d6282acceeb38c0b8`. The located implementation is Fable's; no unsupported Opus attribution is made. `BundlePreset N1` means **CorrHistPlus=4 + SingularV2=1**, with the other owned bundle options reset. CorrHistPlus is compatible; CorrExt is separately excluded because its extension budget counts extra plies while J3 counts double/triple extension events. [Frozen changed-line inventory and CorrHistPlus interactions](https://github.com/couns0538-sketch/dwqww/blob/bdd8854f42d423861e26ba40134dbb1a10ff00b4/PORT_NOTES.md).

Verified B5 Release bench results, binary SHA-256 `7f5653bd308fb528851a9009c122aa40028a2ce6d00e5d19a339e46474746cdb`:

| Depth | OFF | SingularV2=1 | BundlePreset N1 |
|---:|---:|---:|---:|
| 11 | 312866 | 404121 | 277579 |
| 13 | 862329 | 1005954 | 814055 |
| 16 | 3024920 | 4120585 | 2651984 |
| 20 | 12389307 | 11497954 | 18648191 |
| 22 | 34048354 | 34264955 | 40304213 |

B5 perft5 is **4865609**, FMA **0**. Full Release CTest completed: 56/57 passed with only the four known tactical diagnostics; 96/96 new native checks and UCI regression passed. A separate full ASan/UBSan build/run has been started with `-O1 -g1`, `-fno-pie/-no-pie` and `FORGE_ENABLE_SANITIZERS=ON`; its result is **PENDING**, not a sanitizer pass. [Verified qualification checkpoint and raw evidence](https://github.com/couns0538-sketch/dwqww/tree/bdd8854f42d423861e26ba40134dbb1a10ff00b4/astra2_evidence/B5).

**PENDING root update:** B5 final evidence SHA; complete native and sanitizer outcomes; all bench-table links; final decision. Do not promote a running qualification into a completed result.

B6's first full native matrix used runner `01d57eb` (SHA256 `16496dd665db4961499ed8eff01025d5d5fa5a05aa0ab6e6c7b2c4ee6cfb3338`). It passed all 15 OFF/B1/B2 cells. The later revision only makes ledger writes atomic; it passed nine fake-engine test methods, including injected replacement failure preserving the prior valid ledger. Its separate final native OFF verification is pending. No engine source changed. Exact commands and schema are in [B6 tool documentation](https://github.com/couns0538-sketch/dwqww/blob/9db64dfa0299b97b74453f2d2ddf9ffb5b7e5631/docs/bench_matrix.md).

## Remaining failures, limits and integration work

The unchanged `forge_tests` diagnostics in these OFF suites are:

```
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 623 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

B2 also preserves the intermittent `forge_tt_mate_tb_tests` failure discussed above. SmpExactNodes is an acknowledged pre-existing risk; a passing occurrence does not establish that its intermittent behavior is fixed. No expectation was silently changed to hide tactical or SMP failures.

Full round-two **ASan/UBSan, LeakSanitizer, TSan, Windows execution, actual tablebase files and equal-time fastchess strength gates are UNVERIFIED** in this draft; the B5 full ASan/UBSan qualification is specifically in progress. B2's focused inline UBSan result is the limited exception described above. Previous round-one sanitizer results do not qualify changed round-two sources. No Elo estimate or Stockfish claim is justified by these tests.

The next integration must be a new isolated branch and must reconcile these exact overlaps before gating:

1. **FB2 Options and preset assignment:** B1 adds `smp_v2`; B2 adds its timing bit; B5 adds `singular_v2` and N1. Preserve B1/B2 independent values when applying B5's seven owned preset fields. A whole-struct preset assignment must not silently erase independent options.
2. **Effective search snapshot:** retain CorrHistPlus/CorrHistV2 exclusivity, add B5's CorrExt/SingularV2 exclusion, and propagate all three new bits before helper launch. No recursive search should read mutable pending settings.
3. **UCI setters and presets:** use B4's accepted-value change observer for B1/B2/B5 setters, retain N1 in the advertised combo, preserve atomic preset refusal and accurate override tracking, and keep default values OFF/0.
4. **Iterative search:** merge B1's helper diversification and helper-only abort tuple policy with B2's scaled soft/hard deadline. Preserve the main partial-PV behavior. Keep B5's extension event semantics isolated from CorrExt.
5. **Registration and qualification:** retain every new test target; rebuild the combined source, re-run all five OFF pins, perft, full CTest and full sanitizers, then qualify the intended ON combinations. Separate source integration from equal-time strength acceptance.

Before any strength gate, retain original binaries/net hashes, exact option lists, balanced openings and original runner logs/PGNs. Candidates remain isolated and unadopted until their applicable checks and independent gate are satisfied.
