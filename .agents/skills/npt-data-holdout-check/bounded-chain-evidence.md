# Bounded chain evidence for deduplicated row streams

Use this reference when source rows contain complete FENs and White results but
lack trustworthy original game IDs. A successful sampled move-generator check,
a legal connecting path and an authentic game-to-row binding are different claims.

Read and hash the writer without modifying it. Identify game buffering, queue
serialization, filtering, seen-key omissions, rotation and restart/import behavior.
Present source explains possible behavior. Bind its historical version and
configuration to the actual frozen shards before attributing that behavior to
every row. A checksum sidecar alone authenticates bytes, not their producer.

For adjacent rows, use absolute ply from fullmove number and side to move. A
continuation requires equal White result and an exact legal path that preserves
all six endpoint FEN fields, including raw EP and halfmove clocks. Return an
explicit witness, a fully exhausted negative, or UNKNOWN. Depth limits, node
budgets, parsing failures, scope gaps and interrupted transport are UNKNOWN.
Validate each new original helper against an independent external oracle at the
requested sample size and include special moves, clocks and complete move sets.
Never reuse a qualification receipt for a changed executable.

A legal path can connect positions from different games. Conversely, filtering
and deduplication can hide more plies than any fixed search bound. Therefore:

- A positive path proves possible continuation, not shared original identity.
- If the exact endpoint ply gap exceeds the search bound, the result is UNKNOWN.
  If that gap is within the bound and the exact search exhausts every legal path,
  a negative rules out continuation between those endpoints. A longer path could
  not retain the endpoint fullmove number and side to move.
- An observed segment label is not an authentic game ID.
- Dropping a fixed number of stored rows is not a guard measured in legal plies.
- A conservative block split cannot satisfy a user's requirement for exact IDs
  unless those IDs and their row bindings are independently authenticated.

When comparing prepared groups with source segments, inspect omitted source rows
and every intervening segment boundary. A whole omitted segment can contain a
proven break. Keep UNKNOWN boundaries separate from proven mismatches. Physical
file seams and omitted windows need explicit scope markers; do not count a window
start as a tested negative. Keep all mismatches, not just examples or totals.

For zero-overlap numbers, publish the denominator and fill rate beside each key:
six-field FEN, board/side/rights/EP, and board/side. Complete input consumption and
100% key coverage are separate conditions. Invalid omitted rows and file tails
still affect source coverage. RAM-only 64-bit hash matches are candidates until
exact keys resolve collisions; missing rows never count as clean negatives.

Freeze inputs, tools, qualification and row-range artifacts by hashes. A final
report is published only after a temporary file writes, flushes and closes
successfully and the final storage check passes. Failed work leaves incomplete
evidence and cannot leave a usable PASS report. Preserve original failed logs.

The owned R14 helpers are catalogued in [the tool inventory](../../../TOOLS.md).
Their position-only and observed-chain reports have deliberately limited scope.
Apply the main skill's authentic-ID and full-state checks before export clearance.

A generated [identity ambiguity example](../../../sep/identity-ambiguity/README.md)
shows identical emitted row bytes from one legal game versus two legal games,
under an explicitly stated initial seen-state assumption. It validates why those
observations alone cannot supply original IDs; it does not assert ambiguity or
leakage in any actual production shard.
