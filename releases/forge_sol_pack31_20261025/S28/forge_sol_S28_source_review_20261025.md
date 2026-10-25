# S28 independent source review — 2026-10-25

Review scope: read-only source inspection by delegated reviewer `/root/pack24_next_recon/s28_cr_recon`. No build, test, engine run, adoption or strength conclusion was performed by that reviewer.

The reviewer inspected the original v2 implementation (`7530b90a4e5dcb2cfdd49f4fc186cabd78b193a8523700dc50637038c7543c7d`) and found a material qualification gap: candidate-net queued OFF pins were allowed to redefine their own known-failure values instead of matching independently observed base OFF pins. Five benchmark counts would not detect every such OFF leak.

The fix was written after an actual failing regression fixture. Final main-tool SHA256 `421b156ea48dfbaa5ff0e6b219baa6b4e3e3102b705d0c181144413e8cd39db3` compares exact case/depth/bestmove/score-kind/score/full-PV signatures and exact FAIL-line multisets before a queued stage is accepted. The reviewer inspected this final guard and found no further material defect in it. Native qualification logic is unchanged except recording that signature; final output also prints a numeric summary.

The reviewer suggested that the read-only postchecker verify complete stage IDs against the frozen plan and verify the native checksum manifest against its original captured hash before trusting stored results. Those suggestions were implemented in postchecker SHA256 `a091b30611829ddb8319b5d47e6bb2dea7cdb1b1e3042db6df2d7ac6aee15f08`, including actual inside-output sha256sum verification and all-three-case exit/EOF checks. A tampered-pin fixture fails before result/pin values are trusted. The coordinating root independently reviews the final implementation and executes the actual native postcheck; this source-review record does not substitute for either.

All TDD failures and subsequent green logs are retained separately. Native version provenance remains explicit: frozen v2 native matrix, final v3 pure guard applied read-only to closed evidence, final v3 dry-run trace. No full final-v3 native matrix is claimed unless an actual later run is recorded.
