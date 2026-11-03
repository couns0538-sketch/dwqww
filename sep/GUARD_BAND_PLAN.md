# Contiguous candidate split and explicit proof limits

This is a candidate construction plan, not a training export or separation PASS.
The user requires authenticated original game IDs. No legacy row-order split can
satisfy that requirement merely by assigning new labels or removing nearby rows.

Use the pinned jobA prepared rows and completed source-chain map. Choose one
contiguous train prefix and one validation suffix near the original1% validation
allocation. The cut must lie at an observed UNREACHABLE physical source boundary;
never cut a positive chain or call an UNKNOWN edge a proven game boundary.

Treat consecutive positive and UNKNOWN links as one conservative component for
allocation. Select a cut between components. Record the original native boundary
reason and exact source/row coordinates. Around the cut, measure guards using
absolute ply within the two adjacent components, whose ply numbers must increase.
Drop every row at distance at mostK=8 from either local boundary endpoint. If a
component is exhausted, list it explicitly and validate the newly exposed split
endpoint relation; do not quietly reinterpret a stored-row count as legal plies.

The candidate artifact contains row-ID intervals, every dropped row ID/reason,
counts, coverage and hashes. It contains no copied training FEN payload and is
stored under sep, never export. Both retained splits must be nonempty.

Check that no observed range or conservative component is allocated across the
cut, that all requested local guards were dropped, and that the final neighboring
retained endpoints have the recorded bounded relation. These are scoped checks:
they do not establish no interleaving, authentic original IDs, arbitrary omitted
continuations, or an exhaustive nonadjacent train/validation relation.

The overall candidate verdict therefore remains UNVERIFIED unless independent
original provenance supplies the missing identities. Export remains disabled.
Preserve the original split and all original source files. A candidate failure or
missing proof is evidence, not permission to weaken the required clearance.
