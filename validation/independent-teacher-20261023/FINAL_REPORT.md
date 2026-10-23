# Independent-teacher pipeline — progress

Branch `forge/independent-teacher-20261023` preserves accepted pipeline parent
`27070fe` and engine source `1ab50b2`. Runtime search, shipped weights and core
binaries are unchanged. No old training rows, matches or Elo claims are included.
Six-hour window: October 23, 11:04 AM–5:04 PM PDT; new work stops 4:34 PM.

**The five-million-position corpus is not complete. No training, model-loss
comparison, audit-loss result or new network is claimed.**

## Published data and actual progress

Data branch `forge/independent-teacher-data-20261023` at
`f33b59b70291e9c2ebc44044e8a6bde35a037118` preserves 8,704 labeled whole games,
245,248 labels and 237,482 unique first-four-FEN positions. Both archive groups
were downloaded publicly and their sizes/SHA256 verified. Original games,
metadata, teacher UCI streams, native arrays and recovery manifests are retained.
The second group contains the complete aggregate; its count is not additive.

Local continuation is healthy: the 20:39:17 UTC snapshot contains 22,308 labeled
games, 634,095 labels and 610,520 unique positions. These active results remain
local until sealed publication. The previous whole-game timeout is preserved.
The exact game passed both reproductions; its original delay remains unexplained.
A reviewed 13-check guard permitted one unchanged retry at game 14,116, retaining
all completed labels. No incomplete game was counted or replaced by a draw.

Native preparation of the initial segment retained 126,155 train, 7,330 validation
and 6,671 audit rows in 143.398980908 seconds. Both heldouts also replay against
frozen original source bytes after explicit source relocation. These checks use
native HCE/features and do not evaluate a neural model on the audit set.

## Implemented and verified

The trainer licence and checksum mismatch are repaired; both current indices
now verify all 56 listed entries, and the original index is retained. The existing
validation skill was improved without creating a duplicate or claiming a global
installation. Failed startup, resume and handoff attempts remain preserved in
compact evidence archives.

Raw-segment merging preserves metadata exactly and passes six tests plus actual
coordinator ingestion. Four-process labeling passes its live integration and
review. Global prepared-shard merging reuses authenticated native arrays and
applies exact cross-shard audit>validation>train deduplication. A real C++ test
merges 2,001 positions from 80 games and two seeds; validation 253 and audit 341
both replay successfully, and optimization is correctly blocked below five million.
Four final focused tests pass. The broader source run passes 148/149 tests with
one external skip, plus all 13 generator tests. Native CTests pass 14/14 and the
unchanged benchmark is 292,545 nodes.

Four bounded hosted shards are ready: seeds 2026102301–2026102304, identical
Stockfish 19 depth 3 policy, 64-node game generation and 40% result blend. Each
stops at 1.45 million committed unique positions or 22:40 UTC and prepares native
arrays. All four must merge globally before the five-million gate. Six runner
safety tests and six workflow syntax checks pass. Fresh builds reproduce both
original cores/adapters byte-for-byte; real 16-game native preparation passes.
The external Stockfish payload is excluded from Git and recovered by exact hash.
All four hosted runners started and published exact-source checkpoints in run
`40021324995`. Observed builds and the external download passed, but generator
startup rejected the precreated empty discovery directory before accepting data.
Authentic stderr and original failures are preserved. The runner now releases
only asserted empty directories before starting the unchanged writer; eight
tests and two independent reviews pass. Unexpected contents remain untouched.
A real startup smoke is finishing before an isolated `-r1` retry.

Next: launch the reviewed isolated retry after its real startup smoke, verify
actual generated/teacher rows, and continue collection. Only a globally qualified, frozen corpus permits the
single eight-epoch warm start. Original validation selects the earliest minimum
trained epoch; a once-only 10,000-draw whole-game audit must beat shipped with a
95% interval excluding zero before any net-only branch is published. No other
network will be substituted. Exact commands and artifact hashes are in the
manifest and compact evidence archives. Playing strength remains **unproven**.
