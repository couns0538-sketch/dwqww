# offguard: OFF-path guard for the new default-OFF engine options

Three options added in the Sol-leftover round are default OFF, and their OFF builds are bench-identical to the AL1
lock, but they are not byte-identical:
- A1 `HistRework` (`opus-sol-A1`, engine commit `a8b63aae`): it adds a table of about 200 KiB per search thread,
  allocated even when OFF.
- S-A2 `NnueInt16` (`opus-sol-SA2`, `d2301c51`): the accumulator grows from 2 to 4 KiB per stack entry.
- S41 `NetScale` (`opus-sol-S41`, `5a197863`): it adds a branch in `Worker::static_evaluate`.

The PC measurements were taken under gate and training load and are advisory. This job measures the OFF builds against
the lock on a quiet GitHub runner, the way S29 and S-IT were measured:
- g++-14 with box flags, CMake Release;
- `uci_check --full` per build;
- `nm` sizes of the hot functions;
- `nps_ab.py` (from opus-sol-S29): ABBA order, fresh processes, 10 runs per side, bench d16 and d20, nodes must match.

Run: `.github/workflows/opus-offguard-ci.yml` on push, or by hand: `bash opus_round1/offguard/ci_offguard.sh <out>`.
