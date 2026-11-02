# Saved for later engine work

Requested by Couns during the Astra R8 data-quality continuation. These are
repository snapshots, not a second installation and not authorization to launch
engine builds, SIMD experiments or timing in the current data-only job.

| Saved skill | Future use |
|---|---|
| [forge-lock-proof-set](forge-lock-proof-set/SKILL.md) | Reproducible LTO+PGO builds, frozen option/node pins, perft and sanitizer qualification |
| [eval-exact-simd-port](eval-exact-simd-port/SKILL.md) | Exact scalar/SIMD/VNNI evaluation parity and negative-control evidence before timing |
| [abba-nps-timing](abba-nps-timing/SKILL.md) | Quiet-host A/A calibration and matched-work ABBA timing |

Source: [Forge crew skills](https://github.com/couns0538-sketch/dwqww/blob/27752e05d80d7280d7d9a83495052c03ef4ead15/plugins/forge-cpp-lab/CREW_SKILLS_20261101.md),
branch `astra-crew-skills-20261101`, frozen commit
`27752e05d80d7280d7d9a83495052c03ef4ead15`. Helpers and referenced contracts are
included. Each folder retains the full upstream MIT licence. Source blob pins are
in SAVED_ENGINE_SKILLS_SOURCE.json. No native qualification or timing was run.

Before using them later, recover the current engine lock and task permissions.
The build proof's T4 stage needs a separately authorized host; do not expand the
grok-pc two-worker budget. A bit-exact SIMD change preserves ON search identity;
do not force the behavior-changing proof's ON-difference condition onto it.
