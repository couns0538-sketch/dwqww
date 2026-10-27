# S12 data-only publication view — 2026-10-27

Status: SOURCE-ONLY PREPARATION with separately reviewed ON-framing successor. All actual S12 native outcomes remain UNVERIFIED. This local view is ready for root publication review; it is not a published or accepted engine candidate.

The frozen original 44 payloads, separate successor 32 payloads, and standalone independent review 13 files are copied byte for byte. Both original SHA manifests are preserved with `_ORIGINAL_LAYOUT.txt` basenames. The root `SHA256SUMS_20261027.txt` describes this view's actual paths. `SOURCE_TO_VIEW_MAPPING_20261027.json` maps all 91 original files to their view paths, with original byte counts and hashes. The duplicate thirteen review files intentionally preserve both source layouts.

## Original layout mapping

- `/tmp/forge_sol_S12_native_prep_20261027/` -> `original_native_prep/`; its manifest basename becomes `forge_sol_S12_native_SHA256SUMS_20261027_ORIGINAL_LAYOUT.txt`.
- `/tmp/forge_sol_S12_ONframing_successor_20261027/` -> `ON_framing_successor/`; its manifest basename becomes `forge_sol_S12_ONframing_SHA256SUMS_20261027_ORIGINAL_LAYOUT.txt`.
- The successor's `forge_sol_S12_ONframing_tool_successor_20261027.patch` -> `ON_framing_successor/forge_sol_S12_ONframing_tool_successor_20261027_TOOL_DIFF.txt`, preserving exact bytes as an explicit text audit artifact. It changes no engine file and must not be applied inside the frozen original prep.
- `/tmp/forge_sol_S12_independent_source_review_20261027/` -> `independent_source_review/` with unchanged basenames.

Original-layout manifests retain their original relative paths, including the original tooling-diff name. Verify those entries through the explicit mapping, or restore a separate original layout before using them directly. Never rewrite the frozen manifests to make them fit this view. This is a data publication view, not a relocated executable packet; original source/dependency paths remain frozen inside its contents.

## Effective source preparation

The original ON qualifier is retained as known-failing observer history: required ON active/stats prefixes are rejected by the strict normal OFF S25 grammar. Only the two original ON feature qualification commands are superseded by the separate reviewed successor. Build/FIRST/full runtime-OFF Std, baseline reuse, helper, counter and bounded-parity commands remain as preregistered. Read `ON_framing_successor/forge_sol_S12_ONframing_preregister_addendum_20261027.md` for the exact Release and ASAN ON replacements.

The 34 original pure fixtures and 27 successor pure controls are PASS in preserved logs, including independent replay. They were not rerun for this view. They prove tool behavior only. Independent source review reports no remaining demonstrated must-fix in the exact successor inspected. Its JSON SHA256 is `009d0cbb220d6713458eb0669e060e8148dea63a0843149a5dd20fc949a98b89`; Markdown SHA256 is `6828bdc509abea912ea20700aec8a03edbc27c56e4982dda827c9dd70dd4c98c`.

Native compilation, FIRST/current Std, ASAN/ON, actual RED/GREEN/counters/alias/parity, speed, Elo, Windows and adoption are UNVERIFIED. No engine patch is copied here. The existing six-engine-file v2 patch remains unchanged at SHA256 `66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d`.

## Earliest native build after S11 closure

Root must first review the source packet, verify actual S11 closure/publication, verify exact original packet/dependencies and baseline read-only binding, and grant a new finite serial invocation on the assigned CPU. The following frozen argv is prepared only; placeholders are not grants. Run from `/tmp/forge_sol_S12_native_prep_20261027`. The output directory must be new. No native invocation was performed for this view.

```bash
taskset -c 2 nice -n 19 python -B /tmp/forge_sol_S12_native_prep_20261027/forge_sol_S12_build_native_20261027.py --execute --authorization-reference ROOT_SUPPLIED_NEW_SERIAL_LEASE --s11-published-commit ROOT_SUPPLIED_VERIFIED_40_HEX_PUBLICATION_SHA --base Lprime --role candidate --feature OFF --profile Release --out /tmp/forge_sol_S12_native_20261027/Lprime_candidate_Release_OFF_build --cpu 2 --max-seconds 900
```

After the fresh main build, execute its separate FIRST bare11 invocation immediately, then complete full runtime-OFF Std before ON or helpers. Continue one finite invocation at a time under root's lease; the full preregistration is not an automatic execution queue.

Root alone owns stage/commit/push and must verify durable readback. The observed branch/head was `forge/sol-pack31-20261025` / `dd3ab7d230dc04f60e0dad2705e7666318ed6b1a`. No Git mutation was performed here. Original files remain unchanged. No ELF, .o, .a, ZIP, license, AGENTS or new engine patch is included; all copied file modes are0644.
