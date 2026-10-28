# Astra continuation — 2026-10-29

Base: `opus-r3-stack`, `da15814975e224e770f4d25195e0551d02afae48`.

## A1 — not applicable, not in repo
The exact base tree has no `tools/forge_queue.ps1`. The owner confirmed the script lives only on the gate PC and explicitly instructed skipping A1. No queue code was imported or modified. Continue with A2, then A3–A6.

Previous Sol work remains in `/workspace/dwqww`, branch `forge/sol-pack31-20261025`, head `17aa0cae1d36bc88bf93e873905c058e0de5faac`; its uncommitted checkpoint and unrelated work are preserved. This new checkout is isolated under `/tmp/forge-astra-20261029`.

IDEA_SOURCE: Owner-provided A1–A6 specification and Forge's own source; no external engine code.

## A2 — implementation checkpoint; native qualification running
- Existing base already protects mates. Reproduced the remaining TB-score ranking overwrite in the real `better_thread_result`: 2 failing assertions on the unchanged base.
- Added UCI `SmpProtectProvenScore`, default false; only used by existing `SmpBestThread` selection. Mate behavior is unchanged. The new guard preserves the winning TB score band while tablebase scoring is active.
- Score provenance limit: `SearchInfo` has no proof/bound tag, and the current evaluator can reach that numerical band. This repair conservatively protects the score band; it does not prove every high static score came from a TB probe.
- Release build/full tests pending at this checkpoint. RED reproduction is the production ranking function; actual private selector fixtures are additional candidate tests.
- Base bench d11/13/16/20/22: **312866 / 862329 / 3024920 / 12389307 / 34048354**. These replace old h256_e12 numbers for this explicitly changed base. No speed/Elo claim.
- Recipe: GCC 14.2, Release, C++20, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`; CMake builds outside checkout.
