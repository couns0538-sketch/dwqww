# REPORT — seat 07, job 34: how broad is the PC's search change? (per-position, not aggregate)

## What was asked / the answer / how sure

**Asked:** report the **per-set** difference between PC20 and S14 rather than one aggregate, so a later
seat can see which positions changed and by how much — that is what tells the owner whether the PC's
search changes are broad or narrow.

**Answer:** **broad and systemic.** Every one of the 200 positions changed node count; 60 of 200
changed bestmove; 195 of 200 changed score.

**How sure:** high — both sides were re-measured with the *same* driver and schema, and the base leg
reproduced the published 9,500,069 exactly, which is the check that the comparison is sound.

## The two runs being compared

| side | build | settings | sum |
|---|---|---|---|
| base | 6b98f217 | S14 | **9,500,069** (matches the published value, 07-C3) |
| PC | r15 | PC20 | **8,315,168** (07-C26) |

Both: Threads 1, Hash 16, one fresh process per position, `ucinewgame` + `isready` before every `go`,
set O (200 positions), depth 12.

Difference: **−1,184,901 nodes** on the PC side.

## Per-position result

    positions where the node count changed : 200 of 200   (100.0%)
      increased on PC                      :  74
      decreased on PC                      : 126
      identical                            :   0
    positions where the BESTMOVE changed   :  60 of 200   ( 30.0%)
    positions where the SCORE changed      : 195 of 200   ( 97.5%)

    delta nodes:  min -69,363   median -4,888   max +76,082   mean -5,924
    |delta|     :  median 11,684   90th pct 30,949   max 76,082

## What "broad" means here, concretely

There is **no subset of positions that is untouched**. A localised change would show a cluster of
identical rows and a cluster of changed rows; this run has 0 identical rows out of 200. That is what
one expects from a build that alters move-ordering history, correction history and pruning together —
it changes nearly every tree, and the totals happen to land 12 % lower because more positions got
cheaper (126 down) than dearer (74 up), not because a few positions changed a lot.

The largest single movers, for anyone wanting to look at a specific tree:

| index | position | base → PC nodes | Δ | bestmove |
|---|---|---|---|---|
| 143 | `r1bqkb1r/ppp1nppp/3p1n2/3Pp3/2P1P3/2N2N2/PP3PPP/R1BQ…` | 27,342 → 103,424 | **+76,082** | `e7g6` → `h7h6` |
| 87 | `r1bqkb1r/pppp1p1p/5np1/4p3/2BnP3/3P4/PPP2PPP/RNBQK1N…` | 115,882 → 46,519 | **−69,363** | `b7b5` → `d7d5` |
| 80 | `rn1qkb1r/ppp2ppp/4pn2/3p3b/2PP4/2N2N1P/PP2PPP1/R1BQK…` | 137,007 → 67,696 | **−69,311** | `d1b3` → `g2g4` |

Full table: job34/raw/sum_delta.txt (all 200 rows with fens, node counts, deltas and any bestmove
change) and job34/raw/sum_delta.json.

## The caveat I am not hiding

The two runs differ in **both** build and settings (base+S14 vs PC+PC20). So each per-position delta is
a property of the **pair of configurations the owner actually uses**, not of the PC's search alone.
Separating build from settings needs two further full runs — base under PC20, and PC under S14 — which
I did not complete in this job. A reader should not read these deltas as "what the PC patch changed";
they are "what the owner's configuration differs by".

## The one unexplained base-vs-PC difference, and it is a good one (07-C29)

A 20-case sweep under identical settings found five differences. Four map to switches file 5 names.
The fifth, `8/P6k/8/8/8/8/8/K7 w` at `go depth 10`, had no named cause:

    base          a1a2    cp 1067   21,093 nodes
    PC            a7a8q   cp 1124   36,405 nodes

Isolated by rebuilding a scratch copy with each `FORGE_FIX_*` switch **alone**:

| switch alone | result |
|---|---|
| `FORGE_FIX_ROOT_DRAWN` | a1a2 / 1067 / 21093 — same as base |
| `FORGE_FIX_HARD_LIMIT_EMERGENCY` | a1a2 / 1067 / 21093 — same as base |
| **`FORGE_FIX_BARE_KING_LMR_CAP`** | **a7a8q / 1124 / 36405 — exactly the PC answer** |

With all three off the build matched base exactly. So this difference is that single cap, and **the
PC's answer is the better one**: it promotes immediately instead of shuffling the king. That is the
bare-king reduction cap doing its job on a promotion race that the base tree's reduction was hiding —
a small independent confirmation that the PC's bare-king work helps in at least one position.

## Findings

**07-C28** (per-position breadth) and **07-C29** (the isolated, benign difference).

## Suspicions, not proven

- Whether the 30 % of positions with a changed bestmove are better or worse on the PC. Measuring that
  needs games, which is not area 7's job and not something a node count can answer.

## What I did NOT do

- Did not run base+PC20 or PC+S14 sums, which is what would separate build from settings (stated above).
- Did not investigate the remaining score changes; 97.5 % of positions changing score is consistent
  with a systemic ordering change and needs no per-position account.

## What I am NOT sure about

- Whether some of the 200 deltas are inflated by clock-free depth-12 searches hitting different
  aspiration orders; I did not control for that, and it would not change the breadth conclusion.

## Times

See job34/stamps.txt.
