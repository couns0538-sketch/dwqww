# Independent-teacher pipeline — progress

Accepted engine: **Forge 6.4.24**, source
`1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`. Pipeline parent `27070fe` is
preserved. Search, shipped weights, `src/`, `include/` and runtime binaries remain
unchanged. No old training rows or strength matches are used. This six-hour job
ends October 24 at 00:04 UTC; new work stops October 23 at 23:34 UTC.

## Qualified corpus

The actual global merge completed successfully in **605.149 seconds**, retaining
**5,988,335 positions** after exact first-four-FEN deduplication:

| Partition | Positions |
|---|---:|
| Training | 5,390,457 |
| Original validation | 295,653 |
| Frozen final audit | 302,225 |

Whole-game assignments use seed 2026102302 and remain disjoint. Cross-shard
selection removed 47,554 positions, with audit>validation>train priority.
Four fresh generation seeds mix Forge 6.4.24 selfplay and both colors against
exact source `5101c2529d386b7c3a04ba9156a69ee34df6bb43`. Labels come from external
**Stockfish 19, depth 3**, one thread per process, whole-game state isolation,
and a fixed **40% game-result blend**. Exact settings and hashes are frozen in
protocol 8. No Stockfish binary, network, code or GPL text is published.

[Hosted run 40023070082](https://github.com/couns0538-sketch/dwqww/actions/runs/40023070082)
closed all four collectors cleanly. All **48 archive groups** were recovered;
5,147 file paths and 2,605,540,329 bytes passed SHA256/size/mode checks. Original
CI data remain on four immutable, indexed GitHub commits. The global corpus is published at data commit
`442d5647612591a2d5a387c0513f5b482c07d6e8`: all 27 publication files
(723,367,402 bytes) passed public SHA256/size verification.

Independent checks authenticate 1,876 input bindings, every frozen output hash,
array shape/type and whole-game assignment. **63 deterministic row checks** across
all shards and partitions match original native arrays, recipes and raw teacher
records. Training guards accept the training role and reject audit-only data.
This does not claim a second independent reconstruction of global deduplication.

## Source and evidence

Trainer MIT notice and SHA mismatch are repaired; both current indices verify
**56 entries**, and the original index is retained. Existing validation skill was
improved without duplication or a global-installation claim. Native CTests pass
**14/14**; the unchanged benchmark is **292,545 nodes**. Failed startup and retry
attempts remain preserved. The first hosted fresh-output defect was repaired
and passed a real 128-game end-to-end smoke.

A separate local backup at data commit `ebfd2f49b1683ffe93f2786e3a592512ca7f0e8c`
preserves 1,251,735 labels, verified publicly. It is excluded from this corpus.
Its original interrupted-controller status remains unchanged; both producers
exited zero. The earlier isolated generation timeout remains unexplained.
Historical storage consolidation retained every path and byte; linked historical
builds are frozen and require fresh build directories.

## Training and next gate

The single preregistered warm start completed **8 epochs in 1,459.119 seconds**,
with input integrity passing. The fixed rule selected **epoch 7**:
original-validation blended MSE **0.03154945258561024**, versus shipped
**0.034083182956426566**. Teacher-only MSE worsened, from
**0.016892510091424517** to **0.017081781430475423**; the blended target remains
the preregistered primary metric. An independent closed-run review passed
**178 checks**.

Selected quantized include SHA256:
`1ffd149bd0b88b0799e448553162945f6884402a9d855337325bc472f95cc03e`.
Its source/data/checkpoint binding and 94,507 numeric weight changes were frozen
before the once-only final audit. On **302,225 positions from 10,781 represented
whole games**, audit blended MSE fell from **0.03453693078846838** to
**0.031588403018465105**, an **8.5373% reduction**. The 10,000-draw whole-game
bootstrap 95% interval for absolute reduction is
**[0.0025928813212714543, 0.0033175113598455327]**. Input integrity passed;
the audit ran once in 433.359 seconds. Teacher-only audit MSE was
0.017071947293679928 shipped and 0.017036363991417138 candidate.

The loss gate qualifies, but native correctness/perft/UCI and 10,000-position
C++ parity are still running. No new public network is claimed yet. Publish the
weights-only candidate only after these checks pass; do not reselect or retrain.
Dataset replay requires canonical Linux `/workspace` paths; native Windows
replay is unproven. Playing strength remains **unproven**, with no matches run;
the user PC supplies the game gate.
