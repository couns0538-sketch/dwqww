# Result: arithmetic validated; isolated search ablation remains unaccepted

The one-line residual increment behaves as proposed in the **actual frozen Forge core**. All54 direct-method checks pass for both the unchanged EMA and the incremental copy in Release and ASan/UBSan; all four run stderr files are empty. The unchanged Release binary deliberately fails 17/54 incremental-expectation checks, demonstrating the behavioral difference. Those 17 expected failures are not claimed as existing correctness defects.

Frozen source is 47f0560221d986e41a309853e1295c557fcf5bf6. The two exported core manifests differ only in `src/search.cpp`; their before/after manifests are identical. The existing `SearcherTestProbe` friendship calls the real `Worker::corrected_eval` and `Worker::update_correction` with no engine-source instrumentation. Compiler is Debian GCC 14.2.0, pinned `/usr/bin/g++-14`; Release uses -O3 -DNDEBUG, ASan/UBSan uses RelWithDebInfo, all retain -ffp-contract=off and -march=x86-64-v3. Exact commands and compilation flags are preserved.

## Observed fixed-input results

Raw evaluation 100; fixed target 106; depth 15; 4096 updates. Negative-target mirrors pass as well.

| Path | Current EMA entries | Current corrected score | Incremental entries | Incremental corrected score |
| --- | --- | ---: | --- | ---: |
| Pawn only, material0 | pawn768 |103 |pawn1536 |106 |
| Default material100 |pawn512, material512 |104 |pawn768, material768 |106 |
| Target200, pawn only |pawn2033 |107 |pawn8192 |132 |
| Target200, material100 |pawn2033, material2033 |115 |pawn8192, material8192 |164 |

The first two controls confirm the idealized attenuation mechanism under finite integer arithmetic. The large-residual controls confirm a separate consequence of this same assignment change: the existing ±8192 clamp becomes reachable. The EMA starts inside and remains inside its ±2048 target envelope; at the tested depth its signed saturated entry is ±2033. Incremental updates permit ±32 cp per table, and ±64 cp total at default material 100. No clipping constant was changed.

Other passing checks cover depth cap, both residual signs, diff clipping at ±8 cp, preseeded endpoint clamps, zero-residual decay versus retention, signed integer truncation, material coefficient rounding, final mate-bound output clamps, side separation, and actual shared-material/different-pawn indices. Two equal default-table entries 128+128 produce 1 cp because the sum precedes grain division. Unequal entries 1024/-512 update to 1024/-416 with EMA versus 1088/-448 with increment, proving both tables consume one precomputed joint residual. EMA contracts their difference; increment retains it until a clamp intervenes.

After convergence on one pawn structure, a conflicting update on a second structure with the same actual material index changes the first structure's material correction while leaving its pawn entry intact. This is genuine shared material, not an accidental same-pawn hash collision. It is a reason to test noisy search interactions before accepting the ablation.

## Decision and limits

Recommend preparing only `candidate.patch` as an unaccepted independent search experiment, with the permanent actual-method behavior test described in `IMPLEMENTATION-RECOMMENDATION.md`. Preserve caller guards, keys, material weight 100, depth gain and both clips. Do not combine or retune another search mechanism. Full integrated regressions and any independently authorized fresh equal-clock strength gate belong to the parent task. Current attenuation may be useful regularization; no chess defect, search improvement, speed gain or Elo gain is established here.

No engine search, match, production edit, frozen17-package edit or Git/index mutation was performed by this agent. This task compiled both actual cores but exercised only correction methods and board setup. Build stderr preserves six pre-existing rule50 conversion warnings; there are no sanitizer diagnostics from the probes.

First preparation failed before compilation because CMake was absent from inherited PATH; `ATTEMPT1.md` and original command records preserve that failure. Attempt2 used the installed absolute CMake path and completed 20:47:08–20:52:20 UTC, inside the declared 600-second monitored cap. The executed runner has no internal subprocess timeout; its exact bytes/hash and that limitation are recorded in `execution-guard-note.json`. No later edit is presented as a retroactive runtime guard.

## Evidence

- `PROTOCOL.md`: prebuild scope, controls and finite stopping rule.
- `PROVENANCE.json`, `frozen-core-source.tar`, `source-before.json`, `source-after.json`: exact exported core and network identity.
- `candidate.patch`: the entire proposed engine change; SHA256 8a20510cd10646118f020018cf4b72cba51e3e37aee20fd1b10fed47c14ad9df.
- `probe.cpp`, `probe-CMakeLists.txt`, `run_probe-executed-attempt2.py`, `commands.json`, compilation-command JSONs: actual-core test and exact invocation.
- Four `*-own-contract.stdout` and stderr files; expected-RED stdout/stderr; saved probe binaries and `binary-sha256.json`.
- `history-*.stdout`: targeted exact-source history, including the pre-existing EMA and later material table.
- `RESULTS.json`: machine-readable checks and all observed selected states.
