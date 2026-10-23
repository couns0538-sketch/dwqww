# Independent-teacher pipeline — progress

Branch `forge/independent-teacher-20261023` preserves accepted parent `27070fe`
and runtime source `1ab50b2`. Search, shipped weights and core binaries are unchanged.
The trainer, licence repair, checksum repair and authentic generation/labeling tools
are public. Current source passes 14 native tests and the unchanged 292,545-node
benchmark. No old training rows, matches or Elo claims are included.

Six-hour window: October 23, 11:04 AM–5:04 PM PDT; new work stops 4:34 PM.
The required five-million-position dataset is **not complete**. No training,
model-loss evaluation, audit-loss comparison or new network has been produced.

## Completed and preserved

The initial dataset is published on `forge/independent-teacher-data-20261023`
at `a25c8e3d5f0a3e5a668f619297f1053f3849b7b1`. All six public artifacts
were downloaded and SHA256/size verified: 56,752,612 bytes. Its two archive parts
preserve 5,120 labeled whole games, 143,963 labels and 140,156 unique positions,
plus all original generation chunks and raw teacher transcripts. The recoverable
ZIP stream is 56,702,253 bytes; its exact hashes are in the manifest.

Further collection reached 8,704 labeled games, 245,248 labels and 237,482 unique
first-four-FEN positions. All producer/teacher processes closed and were reaped.
All additional rows, original logs and native arrays are now published at
`f33b59b70291e9c2ebc44044e8a6bde35a037118`. All seven new public artifacts
passed SHA256 and size checks.
The generator timed out on uncommitted game 14,116. That exact game passed both
cold native and production-reader reproductions in under 0.05 seconds. The
original delay remains unexplained; no clock fix or causal conclusion is claimed.
No incomplete game was counted or replaced by an artificial result.

Actual native preparation of the initial segment passed complete history,
feature/HCE, array, game-partition and cross-split duplicate checks. It retained
126,155 train, 7,330 validation and 6,671 audit rows in 143.398980908 seconds.
It correctly refused training below five million. A linear full-size projection
is about 85 minutes, not a measured five-million-row runtime. Sustained local
collection is also too slow for the remaining budget; bounded parallel hosted
resources are being investigated, without assuming their availability.

The original empty-chunk discovery failure and omitted explicit resume flag are
fixed; failed inputs and original process exits are retained. Four-process
labeling passes five tests, independent review and a live 16-game integration.
The complete earlier tool suite passes 137 tests with one external test separately
executed. Preparation passes 14 tests. Both current checksum indices verify all
39 listed entries; the original index remains preserved. The existing validation
skill was improved and checked without creating a duplicate.

## Frozen acceptance gate and next action

External Stockfish 19 depth 3 labels fresh Forge 6.4.24 self-play and games against
exact `5101c252`; the result blend is 40%. Whole games split 90/5/5. Exact-position
deduplication prioritizes audit, then validation, then training. Original raw
manifests, UCI streams, source and binary hashes remain authenticated.

The closed raw segments now merge without changing metadata; six tests and
unchanged coordinator ingestion pass. A 13-check guard permits one unchanged
retry at game 14,116, with an exclusive marker preventing a second launch.
The archive helper is reusable and passes nine tests.

Next: retain completed labels and execute that authenticated retry while
testing bounded hosted collection and parallel preparation.
Only a globally qualified corpus of at least five million positions permits one
eight-epoch warm-start run. Original validation selects the earliest minimum-loss
trained epoch. A once-only 10,000-draw whole-game audit must beat shipped with a
95% interval excluding zero before any net-only branch is published.
All settings and artifact SHA256 values are in `manifest.json` and `protocol.json`.
Playing strength remains **unproven**.
