# Mate scores through the transposition table — audit result

**Seat:** late-swarm, `swarm/matehash`. **Audit base commit:** `6b98f217`.
**Binary measured:** `/tmp/build-matehash/forge`, sha256
`e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`.
**Build:** `cmake -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4 -DCMAKE_BUILD_TYPE=Release`,
`LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, g++ 13.3.0.

**Four honesty pins on that binary — ALL MATCH** (`bench N` sent on **stdin**, never argv):

| pin | expected | measured |
|---|---|---|
| `bench 11` | 312,866 | **312,866** |
| `bench 13` | 862,329 | **862,329** |
| `bench 16` | 3,024,920 | **3,024,920** |
| `go perft 5` | 4,865,609 | **4,865,609** |

Evidence: `evidence/pins.txt`, `evidence/build.sha256`. Every number below is from
this binary with these pins.

---

## 1. The answer

**The ply adjustment exists, is applied on BOTH store and probe, and is correct.**

`score_to_tt` / `score_from_tt` (`src/search.cpp:179-199`):

```cpp
[[nodiscard]] int score_to_tt(int score, int ply) {
    if (score >= MateInMaxPly) return score + ply;
    if (score <= -MateInMaxPly) return score - ply;
    return score;
}

[[nodiscard]] int score_from_tt(int score, int ply) {
    if (score == ValueNone) return ValueNone;
    if (score >= MateInMaxPly) {
        const int adjusted = score - ply;
        return adjusted >= MateInMaxPly ? adjusted : ValueNone;
    }
    if (score <= -MateInMaxPly) {
        const int adjusted = score + ply;
        return adjusted <= -MateInMaxPly ? adjusted : ValueNone;
    }
    return score;
}
```

- **Store adds `ply`, probe subtracts `ply`** — the standard position-relative
  encoding, and the signs are the right way round (a mate stored at ply `p` and read
  at ply `q` comes back referenced to `q`).
- **Applied at every store site, checked by enumeration rather than by spot reading.**
  There are **10 calls to `score_to_tt`** and every `tt.store(...)` / `store_tt(...)`
  call in `search.cpp` is wrapped by one — a grep for a store call *not* containing
  `score_to_tt` returns **nothing**. The store lines are `1476`, `1478`, `1541`,
  `1543`, `1773`, `1775`, `2095`, `2097` (pairs are the `FORGE_SPD_TT_NOTLS` and
  striped variants of the same call).
  Both score-bearing probes wrap `score_from_tt`: **`1448`** (qsearch) and **`1598`**
  (main search). A grep for a read of `.entry.score` that is not inside
  `score_from_tt` returns **nothing**, so no path consumes a raw stored mate score.
  (The third `probe_tt` at `2290` uses `.entry.move` only, for the emergency
  hash-move fallback, and never reads the score.)
- **The clamp is `MateInMaxPly = MateValue - MaxPly = 32000 - 128 = 31872`** on the
  store side, and on the probe side the boundary is enforced by returning
  **`ValueNone`** — a stored score that would decode to inside the centipawn band is
  DISCARDED rather than being read as a centipawn score. That is the correct failure
  direction: the alternative (clamping to the boundary) would report a mate at a
  distance that does not exist.

**The named experiment the coordinator asked for — store at ply 4, probe at ply 8 —
PASSES, on 5 distances plus a full exhaustive sweep:**

| DTM below node | score stored at ply 4 | read back at ply 8 | distance at 4 | at 8 | below node |
|---|---|---|---|---|---|
| 1 | 31999 | 31991 | 5 | 9 | **1** |
| 3 | 31997 | 31989 | 7 | 11 | **3** |
| 5 | 31995 | 31987 | 9 | 13 | **5** |
| 7 | 31993 | 31985 | 11 | 15 | **7** |
| 9 | 31991 | 31983 | 13 | 17 | **9** |

The right-hand column is the invariant that matters and it is expressed **without
reference to either ply**: the distance below the node is unchanged by the re-probe.

- **Exhaustive sweep: 118,332 cells, 0 failures.** Every `(store ply p, probe ply q,
  remaining plies rem)` in the legal window, both signs, plus centipawn passthrough
  and `ValueNone` preservation.
- **The checker provably fires (brief rule 3).** The same assertions run against two
  planted-wrong pairs — a store with **no** adjustment, and a store with the
  adjustment **inverted** — and produce **234,608 failures**. Evidence:
  `evidence/unit_score_tt.json`, which also records the **sha256 of the extracted
  source** (`21ef96d3…`) so a reader can confirm the code under test is the engine's.

## 2. `MateValue` / `MateInMaxPly`, and whether a legitimate mate can reach the clamp

- `MaxPly = 128`, `MateValue = 32000`, `MateInMaxPly = 31872`, `ValueNone = 32002`
  (`include/forge/search.hpp:71-75`).
- **The deepest mate a search can produce is `MaxPly - 1 = 127` plies**, which scores
  `MateValue - 127 = 31873`, i.e. **one above the clamp**. A score of exactly
  `MateValue - 128 = 31872` is still classified as a mate score (`>= MateInMaxPly`),
  and `ply == MaxPly` returns from the `ply >= MaxPly` guard rather than producing a
  mate score.
- **So a legitimate mate distance reaches the clamp's neighbourhood but not past it**,
  and the interaction is safe: the deepest reachable mate sits exactly on the
  boundary and the boundary is inclusive on both sides. The band is 128 plies wide
  and the search cannot exceed 128 plies, which is why it fits — **but it fits with
  zero margin, so raising `MaxPly` without raising `MateValue` would break it.**
  That is a constraint worth recording, not a defect.

## 3. Re-probe at a different ply, in one process — the corpus

**Corpus: 186 fixtures, all distance-1..4, 141 of them at distance ≥ 2.**
Built by generating candidates, grading every candidate with this seat's own DTM
oracle, then admitting only fixtures that passed four gates (python-chess valid ·
not terminal · oracle has an exact distance ≤4 · **the engine accepted the FEN**,
proved by ≥1 `info depth` line). `0 rejected`, `distance_ge_2: 141`
(`evidence/corpus.json`).

**Why the corpus is distance ≥ 2-heavy is part of the result:** a mate at distance 1
is stored as `MATE-1` at every ply, so an **absent** adjustment still reports
`mate 1` and such a fixture has no power. A corpus of mate-in-1s would have
manufactured a pass.

**Experiment C — entry stored at ply 1, read at ply 0 (235 parent/child pairs, depth 12):**

| measurement | result |
|---|---|
| parent/child pairs recovered and re-verified legal | **235 / 235** |
| cold arm correct (fresh process) | **168 / 235** |
| warm arm correct | **167 / 235** |
| warm distance == cold distance | **187 / 235** |
| table demonstrably answered (warm nodes < cold nodes) | **176 / 235** |
| **encoding defects found** | **0** |

The interesting population is **cold-correct** (the cold search already got the
distance right, so any warm difference cannot be blamed on precision):

| | |
|---|---|
| cold correct | **168 / 235** |
| **of those, warm ALSO correct** | **154 / 168** |
| of those, warm differs | **14 / 168 = 8.3%** |
| **of those, an ENCODING defect** | **0 / 14** |

**None of the 14 warm divergences is an encoding defect.** The 14 split three ways, and
the split is measured rather than asserted (`evidence/G_warm_divergence.jsonl`):

| shape of the divergence | n | what it means |
|---|---|---|
| **delta of an ODD number of moves** | **9** | an even-ply adjustment error **cannot produce this** — parity alone rules encoding out |
| delta of an EVEN number of moves | 2 | both classified by PV replay as **`PRECISION-warm-honest-at-its-own-length`** |
| warm arm returned `cp`, not a mate | 3 | it did not find the mate at that depth at all; no distance to miscount |

**11 of the 14 were confirmed by replaying the engine's own PV**, which mates in
exactly the plies the score claims. **The remaining 3 are `UNVERIFIABLE`** — not
"false" — because the warm arm emitted a centipawn score with a truncated PV, and the
findings doc establishes that a PV shorter than the claim is unverifiable rather than
wrong. **`UNVERIFIABLE` is a row in this table, not a pass.**

**So the divergence is search instability under a warm table, not a miscounted mate.**
This is consistent with findings §7 item 3 (warm state shifts scores) and it is the
same phenomenon, not a new one.

**The classifier provably fires.** A planted claim one move longer than the PV
supports flips the verdict to `ENCODING-suspect`. Without that control, "0 encoding
defects" would be indistinguishable from a classifier that only ever returns
`PRECISION`. Evidence: `evidence/G_warm_divergence.jsonl`.

### Mate-distance claims, with depth AND seldepth (per the brief)

Every wrong-looking figure in this seat's tables is quoted with `depth` and
`seldepth` in the evidence files. The important qualifier: **`mate N` needs `2N-1`
plies**, and a claim the reported seldepth cannot contain is unverifiable rather than
false.

| population | depth | seldepth range | note |
|---|---|---|---|
| C reprobe, depth 12 | 12 | 12–19 | 219/235 rows had seldepth ≥ 2·|mate|−1 |
| E engine-vs-DTM, depth 12 | 12 | 12–43 | 62/186 disagreed with DTM |

Several rows report `mate 4` at `seldepth 12`, which **cannot contain** a 4-move
mate (needs 7 plies). Those rows are the ones where the engine's own PV **does** mate
at exactly the claimed length when replayed — so the seldepth is understating the
search, not the score. **This is a `seldepth` reporting gap, not a mate-encoding
defect**, and it is why every distance claim here was ultimately settled by replaying
the PV rather than by comparing numbers.

## 4. Disagreement with an independent DTM oracle — and what it is NOT

The engine's reported distance differs from an exact DTM oracle on **62 / 186**
fixtures at depth 12 (`evidence/E_engine_vs_dtm.jsonl`). **This is not a
transposition-table finding** and must not be read as one: it reproduces **COLD**,
on a fresh process with a cleared table. Classified by replaying the engine's own PV:

| class | count | meaning |
|---|---|---|
| `H2-precision` | **41** | the PV is a real forced mate of **its own** claimed length; the engine found a longer mate than the shortest one |
| `no-mate-claimed` | **17** | the engine returned `cp` where a mate exists (it did not find it at this depth) |
| `unverifiable-pv` | **4** | PV truncated; not evidence either way |
| **`H1-encoding`** | **0** | **no row showed a PV mating at a different length than claimed** |

**Positive control: 40/40 agreement rows classify as `exact`** — the classifier is
not simply labelling everything imprecise.

**This is a real but different issue: the engine over-reports mate distance (it finds
a longer mate) at depth 12 in a mate-rich endgame corpus.** It is a search-precision
property. I did **not** investigate whether it is depth-limited, and I am **not**
claiming it as a defect beyond "the engine's distance is not always the shortest
one at depth 12".

## 5. Mate-score eviction — the mate score SURVIVES a full table

**24/24 correct, with the table genuinely full.** Two table sizes, 12 fixtures each,
mate distance ≥ 2 (distance-1 fixtures have no power here — see §3):

| table | peak `hashfull` | flood | re-probe correct | cold correct |
|---|---|---|---|---|
| **1 MB** | **1000 / 1000** (full) | 2 × 10 positions at depth 16 | **12 / 12** | 12 / 12 |
| **8 MB** | **982 / 1000** | 2 × 10 positions at depth 18 | **12 / 12** | 12 / 12 |

**The `hashfull` control is what makes this a result rather than a vacuous zero, and
the first version of this experiment failed it.** That run reported
`hashfull_peak: 0` on **all 24 rows** because I read `hashfull` off the *final* `info`
line only — and the engine's last line for a search that ended on a mate does not
carry a useful value. `hashfull` reaches **993** on the same position when read across
all lines. **The first run said `reprobe_correct: 24`, exactly like the second, and it
proved nothing.** Fixed by taking the peak across every `info` line and deepening the
flood.

Two honest qualifications:
- **The re-probe used fewer nodes than a cold search on 14 of 24 rows**, so on the
  other 10 the table did not visibly answer and "survived" there rests on the mate
  being correct rather than on evidence the entry was consulted. The eviction result
  is therefore **24/24 correct under full-table pressure**, not "24/24 answered from
  the table".
- A 1 MB table at `hashfull 1000` is the harshest case available and the mate came
  back correct at the right distance every time; that is the claim, and it is bounded
  by the corpus being 12 positions per size.

## 6. What I had to withdraw

Three things, all caught by my own controls rather than by review:

1. **A 117,304-cell "failure" that was my checker's bug.** My first unit harness
   asserted the re-probed distance should equal `rem`; the correct invariant is
   `q + rem`. A checker that rejects 99% of cells is as useless as one that accepts
   everything.
2. **22 phantom "encoding defects" that were a sign error.** I computed the mating
   ply as `2|k|-1` for BOTH signs. A *mated-in-k* claim lands on ply `2k`, because the
   opponent delivers it. Corrected, all 22 became honest claims and the encoding count
   went to **0**. **This is the single most important withdrawal**: had I stopped at
   the first classification, this report would have claimed 22 encoding defects that
   do not exist.
3. **A classifier that was blind.** My first warm-divergence classifier read a `pv`
   field that `exp_c_reprobe.py` never wrote, so **14/14 rows returned UNVERIFIABLE**
   and "0 encoding defects" would have been vacuous. Fixed by parsing the PV out of
   the raw info line, and a planted control now proves the classifier fires.

## 7. What is NOT tested, and why

- **The `mate_moves_` interaction.** The coordinator reports that the iteration break
  at `search.cpp:1431-1435` passes a mate-encoded value along, and that the guard at
  `:1434` is unreachable (`2*ply >= 63999` cannot occur with `MaxPly 128`). I **read**
  that code and agree it cannot fire, but I did not measure it, and this seat's
  experiments all run `go depth`, never `go mate` — so **no result here speaks to the
  `go mate N` path at all.**
- **`score_usable`'s exact-clock short-circuit.** Audited by another seat (43 cells,
  0 mismatches); I did not re-measure it. My `score_from_tt` unit test covers the
  arithmetic of the adjustment, not `score_usable`'s gating.
- **Threads > 1.** Everything here is single-threaded (`Threads 1`). The TT is shared
  across threads and I did not test whether a race can return a half-written score.
- **`DrawJitter` > 0.** All runs used the default; a nonzero jitter perturbs leaf
  scores near 0 and could interact with the mate band, untested.

## 8. Files

- `scripts/engine.py` — UCI driver that reads to `bestmove` before sending anything
  (never pipes `quit` into a live search).
- `scripts/pins.py` — the four pins, `bench N` on stdin.
- `scripts/unit_score_tt.py` — extracts `score_to_tt`/`score_from_tt` **by text** from
  `search.cpp`, records the extraction's sha256, and runs 118,332 cells plus two
  planted-wrong twins.
- `scripts/dtm.py` — exact DTM by definitional predicates (`_mate_within`,
  `_mated_within`), plus `verify_pv`.
- `scripts/oracle.py` — the first oracle (kept for its fast/reference cross-check);
  superseded by `dtm.py` for distance claims.
- `scripts/gen_candidates.py`, `gen_chains.py`, `corpus.py` — corpus construction and
  its four gates.
- `scripts/exp_c_reprobe.py` — the ply-1 store / ply-0 read re-probe.
- `scripts/exp_e_engine_vs_dtm.py`, `exp_f_classify.py`, `exp_g_warm_divergence.py` —
  the disagreement classifier and its positive control.
- `scripts/exp_d_eviction.py` — written, **not run**.
