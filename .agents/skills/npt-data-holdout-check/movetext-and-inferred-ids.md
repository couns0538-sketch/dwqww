# Inferred groups and exact movetext identity

A name such as `source#ordinal` or `s0g17` is not evidence of authentic game
identity. Inspect the producer: resets in ply, result changes, increased piece
count, castling-right changes and source-file transitions produce inferred
groups. Filtering, deduplication and shard rotation can remove or split games.
Disjoint inferred groups establish only internal split consistency.

For available complete PGNs, hash a versioned canonical initial full position
and legal mainline moves. Ignore headers, comments, annotations and variations
so format changes cannot conceal identical complete games. Preserve original
archive hashes, game ordinals and authenticated population-row bindings separately.
The R13 helper uses SHA256 of `astra-r13-mainline-v1`, NUL, full initial FEN, NUL,
space-separated mainline UCI moves. Result is excluded from identity.

Exact movetext hashes do not establish equivalence of truncated or extended
versions, and cannot manufacture missing original row-to-game assignments.
Without authenticated complete train/holdout coverage, report game overlap as
null/unknown and status UNVERIFIED, even when available hash sets are disjoint.
Never prefix identities by split or shard to hide the same game across outputs.

Bound recovery searches to the user's time and access limits. Record scanned
roots, exclusions, caps and rejected candidates. If no authentic mapping is
recovered and the user authorizes fallback, stop recovery and improve independent
deliverables. A bounded search is not proof that no mapping exists anywhere.

Regression scenarios: same game with different comments/headers; same game with
different selected positions; missing bindings; inferred-ID collision avoidance;
bad setup FEN; truncated coverage; original state lost before label search.
