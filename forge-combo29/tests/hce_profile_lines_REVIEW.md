# HCE histogram-to-source follow-up

**No new engine benchmarks, production edits or speed claims.** This uses only the already recorded immutable-lock gprof binary, histogram bins and DWARF. The binary hash is checked before symbolication.

## What the existing samples distinguish

There are 143 distinct sampled HCE address bins across four runs; 24 addresses recur in two or more runs. `addr2line -i -f -C` preserves complete inline chains. Coarse source groups use the first specific helper's eval.cpp line in each chain, rather than assigning every inlined accumulator addition to the generic `add` helper.

| Coarse source region | NNUE off d16 | NNUE off d18 | NNUE on d16 | NNUE on d18 |
|---|---:|---:|---:|---:|
| Piece evaluation, eval.cpp:99–195 | 14 | 22 | 12 | 35 |
| King evaluation, :197–273 | 7 | 12 | 6 | 9 |
| Threat evaluation, :275–317 | 6 | 3 | 3 | 7 |
| Pawn-cache check/dispatch, :397–413 | 2 | 8 | 3 | 7 |
| PSQT/phase setup, :375–395 | 5 | 8 | 0 | 0 |
| Pawn-structure calculation, :56–97 | 0 | 2 | 2 | 3 |
| Attack/mobility setup, :418–439 | 0 | 4 | 1 | 3 |
| Passed-pawn evaluation, :319–345 | 0 | 0 | 0 | 1 |
| Final taper/score, :450–474 | 3 | 3 | 0 | 4 |
| **Total HCE ticks** | **37** | **62** | **27** | **69** |

These are **histogram tick counts**, not independently measured line runtimes. Piece evaluation is consistently the largest coarse bucket, with king evaluation next. The zero PSQT-setup bins in NNUE-on runs are consistent with runtime PSQT reuse in the residual path; a zero count does not prove zero cost.

Notable recurring bins:

- `0x18aa2`, pawn-cache validity/branch neighborhood at eval.cpp:397: present in all four runs, with 2/6/3/6 ticks respectively, **17 total**.
- `0x1b0c9`, black rook attack lookup in piece evaluation at eval.cpp:129: present in all four runs, 1/1/1/2 ticks.
- `0x1930a`, king-zone hit handling at eval.cpp:146: present in three runs, one tick each.
- `0x1a129`, nearest-pawn distance in king evaluation at eval.cpp:271: present in three runs, one tick each.

Each bucket combines related work to avoid false precision. The full address, inline-chain, discriminator and per-run mappings are in `hce_profile_lines_results.json`.

## A concrete exact-layout hypothesis

The pawn-cache check is more than a generic umbrella location: disassembly around its most recurrent bin contains the `cmpb` against `PawnEntry::valid` at offset `0x20`, followed by its branch. The histogram bin overlaps the check/branch neighborhood. It does **not** prove that the load missed cache or that the entire bin cost belongs to that instruction.

A standalone type-layout probe against the immutable header measured:

| Field/layout | Locked PawnEntry | Reordered probe type |
|---|---:|---:|
| sizeof | 40 bytes | 32 bytes |
| alignof | 8 | 8 |
| key offset | 0 | 0 |
| score offset | 8 | 8 |
| passed offset | 16 | 16 |
| valid offset | 32 | 12 |

The probe moves only `valid` before `passed`, filling existing padding. With the unchanged 32,768-entry cache, storage would fall from **1,310,720 to 1,048,576 bytes per Evaluator**, saving **262,144 bytes (20% of the cache's storage)**. The span covering key and validity metadata falls from 33 to 13 bytes. This is a verified layout/footprint result for this compiler/ABI, **not a 20% speed prediction**.

An eventual guarded candidate could retain every field, default value, cache index, full key comparison and arithmetic operation while changing only field order. The inspected immutable source uses named field accesses and value initialization, with no positional PawnEntry aggregate initializers or serialized layout. Because the type is public, external ABI/aggregate consumers still require consideration before broader adoption. It would need default-off byte identity, exact evaluation/search tests, ABI-size checks and native profiling before any optimization acceptance.

This is a more concrete structural change than eliminating a small fraction of repeated TT arithmetic: it reduces the footprint of an entire frequently accessed cache and places validity beside the key. **CPU-time headroom is still unquantified.** The current samples contain no cache-miss counters, no hit-rate breakdown and no controlled layout comparison. No production header was modified; the reordered type exists only in the separate layout probe.

## An apparent opportunity rejected

The piece evaluator's source computes queen bishop/rook rays for mobility and refers to the same attacks again for weak-queen detection. This initially looks redundant. Inspection of a fresh strict-FP/O3 optimized-tree dump for immutable `eval.cpp` shows GCC already reuses both ray results: `_3192` and `_3186` feed both the combined queen attacks and later `enemy_sliders`. Thus a source-only ray-reuse rewrite is **not supported** as an optimization by this evidence.

The focused excerpt is preserved in `hce_profile_lines_queen_ir.txt`. Its GCC “local count” and branch-probability annotations are compiler estimates, not recorded runtime counts. No claimed call-frequency evidence is derived from them.

## Uncertainty

- The profile was built with `-pg`; it is not the release code layout, even though nodes matched.
- Each original run contains only 27–69 HCE ticks. Most exact addresses appear once. Do not rank one-tick source lines as reliably different costs.
- Optimized DWARF can describe several inlined scopes for one instruction and can assign scheduling/prologue work to a neighboring source line.
- Four-byte histogram bins can cross instruction boundaries. Midpoint symbolication cannot reconstruct the exact interrupted instruction in every bin.
- Recurrence across the two depths/modes is useful context, not four independent repetitions of an identical workload. The NNUE modes search different positions/nodes.
- The residual NNUE-on path includes HCE; it is not a network-only evaluator. These observations apply to both HCE cache users but do not imply equal performance in the two modes.

## Reproduce without rerunning an engine

```sh
python3 forge-combo29/tests/hce_profile_lines_map.py \
  --binary /workspace/shared/forge-build/hotspot-profile/forge-gprof \
  --decoded forge-combo29/tests/hotspot_profile_decoded.json \
  --profile-metadata forge-combo29/tests/hotspot_profile_results.json \
  --output /tmp/hce-profile-lines.json
```

The standalone layout probe uses only the existing immutable source/include snapshot:

```sh
g++-14 -std=c++20 \
  -I/workspace/shared/forge-build/hotspot-profile/source/forge-combo29/include \
  forge-combo29/tests/hce_profile_lines_layout_probe.cpp -o /tmp/hce-layout
/tmp/hce-layout
```

The optimized-tree inspection compiled only immutable `src/eval.cpp` with the recorded strict-FP/O3/x86-64-v4 flags plus `-fdump-tree-optimized`; it did not execute an engine or modify production. No additional snapshot, Windows executable or bundled input was accessed.

Artifacts: mapping script/result, standalone layout probe/output, focused validity-check disassembly and optimized-tree excerpt. **Candidate status remains UNPROVEN.**
