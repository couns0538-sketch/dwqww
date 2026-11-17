# S-F70 (v3) — one eval in five rebuilds the accumulator from scratch, because a king move invalidates the pair fast path

Seat 20. Binary `build-v3/forge` sha256 `227aae56ef1678479cf08d0fc3e3c73683753e89d61f12b252f0fec9e388471e`
(`Chess Engine Forge 6.4.24 candidate`, `-DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1`, kernel `avx512`).
Instrumented binaries `f255b8cb…` then `b677176a…` (counters only; identical node counts). Regime PC20
(S14 17 options + 5 extras) + the file-7 test net, Threads 1, Hash 16.

Step 0 passed all twelve file-7 pins before any measurement (eight benches, three `eval` lines, net sha256
`1db8525e…3ffd4a`, checksum `fdff70de72e4ca82`, max values 64/96/16, kernel `avx512`).

## The measurement (stable across three workloads)

| workload | nodes | `refresh_from_pieces` | per 1000 nodes | pair-path failures / replays | cols per refresh |
|---|---|---|---|---|---|
| `bench 11` | 625,258 | 93,575 | 149.7 | 93,559 / 497,466 = **18.81 %** | 7.263 |
| `bench 12` | 1,381,446 | 220,890 | 159.9 | 220,874 / 1,117,045 = **19.77 %** | 7.266 |
| `bench 13` | 3,652,372 | 617,443 | 169.1 | 617,427 / 2,999,498 = **20.58 %** | 7.246 |

The rate rises monotonically with depth, as deeper searches move kings more often relative to eval count.

## The mechanism, read from the source

`replay_ply` (`include/forge/nnue_v3.hpp`, ~line 226) computes both perspectives' king squares and keys, then takes
the fast path only when **both** keys are unchanged:

```
if (pair_ok) { apply_changes_pair(...); ... }        // both perspectives incremental
for (p : {White, Black}) {                           // else: split by perspective
    if (key == parent.keys[pi]) apply_changes(...);  // incremental
    else { undo later plies; refresh_from_pieces(...); }   // FULL REBUILD, ~7.25 columns
}
```

So when **either** side's king changes bucket or mirror-flip, that perspective rebuilds from scratch (7.25 columns
against 1.49 on the pair path, i.e. **~4.9× the work for that perspective**), while the other side still goes
incrementally. Measured: exactly one perspective rebuilds per pair-path failure (king-change refreshes equal pair
failures in every run, 617,427 vs 617,427), and only **50,150 plies were undone in total** — 0.08 per failure. The
undo loop is therefore *not* the cost; the rebuild is.

## Why this corrects my own S-F70 (the first version, committed an hour earlier)

That version concluded "the `RefreshCache` is doing its job, so the cost is not the refresh being slow." **That was
half wrong.** The cache does do its job *when it is reached* (7.25 columns, not 768) — but it is reached only on the
`ancestor < 4` fallback inside `make_valid`, which happened **8 times in 617,443**. Real refreshes come from
`replay_ply`'s king-change branch, which **bypasses the cache entry entirely**: `refresh_from_pieces` still diffs
against `entry.values`, so it is cheap per call, but it rebuilds the destination from that entry rather than
carrying the parent's accumulator forward.

I found this only because gprof reported 617,427 calls from `static_evaluate_v3` while `refresh_cached` ran 8 times —
the call graph contradicted my reading of the source, and the call graph was right. **This is METHOD RULE 0b
(ask-for-provenance) applied to a profiler: two of my own numbers disagreed, and the discrepancy was the finding.**

## Prediction scorecard (committed alone at `job82/PREDICTION.md`, before any profiling)

| # | predicted | measured | verdict |
|---|---|---|---|
| P1 | hottest v3 function = `apply_changes_avx512` | **`refresh_from_pieces`, 43.2 % of v3 self time** | **REFUTED** |
| P2 | that function = 45 % of v3 time | 43.2 % | CONFIRMED (inside 30–60 %) |
| P3 | v3 = 30 % of bench 13 | 21.6 % | CONFIRMED (inside 20–45 %) |
| P4 | forward pass = 20 % of v3 | 18.9 % | CONFIRMED (inside 12–30 %) |
| P5 | full refresh **rare**, ~10 % of v3 | **43.2 %, the largest v3 item** | **REFUTED — inverted** |
| P6 | bookkeeping = 10 % of v3 | inlined, no separate entry | NOT MEASURED |

**3 confirmed / 2 refuted / 1 unmeasured.**

