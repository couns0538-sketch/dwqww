# R11 game provenance tooling — UNPROVEN

This is an evidence adapter and pack checker, not a PGN/binpack decoder or a
training launcher. It never derives a game ID from row order, move counters,
piece counts, shard names, or maximal FEN chains.

The production source population is pinned in `pack_io.PRODUCTION` to R10's six
complete input identities and row counts. The input schema is documented in
`REQUEST.md`. The builder copies each immutable input once into deterministic
gzip evidence. Raw bytes are hashed while consumed; the independent verifier
decompresses, recounts and hashes them again. Full-FEN state and labels are joined
back to original raw rows through the frozen cohort, not accepted from the
producer's count summary.

Historical authenticity is a trust boundary. An arbitrary file containing game
indexes is not an authenticated archive. `TRUSTED_PRODUCTION_ORIGINS` is empty
until independent review establishes the archived source's historical identity.
The request cannot authorize its own origin digest. Binding maps have a second,
independent `TRUSTED_PRODUCTION_BINDINGS` registry, also initially empty. Each
reviewed binding digest is tied to every exact population-input SHA256. A real
archive can contain identical FEN/ply positions in different games; matching
those fields alone does not authenticate which original game produced a row.
The normalized
`archived-game-rows-v1` adapter only accepts reviewed archives; it makes no claim
that a digest alone proves history. Copied or relocated identical archives keep
the same digest/game identity. Repacked exports need a separately reviewed
canonical-origin adapter; they must not be given new IDs to hide overlap.

Without origins, every original population row receives a compact UNTRACEABLE
range outcome with null `game_id`; no retained training row is emitted. The
verifier returns BLOCKED with `game_overlap: null`, not a vacuous zero. Complete
013/014 coverage is always required. A successful synthetic control is labeled
FIXTURE_PASS and cannot authorize production or training.

## Execution

Run only through the root task's reviewed D-only Idle CPU launcher, after lane
admission. Both CLIs require `--threads 1` and support no GPU or training path:

```
python -B build_game_provenance.py --request REQUEST.json --out NEW_PACK --threads 1
python -B verify_game_provenance.py --pack NEW_PACK --out NEW_AUDIT --threads 1
```

All output paths must be absolute under D:/a11. A native invocation currently
requires the shared CPU lane to become available; setting a flag is not an
admission substitute. No commands above were executed during initial authoring.

`--resume` resumes only after committed input-copy boundaries. It rechecks the
request, bundled bytes and original files. Orphan pending files or partially
processed row output are preserved and require a fresh attempt. Processing-state
SQLite lives beside the pack, so it cannot inflate or invalidate the sealed
artifact census. This is a deliberately narrow resume contract; production
mid-processing restart equivalence is not claimed. Fixture cooperative replay
checks input-boundary interruption without killing or suspending a process.
This is an INCOMPLETE part of the approved plan: output-shard/checkpoint resume
at all production fault points is not implemented or proven. A dedicated fixture
checks refusal and preservation of partial processing state. The current tools
must not be described as completing the approved restart-proof requirement.

Retained row chunks use 50,000 rows, gzip level 1, mtime 0, empty filename,
canonical ASCII JSON and newline delimiters. Input copies preserve every byte
under gzip. The compact exclusion ledger is capped at 100,000 ranges; more
fragmented evidence fails closed rather than growing unbounded memory.

`MD5SUMS` and `SHA256SUMS` cover every pack file except the two manifests
themselves. The verifier checks exact coverage, hashes, complete population
accounting, original-state correspondence, recomputed IDs and game sets. It
uses its own SQLite audit and does not import builder logic. The same-game,
different-position negative rewrites valid checksums, so it exercises the
semantic overlap guard rather than merely a checksum failure.
The pack includes the exact verifier and shared format helper under `tools/`;
the verifier checks its executing code identities against those bundled bytes.

Admission reserves all input/archive/binding copies, row outputs, SQLite payload
and index overhead, rollback journals, and fixed metadata headroom. Input byte
sizes are measured before output creation; archive/binding row and byte metadata
is mandatory and checked against consumed bytes. The verifier independently
reserves its own emitted-row and original-state indexes. Live guards check drive
floors while parsing/inserting/outputting and every MiB of checksum reads, with
at least one resource check per 4096 records or MiB. They track retained owned
outputs/indexes against the reservation. No failure triggers process control or
cleanup. Windows trailing-dot/space aliases and reparse ancestors are rejected
root-to-leaf before any descendant is inspected.

## Current validation status

The test suite is written. Native RED/GREEN execution is DEFERRED because the
permitted CPU lane is occupied; the parent explicitly ruled that safety takes
precedence over TDD execution order. No passing-test claim is made. Tests retain
their fixture directories under the launcher-provided D:/a11 temporary root.
The regression suite does not read private datasets.
