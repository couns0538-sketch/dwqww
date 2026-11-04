# Boundary evidence contract, schema 1

This candidate is unqualified until its focused tests, independent review,
legal-path filter qualification, and real native fixture integration pass.

`r14_boundary.py` defines `Endpoint`, `Population`, `read_window`,
`candidate_chunks`, and `count_candidates`. Retained physical rows that cannot
be parsed or independently validated are represented by `None`; they remain in
the Cartesian population and are counted once in the invalid-endpoint union.
An endpoint's absolute ply and physical line are validated before unsigned
array conversion. Piece losses are computed in signed int32, and popcount totals
are accumulated in uint16 before widening for the bound comparison.

The exact, disjoint accounting fields are `invalid_endpoint_pairs`,
`excluded_result`, `excluded_ply`, `excluded_clock`, `excluded_rights`,
`excluded_material`, `excluded_piece_squares`, and `survivors`. Their sum equals
`total_pairs` after a complete enumeration. An interrupted enumeration explicitly
retains `complete=false` and `unclassified_pairs`. Candidate tuples retain the
multiplicity of physical rows, even when FENs are identical.

`r14_boundary_run.py` requires the pinned million-pair native qualification and
a pinned `boundary_filter_qualification` PASS with at least 100,000 resolved
random legal paths, special move coverage, and scalar popcount checks. The
qualification binds the core and all recorded dependency bytes. The first pass
counts every survivor; a second pass repeats enumeration and resolves candidates.
Both complete passes' accounting totals must match exactly.

The source windows are the last/first 50,000 physical rows of 012|013 and 014|015.
Every source byte is consumed for its expected MD5, although only window rows
are parsed. Input receipts expose exact bounds, full row/byte count, metadata
before/after, `endpoint_key_fill_rate`, `endpoint_legal_state_fill_rate`, and
retained invalid-row counts. `full_source_byte_hash_verified` covers every byte;
`parse_scope=retained_endpoints_only` and `full_source_parse_verified=false`
explicitly avoid claiming that unselected source rows were parsed. Full-source
parse evidence requires a separately bound complete source scan. Rows are never
copied into evidence files.

The top-level report's `status` and `authentic_game_separation` remain
`UNVERIFIED`. `bounded_no_link_status` is a separate narrow verdict. It is FAIL
if a verified witness exists, PASS only if both complete finite populations
contain no link and no unresolved pair, and UNVERIFIED otherwise. A legal link
can arise between different original games. Original IDs and historical writer
binding are never inferred from this search.

Each seam contains `inputs`, `first_pass`, `search`, `artifacts`, `complete`, and
its own narrow verdict. `receipt_seal_complete` must be true before the narrow
verdict can pass or fail; interrupted or failed receipt sealing stays UNVERIFIED.
Sealing can resume after an interruption between closing and renaming a part.
Search fields include `candidate_pairs`,
`attempted_pairs`, `query_attempts`, `retried_pairs`, `unqueried_pairs`,
`initial_counts`, `retry_counts`, `final_counts`, `final_reasons`, `second_pass`,
and `complete`. Initial node-limit UNKNOWN results receive at most one retry
at 1,000,000 nodes; final UNKNOWN is never a negative. Initial budget is 100,000.

Query parts use little-endian `<IIBBBI`, exactly 15 bytes per record:

| Field | Type |
| --- | --- |
| left physical line | uint32 |
| right physical line | uint32 |
| exact ply depth | uint8 |
| attempt, 1 or 2 | uint8 |
| outcome code from the segment driver | uint8 |
| visited nodes | uint32 |

Positive JSONL parts preserve every physical endpoint pair with its depth,
node count, and UCI witness. Every positive witness is independently replayed
through legal moves and checked against all six target FEN fields, including
raw en passant and clocks. Parts are at most 10 MiB and are renamed atomically
after sealing; artifacts include full paths, MD5, SHA256, byte and record counts.
No candidate arrays or hash sets are written to disk.

The runner uses a single admitted Idle CPU, bounded request batches, the shared
resource guard, a monotonic deadline, and owned-child cleanup. On a hard resource
stop it emits stdout only and discards unsealed buffered tails. A regular timeout
may seal partial receipts if fresh resource checks permit. There is no resume
claim: each invocation requires a fresh output directory.

`r14_boundary_qualify.py --pairs 100000` qualifies only the necessary-condition
filters. Smaller runs carry `boundary_filter_smoke` scope and cannot qualify
production. Its deterministic seed and requested count reproduce the random
sequence. The existing native qualification is reused without modification.
Feature coverage counts only completed, verified random pairs and verified
special-path prefixes; a discarded shorter path contributes no capture or
promotion coverage.
