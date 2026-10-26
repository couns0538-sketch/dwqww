# Independent read-only S16 review, 2026-10-26

The reviewer checked authoritative game-ID invariants, source mappings,
configuration dispatch, exclusions and resource preflight. No engine/compiler,
network/Git operations or heavyweight suites were run; no files were edited.

Findings were reproduced and corrected with recorded regressions:

- --config silently ignored --diagnostic-mode; the combination now rejects.
- Authentic-ID segments, indexes and repeated per-row IDs exceeded the original
  300 B/row scratch allowance. Separate stem, segment, row-ID and WAL reserves
  now supplement that base. The review's in-memory probes observed 911 B/row
  for distinct long IDs and 444.416 B/row for one long contiguous ID.
- Hardlink alias rows lacked a counts entry during preflight; they now use the
  pinned Reader directly, avoiding alias-stem collisions and missing keys.
- Character-count stem selection underbudgeted Unicode JSON removal lines;
  maximum serialized stem length now determines the ledger reserve.

Final source recheck: all findings addressed; no remaining actionable blockers
in the reviewed paths. The independent reviewer did not rerun the final suite.
The delivery's separate all41 GREEN log records the actual full verification.

The reviewer also confirmed the real916 diagnostic boundary statistics: 916
rows, 11 boundaries, 12 inferred groups and a maximum of 2 boundaries per 100
rows. A passed rate tripwire cannot prove absence of synchronized interleaving;
owner-authoritative IDs remain required by the production path.
