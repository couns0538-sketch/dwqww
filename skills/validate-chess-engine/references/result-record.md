# Result and handoff record

Produce a compact summary backed by original evidence:

1. **Decision and scope:** accepted/rejected/inconclusive/blocked; correctness, speed, and strength conclusions separately.
2. **Identity:** source commits and dirty patches, generated JS/binary/network hashes, runtime/compiler, runner and opening-suite hashes.
3. **Protocol:** complete argv/config, start/end UTC, time control, threads/hash/affinity, seed, paired colors, adjudication, improvement versus non-regression purpose, SPRT hypotheses/error rates/model/budget.
4. **Results:** W/D/L, games and complete pairs, five pair bins, score, supplied statistical estimate/uncertainty with model, actual LLR/bounds/state and termination reason; crashes, illegal moves and time losses.
5. **Artifacts:** original PGNs, runner stdout/stderr, engine logs, test/bench outputs, source/patch, resumable state, and a SHA-256 manifest.
6. **Interpretation:** what the evidence establishes, what remains untested, the accepted baseline, and the next command/revisit condition.

Keep statistical values that are missing explicitly missing. A summary is an index into evidence, not a reconstruction of it. Retain interrupted and rejected runs.

## Check paired-count consistency

The provider documents `node scripts/check_match_counts.mjs RECORD.json`. That script could not be retrieved and is not included in this proposed bundle; run it only from an existing installation that actually contains it. The documented input schema is:

```json
{
  "schema_version": 1,
  "wins": 4,
  "draws": 2,
  "losses": 4,
  "pentanomial": [1, 1, 1, 1, 1]
}
```

This synthetic example contains five pairs, one in each pair-score bin. Bins are `[LL, LD, DD_or_WL, WD, WW]` from the candidate's perspective. The center bin contains either two draws or a win/loss pair; aggregate data must still be consistent with W/D/L totals and draw parity.

The tool checks schema, nonnegative safe integer counts, complete pairs, score/margin consistency, and possible draw counts. It returns a descriptive score only. A successful exit means the supplied counts are internally consistent; it does not establish authenticity, independence, absence of time losses, or an SPRT PASS. Verify the supplied counts against the original runner/PGNs and preserve their hashes.

Follow the engine project's existing checkpoint policy. If using `improve-grokchess`, use its recoverable-experiment reference. Save to the authorized persistent project destination and verify success; do not call a temporary path a completed backup.

