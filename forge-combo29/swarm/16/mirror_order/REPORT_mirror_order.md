# REPORT_mirror_order — does a MIRROR-ORDER permutation make the pair equal? (the last untested step)

**What was asked (my own follow-up to S-F12):** S-F12 tested a REVERSED move list, which changed the counts but
widened the gap, and I concluded a reverse was the wrong transform — the correct one is to force one side's list
into the other side's mirrored sequence. This does that.

**The answer: mirror-order correspondence is a MAJOR factor — it takes the probe pair from unequal to EXACTLY
equal at both depths, and 10 of 15 position×depth cases to exactly equal — but it is NOT sufficient (5 of 15 still
differ).**

## The probe pair (the S-F12/S-F8 position)

```
depth | BASE build (A / mirror) | MIRROR-ORDER build (A / mirror) | equal
    1 |        25 / 30           |            37 / 37              | YES
    2 |        66 / 60           |            79 / 79              | YES
```

Scores also match exactly under the mirror-order build (depth 1: cp 1161 / cp 1161; depth 2: cp 1190 / cp 1190),
and the result is deterministic (same position twice gives the same score). **P1, P2, P3, P4 all confirmed on
this position** — and P2 is the decisive one, because at depth 2 the full-window root had FAILED (336 vs 334).

## Across five positions × three depths

```
position                                     d    base      mirror-ord   equal
1r6/2k2pp1/...                                1    67/74      68/68       YES
                                              2   164/135    133/133      YES
                                              3   256/407    219/219      YES
r3r1k1/p1bb1ppp/...                           1   155/165    156/156      YES
                                              2   217/226    218/218      YES
                                              3   289/295    288/288      YES
6k1/p4r1p/1p2Q3/...                           1    87/75       69/75       no
                                              2   141/129     123/129      no
                                              3   219/209     204/210      no
5R2/5npp/5k2/...                              1    12/12       12/12       YES
                                              2    32/32       34/34       YES
                                              3   174/166     132/132      YES
8/1p1k1KN1/4pB2/...                           1    20/20       20/20       YES
                                              2    67/42       64/44       no
                                              3   140/107     146/124      no

MIRROR-ORDER equal: 10 of 15
```

**So the honest result is 10 of 15, not 15 of 15.** That is why I tested beyond the probe: the probe position
alone would have made this look like a complete explanation, which is exactly the trap my own STANDING CAUTION
warns about (habit 3, a single probe is not a property).

## The residue is NOT the transposition table

On the two positions that still differ, the mismatch is identical at Hash 1, 16 and 256 MB:

```
p3 d1: H1:69/75!  H16:69/75!  H256:69/75!
p3 d2: H1:123/129! H16:123/129! H256:123/129!
p5 d1: H1:20/20=  H16:20/20=  H256:20/20=
p5 d2: H1:64/44!  H16:64/44!  H256:64/44!
```

So the residual is not a hash-size effect. Nor is it explained by any single feature I checked: p3 has 25 legal
moves with 8 checks, p5 has 12 with 1 capture, while the now-equal p1 has 37 moves and p4 has 10. Whatever remains
is a second, smaller order- or state-dependence that my canonicalisation does not remove.

## A harness error I made and caught

My first p3 test used a mirror FEN I had typed by hand, and it was WRONG in three rows (I had the mirror in check
with 2 legal moves against the original's 25). The multi-position test computed mirrors with
`chess.Board(f).mirror()`, so its numbers were sound; I re-ran p3 with the correct mirror and the residue is the
same 6 nodes, so the finding does not depend on my error. But the error is worth recording: hand-typing a mirror
FEN is exactly the kind of transcription a script should do, and from now on mine do.

**How sure:** high on the 15-case table (cold, Threads 1, PC20, deterministic) and high that mirror-order is a
major factor. NOT sure what the residual is.

## Honesty numbers

```
PC build   /home/ubuntu/builds/bld-pc/forge    none 312866 / S14 242796 / PC20 278024  (all match file 5)
MIRROR-ORD /home/ubuntu/builds/bld-mirord/forge = PC r15 + a canonical, mirror-invariant move sort,
            -DFORGE_EXPERIMENT_MIRROR_ORDER=1   EXPERIMENT build: bench numbers not claimed
settings   PC20 + Threads 1 + Hash 16 (Hash also 1 and 256 in the residue test), cold per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| canonical mirror-invariant sort (switch, default 0) | done | `src` patch described above | builds; determinism verified |
| probe pair at depths 1 and 2 | done | `raw_mirror_order.txt` | 25/30 → **37/37**; 66/60 → **79/79** |
| 5 positions × 3 depths | done | `raw_multi.txt` | **10 of 15 equal** |
| is the residue the TT? | done — no | `raw_hash1.txt` | identical at Hash 1/16/256 |
| identify the residual mechanism | NOT done | — | no single position feature predicts it |

## Findings

`S-F34 | 6 | forcing a canonical, MIRROR-INVARIANT move order (sorting each generated list by the colour-relative from/to squares) makes the colour-mirror pair EXACTLY equal on the S-F12 probe — 25/30 → 37/37 at depth 1 and 66/60 → 79/79 at depth 2, with identical scores — and equal on 10 of 15 position×depth cases, so the generation order is a MAJOR cause of the asymmetry and the correct transform (a mirror-order permutation, not the reverse that S-F12 tested). It is NOT sufficient: 5 of 15 cases still differ, and that residue is independent of hash size (identical at 1/16/256 MB) | mirror_order/raw_mirror_order.txt mirror_order/raw_multi.txt mirror_order/raw_hash1.txt | NEW |`

`S-F12 (QUALIFIED) | my conclusion "order is necessary but not sufficient" stands, but the reason I gave was wrong: a REVERSE was the wrong transform, and the correct one (mirror-invariant canonicalisation) equalises the probe pair completely and 10 of 15 cases overall | mirror_order/raw_multi.txt | QUALIFIED |`

## Suspicions, not proven

- That the residual is a counter/history effect that survives canonical ordering because those tables are keyed by
  MOVE IDENTITY rather than position, so two mirror searches still accumulate differently. Untested.
- That p3's constant 6-node offset at every depth is a fixed-count artefact (e.g. one extra node per depth at the
  root) rather than a search difference. Its scores are also slightly apart (201 vs 200 at depth 1), so it is a
  real search difference, but the constant offset is suspicious.

## What I did NOT do

- Did not test more than 5 positions (this was a closing experiment, not a sweep).
- Did not isolate the residue (would need another instrumented build).
- Did not verify the mirror-order build's bench pins (by design: the sort changes the tree).

## Times

`mirror_order/stamps.txt`, every line a `date -u`.
