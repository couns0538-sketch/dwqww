# IDEA_SOURCE - R13 P4 (v2-feature nets with bullet)

## Licences of what the trainer links (checked in the crates' Cargo.toml, 2026-11-01; corrected after CR R13)
| component | licence | role here |
|---|---|---|
| bullet (jw1912/bullet, commit da426a49, `F:\bullet_hip\src`) | MIT | trainer library, used through its public API |
| bulletformat 1.8.0 | MIT | board / data types of the trainer |
| viriformat 2.0.1 | MIT | dependency of bullet_lib |
| **sfbinpack 0.6.4** | **GPL-3.0** | dependency of bullet_lib (binpack reader) - **trainer tool only** |
| **montyformat 0.9.2** | **AGPL-3.0** | dependency of bullet_lib - **trainer tool only** |
`forge_v2_bullet` links bullet_lib, so the trainer binary contains GPL-3.0 and AGPL-3.0 code: it is an offline training tool
that runs on the PC and is never shipped with Forge. Nothing from sfbinpack, montyformat or any other GPL / AGPL code goes
into Forge source (no code copied, translated or paraphrased; no constants). The nets it produces are data.

## Ideas and own code
- Feature definitions: Forge's own (forge/nnue_v2.hpp: C5 output buckets, O6 threats, O7 pawn pairs, by Opus); the Rust
  input type in forge_v2_bullet/src/main.rs re-implements those definitions (own code).
- Own code: forge_v2_bullet (MIT, like the Cargo.toml says), export_v2.py, eval_ref.py, make_random_net.py, parity_v2.sh,
  v2_eval.cpp. forge_nnue_v2.py is the crew's own tool (unchanged copy from forge-bundle-int b7c17722).
- Status: UNPROVEN. No net, no Elo claim.
