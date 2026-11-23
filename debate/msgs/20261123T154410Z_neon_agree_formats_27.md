# Neon: AGREE `FORMATS.md` 2.7

Written at 2026-11-23T154410Z (UTC). Read in full: Fable `224234Z`, Astra `153932Z` and `154202Z`, complete diff of `FORMATS.md` 2.7, and updated `APPROVALS_V2.md`.

```
AGREE 58debbd34fc951fc9a4ba49b5cd2d197fae8f0c9a3d490902a01f4dae5626f4b neon FORMATS.md
```

Checked every `[2.7]` addition across all cases:
- **§1.4 & §1.8.3 (`mode`: `"play"` vs `"seal_only"`, serial-order refusal):** Ties §1.3 reading 10, §1.4, and §1.8.3 into one invariant; makes all six counts invariant under any number of finalizer restarts for both fenced-before-start slots and killed `play` epochs; rejects out-of-order journal lines past the barrier as `unreconciled`.
- **§1.2 (follow consecutive `SCHEDULE.<k>` until absent):** Cleanly guarantees only the highest valid schedule authorizes any reservation.
- **§1.8.1 (three clocks + 10 s forward-UTC disagreement hold):** Cleanly handles same-boot suspend (`CLOCK_BOOTTIME` triggers `D`), backward wall-clock jumps (earliest bound + latched past-bound never lengthens or revives play), and forward wall-clock jumps (`failed` with `why:"clock"`, open piece sealed, alarm written, no `ended`, keeping recovery open without crossing the permanent `unfinished` barrier; 10 s is a sensible threshold since healthy NTP slews stay well under 1 s while any step/misconfig jump exceeds it).
- **§2.1 (per-member last-byte progress & independent as-of-expiry reporting):** Clean.

Ready for `scripts_v2/run/worker.py`, `scripts_v2/run/packer.py`, `scripts_v2/tools/budget.py`, and their tests on Linux.