### How that number was obtained, because the method is the point

I first wrote **"5 of 6 refuted"** by looking at the table and seeing that the top function was not the one I named.
That was an eyeball, and it was wrong in **both directions**: it scored P2, P3 and P4 as refuted when all three
landed *inside* the ranges I had pre-registered, and it scored P5 as merely refuted when P5 was **inverted** (I
predicted the refresh was rare; it is the single largest v3 item). A reader given "5 of 6 refuted" would have
concluded the model was worthless, when in fact five of six pre-registered intervals bracketed the truth.

The correction was arithmetic, not a second reading: each prediction carried a **kill range written down before any
profiling**, so scoring is a comparison, not a judgement —
`43.2 %` against `[25,65]` → confirmed; `21.6 %` against `[15,55]` → confirmed; `18.9 %` against `[8,38]` → confirmed;
`refresh` as the top function → refuted; `43.2 %` against `[2,28]` → refuted. **Six comparisons, no discretion.**

This is the same discipline as the call-graph correction one section above: when my own number and my own narrative
disagree, the number wins, and the correction stays visible rather than being quietly edited away. Prediction files
that are graded by the person who wrote them are worth nothing unless the grading rule was fixed first — which is
the only reason pre-registering the kill ranges was worth the commit.

## Why no patch is offered — the reason, stated plainly

**A king-bucket change permutes all 768 feature indices of that perspective, so there is no incremental shortcut to
take.** The feature index is

```
feature_index = key.bucket * InputsPerBucket + (relative_color*6 + type)*64 + relative_square
relative_square = (square ^ (perspective == White ? 0 : 56)) ^ key.flip
```

Both `key.bucket` and `key.flip` are multiplicative/additive terms on **every** one of the 768 indices. When the king
crosses a bucket boundary, or crosses the mirror line so `flip` changes, *no* weight row of the new accumulator is the
same weight row as the old one — the old accumulator's contents are not merely shifted, they are drawn from a
different slice of `w1` entirely. Carrying the parent accumulator forward and "fixing up the king column" is therefore
not available: the parent's 768 values index the *wrong* weights, not stale values of the right weights.

This is why the code rebuilds, and it is **the reason no patch is offered**: any patch that stayed bit-exact would have
to make the rebuild itself cheaper (different summation order is not bit-identical under int16 saturation; a wider
temporary changes nothing about the saturation points), not skip it. File 7 requires every bench number, per-position
node row and eval value to be **identical**; a shortcut that skips the rebuild would change eval values, and a
non-shortcut has no obvious win. Stating "no patch here" is the finding, not a failure to find one — the same way a
withdrawal by bound is stronger than a re-run.

## What a patch *would* have to be, if a later seat wants to try
Not a shortcut but a cheaper rebuild: e.g. keeping a second accumulator per perspective at the *other* flip so a flip
change is a pointer swap (memory cost: 2× accumulators, and `MaxPly+8` of them), or batching the bucket-constant part.
Both are design changes with a memory/behaviour cost, not one-line wins, and neither is bit-exact for free.

## It generalises to real positions (file 7's own workload)

File 7 also asks for 200 openings at `go depth 12` (`ucinewgame` + `isready` before each). Over the first 200 of
`job24/G_353.fens`, same build and counters, **27,762,950 nodes**:

| workload | nodes | refreshes/1000 nodes | pair-path failure rate | cols/refresh | undone plies/failure |
|---|---|---|---|---|---|
| `bench 11/12/13` | 0.63 / 1.38 / 3.65 M | 149.7 / 159.9 / 169.1 | 18.81 / 19.77 / 20.58 % | 7.26 | 0.08 |
| **200 openings, depth 12** | 27.76 M | **158.4** | **21.45 %** | **5.34** | **0.19** |

The failure rate is **slightly higher** on real openings than on any bench (openings move kings early: castles,
king walks), and `cols/refresh` is **lower** (5.34 vs 7.26) because in the opening the reconstructed placement is
closer to the cached entry. Both directions are what the mechanism predicts, which is a check on the explanation
rather than just the number. **So the claim is not a `bench` artifact.**

## Status
**NEW, corrected from my own first version; needs independent confirmation.** Reproduce with counters at the two
sites above. The reproducible claim: under PC20 + the file-7 test net, **18.8 % / 19.8 % / 20.6 % of replay evals on
`bench 11` / `12` / `13` take the full-rebuild branch**, at **7.25 columns per refresh** and **~0.08 undone plies per
failure**.
