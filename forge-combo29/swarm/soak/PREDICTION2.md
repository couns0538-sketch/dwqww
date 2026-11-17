# PREDICTION 2 — committed before the MultiPV-cliff and resize-peak measurements

A second, separate prediction file. `PREDICTION.md` is left exactly as committed; this one
covers measurements added after it, and is committed and pushed **before** the first of them.

Context: `P5` in `PREDICTION.md` is answered by prior work in this audit, so my run is a
**replication** and FINDINGS.md says so rather than presenting it as a contribution.

## The prior figures I am quoting, and one discrepancy in them

Prior work's boundary table, cited as the source of record:

- **Hash 16: 60 MB works, 59 MB fails** (`docs/forge-findings.md`, §7 trap 3c boundary table).
- **Hash 256: 300 MB works, 290 MB fails** (same table).

The earlier summary I was given said "56 dies / 60 works" for Hash 16, and the document's own
boundary table says the failing cap is **59**. Those are different claims and I am not
inheriting either: **my own bisect stepped in 2 MB increments and never tested 59**, so what I
measured was "58 dies, 60 works" — which is consistent with 59 dying but does not establish
it. `P9` below resolves this by testing 59 directly, because I am the seat that will be
quoting the pair.

## The prior rule of thumb, which P7 tests directly

**The cliff is roughly table size + ~40 MB.** My own four-point bisect gives **Hash + 44 MB**
(52/60/108/300 works at Hash 8/16/64/256), which reproduces the prior Hash-16 and Hash-256
figures exactly and is within 4 MB of the stated ~40 MB.

Source, on this base commit (`6b98f217`):
- `search.cpp:2385-2386` — the MultiPV alternate table is sized
  `hash_mb = max(1, tt.cluster_count() * sizeof(TTCluster) / 1 MiB)`, i.e. **the same MB as
  the main table**.
- `search.cpp:365-366` (`TranspositionTable::resize`) — `make_unique<TTCluster[]>(new_count)`
  and only then `clusters_ = std::move(new_clusters)`, so a resize holds **old + new**.

## P7 — the `ulimit -v` cliff moves with MultiPV

If MultiPV-2 holds two full-size tables at once, the cliff is `2 × Hash + 44`, not
`Hash + 44`. This is a **numeric** prediction from the rule of thumb, not "roughly doubles":

| Hash | MPV 1 predicted | MPV 2 predicted | MPV 2, prior rule (2·Hash + 40) |
|---|---|---|---|
| 64 | 108 MB (measured already) | **172 MB** | 168 MB |
| 256 | 300 MB (measured already) | **556 MB** | **552 MB** |

- **P7a, Hash 64, MPV 2**: predict the lowest cap that completes all 12 searches is
  **168–176 MB**.
- **P7b, Hash 256, MPV 2**: predict **548–564 MB**, centred on **556** (prior rule says 552;
  the two differ by my measured 44 MB constant against their ~40).
- **Predicted ratio MPV2/MPV1**: **1.59 at Hash 64** (172/108) and **1.85 at Hash 256**
  (556/300). Both below 2.0 because the fixed non-table component is paid once, not twice.
- **KILLED IF**: the MPV-2 cliff at either Hash is within **25 %** of the MPV-1 cliff. That
  would mean the alternate table is not resident across the search, and the sizing reading —
  and the §3 cost model built on it — is wrong. **I would report that as the headline over
  every P1–P4 result.**

## P8 — the resize transient is old + new, and the allocator does NOT reuse the block

A single `setoption name Hash` from 16 → 256 in a warm process.

- Predicted peak RSS: `16 + 256 + B` where `B` is the non-table resident component
  (≈ 8.6 MB measured), i.e. **≈ 280 MB**.
- Instrument: **`VmHWM` from `/proc/<pid>/status`**, the kernel's exact peak-RSS high-water
  mark, not a sampling estimate. A 2 ms sampler can miss a transient shorter than its period;
  `VmHWM` cannot. (An earlier arm used a 2 ms sampler and reported 23.7 MB above
  `max(from,to)` for 16 → 256 — far below the predicted 16 MB of old table. That number is
  suspect for exactly this reason and is re-taken here with `VmHWM`.)
- **KILLED IF**: the peak is ≈ 264 MB (256 + B), which is what an allocator reusing the old
  block would give. Then the doubling is **not** real in practice and the `resize` concern is
  theoretical.
- **Control that makes it interpretable**: `256 → 256` must give `256 + 256 + B ≈ 520 MB`.
  The unchanged-value resize is the sharpest case. If that control does **not** peak near
  520 MB, the instrument is not seeing the transient and the 16 → 256 result proves nothing.

## P9 — resolving the prior discrepancy at Hash 16

- Test caps **57, 58, 59, 60** at Hash 16, MPV 1, 12 depth-10 searches each.
- Predict **59 fails and 60 completes**, matching the prior boundary table.
- **KILLED IF**: 59 completes. Then the prior table's 59 is wrong and the true boundary is
  between 59 and 60 with 58 as the last failure — my 2 MB bisect was coarse, not wrong.
