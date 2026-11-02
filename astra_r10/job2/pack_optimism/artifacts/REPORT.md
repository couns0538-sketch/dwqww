# Job 2 — BLOCKED / UNPROVEN

Entered after Job1 was sealed and pushed as a565951a238c6a17ca52bd93d9b4d60125924d5c.
Live remote heads on2026-11-01 still matched the requested bases:

| Item | Head | Decision |
|---|---|---|
| P4 | df79fb6e33e0ec45e4bdf40cbbdfadb3b6fc27a6 | Not skipped for newer work; blocked on required CR inputs |
| P7 | cd9cb992fd6a6b05766d1117c1de441a430586a9 | Not skipped for newer work; blocked on required CR input |
| Status | 43af044a14a375b653f3d0bc633d9f476325ca81 | Read; its earlier progress table is not substituted for current heads |

Frozen Git copies and per-file SHA256s are in inputs01/INPUTS.json. The recovery
worker ran Idle with one worker and checked spare-core load before fetching.
Only the owned D:a10 repository was changed. No Opus branch/folder was modified.

Required CR commits1e7b5d20,cc826b0a and129d440e cannot be recovered from this
repository: remote commit lookups return422 and original local objects are absent.
The exact delta path at cc826b0a returns404. Relevant branch/commit searches are
empty. Unrelated short-SHA collisions were rejected. Original lookup evidence is
in recovery/cr_lookup.json and recovery/REPORT.md. Repeated recovery failure stops
the affected items under Couns's stop rule; no patch is invented or substituted.

| Required check | R10 result |
|---|---|
| P4 CR patch + delta applied | BLOCKED, originals unavailable |
| Fresh H256 parity / larger widths | UNVERIFIED, not run |
| Stale ref deliberately refused | UNVERIFIED, not implemented on an unpatched substitute |
| P7 CR applied | BLOCKED, original unavailable |
| Six original PGN SHA256s | UNVERIFIED; committed inputs.sha256 contains only derived files and evaluator |
| Widened-range separate fits / held-out CI | UNVERIFIED, not run |
| New default-off candidate builds / OFF pins / perft / reproducibility | UNVERIFIED, no candidate built |

The P7 report locates its original PGNs on forbidden F: and its fitting data are
not committed. No F: or Opus folder was accessed. The existing six PGN names and
derived-file hashes are preserved in the copied report; they cannot supply missing
PGN hashes or authenticate an independently reconstructed split. Existing P7
fitted values and CIs are historical Opus evidence, not an R10 refit.

No new seed was consumed. EvalMatScale remains0 in any future separate candidate;
no combined gate is proposed. No engine build, parity run, training, GPU, gate,
match or SPRT was performed in Job2. P5 was excluded.

## Separate incomplete handoffs

pack_rule50/ and pack_optimism/ preserve the same frozen input/recovery evidence
with distinct blocked candidate intents. Both are SEALED_INCOMPLETE / UNPROVEN;
neither contains a new accepted candidate executable or a fitted option value.
Review owners: CR and Engine Strength. A checksum PASS establishes copy integrity
only. These folders cannot be queued as gates.

Resume only with authentic CR commits/exports and permitted frozen original PGNs
plus the exact derived fit inputs. Recheck Opus heads first; skip newer work.
Then apply CR in new copies, run P4 fresh-reference refusal/parity and the separate
widened P7 fits with an unused bootstrap seed, preserve the80/20 game split,
report held-out loss/CI and boundaries, and qualify each candidate with the exact
kit and OFF pins. Crew alone decides later UHO gates. Continue now to Job3.
