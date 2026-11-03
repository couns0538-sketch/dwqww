# Adjacent segment evidence, schema 1

`r14_segments.py` observes full-state legal links between consecutive selected
physical rows. Its segment IDs are inferred labels. They are not authentic game
IDs, and its overall status remains `UNVERIFIED` without original identity and
historical writer binding. A completed scan does not certify separation.

The scanner requires the pinned completed production helper qualification with
at least one million resolved one-ply comparisons. Deep qualification unknowns
are recorded separately; production scan unknowns remain unresolved evidence.

```
python.exe -I D:\a14\tools\r14_segments.py --mode production --cpu 3 
  --qualification D:\a14\sep\qualification-million01\REPORT.json
  --qualification-md5 b91461a33503289c3025b5723d202d72
  --out D:\a14\sep\segments-production01 --seconds 10800
```

This is a command synopsis, with line breaks for readability. Use the authorized
resource launcher or one command line. Production launch follows candidate review
and a fresh shared-workload health check. `--mode jobA` selects the other scope.

## Input scopes

Production source IDs are shard numbers 12, 13, 14, and 15. Shards 13/14 are
scanned completely; shards 12/15 include their first and last 50,000 physical
rows. The skipped middle becomes a scope gap. JobA source IDs 0/1 mean shards
001/002: all of 001 and the first 583,415 rows of 002 are scanned, with 002 rows
533,416 through 583,415 marked context. Every selected source is consumed and
hashed in full, including unscanned rows.

`source_specs` binds each source ID to path, shard, expected MD5, selection,
limit, and target limit. `input_receipts` provides the consumed MD5, full row
count, byte-consumption completion, full-source parsing coverage, selected and
target key fill rates, selected ranges, context count, and selected endpoint
openness. `chain_windows` explicitly lists each selected window with first and
last line and `open_left`/`open_right`. These flags mean that additional physical
rows in that source were omitted outside the window. A physical file edge is
not thereby an authenticated game edge. `cross_file_adjacent_pairs` records each
tested physical seam, including its witness or unresolved outcome.

## Binary maps

Every `artifacts` entry contains `source_id`, `kind`, `path`, `md5`, `sha256`,
`bytes`, and `records`. Parts appear in per-stream order and are at most 10 MiB.
All integer encodings are unsigned little endian. Line numbers are one based.

| Kind | Struct | Bytes | Fields |
| --- | --- | --- | --- |
| ranges | `<IIQB` | 17 | first_line, last_line, segment_id, start_code |
| pairs | `<IBI` | 9 | right_line, outcome_code, nodes |
| boundaries | `<IBI` | 9 | right_line, outcome_code, nodes |

There is one `pairs` record per scanned row, including scope events. A regular
pair's left row is the preceding physical row; for a tested seam it is the last
row of the preceding source. Scope events have no tested left row. `boundaries`
contains every record whose code is nonzero, including unresolved scope events.

Segment IDs start at 1 and increase globally at every non-REACHABLE event. They
never recur in a source. A verified REACHABLE seam closes the left source range
and starts a right source range with the same ID and start code 0. Its JSON seam
entry names `continued_segment_id`. A range never spans omitted rows. All
scanned rows, including invalid ones, receive exactly one range owner.

| Code | Status | Reason |
| --- | --- | --- |
| 0 | REACHABLE | legal_witness |
| 1 | UNREACHABLE | nonpositive_ply_gap |
| 2 | UNREACHABLE | result_mismatch |
| 3 | UNREACHABLE | exhaustive_no_path |
| 4 | UNKNOWN | gap_exceeds_k |
| 5 | UNKNOWN | node_limit |
| 6 | UNKNOWN | invalid_input |
| 7 | UNKNOWN | missing_parsed_row |
| 8 | UNKNOWN | transport_error |
| 250 | UNKNOWN | scope_start |
| 251 | UNKNOWN | scope_gap |

Codes 250/251 are not pair checks. Neither those codes nor any other UNKNOWN
provides a certified game boundary. UNREACHABLE proves only that the tested
left/right states cannot satisfy that exact bounded link; it does not supply an
original game identity. Positive witnesses prove reachability, not identity.
Every positive witness is replayed through an independent legal-move API and
compared against all six target FEN fields, including raw en passant and clocks.

The JSON embeds this table and the struct layouts. `pair_counts` and
`reason_counts` exclude scope events. `source_counts` includes scanned/valid,
target/context rows, tested outcome totals, and scope event counts. `complete`
means source processing and map sealing finished with unchanged tool identities;
the separate reasons and key-fill fields expose unresolved evidence. Interrupted
scans retain sealed parts and an incomplete report when resource rules permit.
Hard resource stops emit a stdout refusal and discard buffered map tails instead
of allocating additional evidence. No dataset copies or disk hash sets are made.

`qualification`, `native`, `pins`, and `tool_identities` bind exact path, MD5,
and SHA256. Every identity is rechecked before report publication. Output reports
are atomically renamed from a freshly written part file after resource checks.

## Reusable APIs

`select_source(SourceSpec, receipt)` yields `SourceRecord` values while hashing
the complete source. `selected_records(specs, receipts)` identifies physical
adjacent-file seams. `scan_pairs(records, query_many)` emits `PairEvidence`,
with bounded batches and strict reply count/ID checks. `SegmentAssembler` sends
range tuples to its callback, and `iter_ranges(paths)` reads ordered parts.

The synthetic-only `fixture_audit` requires explicit authentic truth supplied by
the test. It rejects straddles, shuffled chains, and inconsistent results. Missing
rows, missing event coverage, and unresolved links cannot produce fixture PASS.
