# Independent-teacher pipeline — progress

Accepted engine source is `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`
(Forge 6.4.24); pipeline parent `27070fe` is preserved. Search, shipped weights,
`src/`, `include/` and runtime binaries are unchanged. No old training rows,
strength matches or Elo claims are included. Six-hour window: October 23,
18:04–00:04 UTC; new work stops 23:34 UTC.

**The globally deduplicated five-million-position corpus is not complete.
No training, model-loss comparison, audit-loss result or new network is claimed.**

## Published data and current execution

Data branch `forge/independent-teacher-data-20261023` at
`ebfd2f49b1683ffe93f2786e3a592512ca7f0e8c` preserves **44,068 labeled whole games,
1,251,735 labels and 1,200,846 local unique first-four-FEN positions**. All 17
latest publication files were publicly read back: 402,498,630 bytes, matching
SHA256 and size. Counts include earlier groups and are not additive. Raw games,
metadata, UCI streams, original logs and recovery manifests are retained.

The local controller was deliberately interrupted to seal this partial backup;
its original `FAILED` status and signal error remain unchanged. Generator and
teacher coordinator both actually exited zero. The earlier whole-game timeout
remains unexplained; exact-game reproductions passed. One reviewed unchanged
retry retained completed labels. This local corpus is **excluded** from the
qualifying four-shard training merge.

Hosted retry [40023070082](https://github.com/couns0538-sketch/dwqww/actions/runs/40023070082),
source `5111164ae0e86ff49804cdd3a3289fcae00d8cd5`, has four verified builds,
real collectors and published nonzero labels. The closed 21:12 UTC monitor
recorded 3,553,628 labels and a sum of 3,410,637 within-shard uniques; this sum
is **not global deduplication or qualification**. Later, shard 3 completed
collection and native preparation with 1,590,224 within-shard unique positions.
Recovery verifies every archive/member hash and explicit source relocation;
original external Stockfish payloads are excluded from Git.

## Implemented and verified

Trainer MIT notice and SHA mismatch are repaired; both current indices verify
all 56 entries, with the original index retained. Existing validation skill was
improved without duplicating it or claiming a global installation. Failed
attempts and their original evidence remain in compact archives.

Prepared-shard merging reuses authenticated native arrays and applies exact
cross-shard audit>validation>train deduplication. A real C++ two-seed integration
retains 2,001 positions; all 253 validation and 341 audit rows replay. Optimization
correctly refuses this partial fixture. Broad source testing passes 148/149
with one external skip, plus 13 generator tests; focused final changes also pass.
Native CTests pass **14/14**; unchanged benchmark is **292,545 nodes**.

The first hosted attempt failed before data because a precreated discovery
directory violated the fresh-output contract. Original stderr is preserved.
The bounded repair passes eight tests and two reviews. A real 128-game startup
smoke passes generator, four teacher processes and native preparation: 3,338
labels, 3,311 unique positions, intentionally below the training gate.

## Next gate

Recover all four closed native-prepared shards, globally deduplicate, and require
at least **5,000,000 retained positions**. Publish that frozen dataset before
one preregistered eight-epoch warm start. Original validation selects the earliest
minimum trained epoch. Freeze genuinely changed quantized weights before one
10,000-draw whole-game bootstrap audit. Publish a net-only branch only when the
95% interval for shipped-minus-candidate audit MSE lies wholly above zero.
Otherwise publish data and honest results only. Artifact hashes, exact commands,
failures and continuation state are in the manifest and compact archives.
Playing strength remains **unproven**; the user PC supplies the game gate.
