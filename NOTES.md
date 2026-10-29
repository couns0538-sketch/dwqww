# Round-two completed continuation checkpoint — 2026-10-29

B1–B7 are finished on independent astra2-* branches from b7c1772. FINAL_REPORT_R2.md is the durable index of exact commits, original logs, every bench result, known failures and next integration steps. No accepted branch was modified; no files or branches were deleted. Tested Release Linux binaries are retained under astra2_evidence/B7/native_binaries with exact source/tree/network provenance. They are not Windows binaries.

B1 review addressed partial-main PV preservation, capped helper ranking, both TB score signs and brittle tests. B2 budget invariant is fixed, while the independently reproduced baseline SMP mate-search flake remains open. B3 adds v2 preflight tests without changing the already-correct loader; v3 is deferred. B4 exposes all tunables and adds precise option diagnostics. B5 ports default-zero SingularV2 and N1 with CorrExt exclusivity. B6 enforces exact OFF matrices and preserves interrupted checkpoints.

B5 complete Release and leak-enabled ASan/UBSan CTest:56/57, four known forge_tests diagnostics, zero sanitizer findings. Initial sandbox-runtime failure remains preserved. B6 has9fake test methods, CTest1/1,15preset matrix cells plus5finalOFF cells passing. No speed or Elo claim.

Next: independent review/gating of these isolated candidates; reconcile FB2 snapshot fields, seven preset-owned values and B4 override tracking on a new integration branch. Re-run combined OFF pins/perft/full tests/sanitizers before acceptance, then equal-time fastchess strength gates. Actual Windows, TSan, external Syzygy and combined-source validation remain unverified. Do not repeat completed investigations without a changed source or unresolved question. Preserve /workspace/dwqww's original dirty checkout.

IDEA_SOURCE: user round-two job and checkpoint requirements; existing chess validation/evidence workflows.
