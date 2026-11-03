# Future self-play game provenance proposal

Text only: no production writer, configuration or dataset has been modified.

Assign an immutable game ID when a game starts: a persistent run identifier plus
a monotonically allocated game sequence. Worker IDs and output shard numbers are
not game identities. Retain the same identity through retries and file rotation.

Emit a .games sidecar containing game_id, final White result, producer source and
executable hashes, effective configuration, opening identity, random seed, and
all retained output ranges (file identity, first line, last line). A game split
across two files has two ranges but one game ID. Games yielding zero retained
positions still receive a completion record with an empty range list.

Retain legal mainline moves and the initial full FEN, or a separate hashed replay
artifact, so each retained row can be tied to its original ply and exact six-field
state. Record filtering/dedup reasons by original ply or a compact retained-ply
map. Do not attempt to reconstruct identity from adjacent position similarity.

Commit row bytes and provenance together using a recoverable transaction or an
append-only journal: fsync both payloads before publishing completion. Recovery
must reject a range missing either side of the binding; never silently regenerate
IDs. Seal finished files and sidecars with row counts, MD5 and SHA256 and bind
their hashes in a run manifest. Imported legacy files remain explicitly legacy
with absent game IDs; importing/checksumming them must not certify provenance.

Acceptance tests: file rotation within a game; interleaved worker completion;
crash before/after data flush and sidecar flush; interrupted publication; duplicate
game replay; zero-retained-row games; mismatched result; tampered range/hash;
overlapping ranges; missing original ply; and restart with unchanged IDs.

This can support future authentic-ID audits. It cannot retroactively authenticate
the existing 001-039 population without additional original evidence.
