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

**3 confirmed / 2 refuted / 1 unmeasured.** (I first wrote "5 of 6 refuted" by eyeballing the table; the arithmetic
against my own pre-registered kill ranges says 3/2. Corrected in place, correction visible.)

## What Step 2 should now target — stated as a hypothesis, not a patch claim
The expensive case is *a perspective whose king key changed*, and the code answers it with a rebuild even though the
**piece placement of the other 15 pieces is already correct in the parent's accumulator**. A cheaper path would carry
the parent accumulator forward and apply the king-column change (one column), but the feature index depends on
`key.bucket` and `key.flip`, so *every* feature index changes when the bucket changes — which is exactly why the code
rebuilds. **I am not claiming a patch exists.** File 7 requires every bench, node row and eval value to stay identical;
a bucket change permutes all 768 features, so a same-numbers speed patch here would have to be a better rebuild (e.g.
summing columns in a different order is not bit-identical for int16 saturation), not a shortcut. That is the honest
state: the hot spot is identified, the fix is not obvious, and guessing one would waste a build cycle.

## Status
**NEW, corrected from my own first version; needs independent confirmation.** Reproduce with counters at the two
sites above. The reproducible claim: under PC20 + the file-7 test net, **18.8 % / 19.8 % / 20.6 % of replay evals on
`bench 11` / `12` / `13` take the full-rebuild branch**, at **7.25 columns per refresh** and **~0.08 undone plies per
failure**.
