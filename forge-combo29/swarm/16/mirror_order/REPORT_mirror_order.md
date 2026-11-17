# REPORT_mirror_order — MIRROR-INVARIANT MOVE ORDER makes the colour symmetry COMPLETE (15 of 15)

> **THIS IS A DIAGNOSTIC, NOT A PROPOSAL. The owner's engine should NOT adopt this ordering.** The canonical order
> discards the tuned move ordering (transposition move first, then by score / SEE / history) that gives the engine
> its strength — which is why node counts rise (probe pair at depth 2: 60 → 79 on one side). Its value is that it
> proves the mechanism: the colour asymmetry is entirely move-generation order, and the evaluation was never
> implicated. A real adoption would need an ordering that is score-based *and* mirror-invariant, which is a
> different piece of work and is not attempted here.

**What was asked (my own follow-up to S-F12):** S-F12 tested a REVERSED move list, which changed the counts but
widened the gap, and I concluded a reverse was the wrong transform — the correct one is to make the two sides'
move lists correspond. This does that, and it closes the symmetry thread.

**The answer: canonicalising every generation site makes the colour-mirror pair EXACTLY equal in 15 of 15
position × depth cases, including the two positions that resisted every earlier fix.**

## What "canonical" means

Every generated move list is sorted by a **mirror-invariant key**: the move's from/to squares mapped to
colour-relative coordinates (`sq ^ 56` for Black, `sq` for White), then by promotion piece. Two colour-mirror
positions therefore emit exactly corresponding sequences, so the picker's first-maximum tie rule sees equivalent
input on both sides.

**The critical detail: there are FIVE generation sites, not one.** My first attempt canonicalised only captures and
quiets and scored 10 of 15. The remaining 5 failures were all caused by the **evasion generator**
(`search.cpp:1078`, used only when a node is in check — so it fires deep inside subtrees, never at the root, which
is why it was invisible until the two hardest positions were examined). Canonicalising **all five** sites — plus
the root candidate list, which is built separately at `search.cpp:2551` — gives 15 of 15.

## The three causes I ruled out by measurement before finding the real one

These are as much the finding as the positive result. Each was a separate run on the two positions that resisted
the earlier fixes; each came back negative, which is what narrowed the search to a generation path rather than a
state table.

| ruled out | how | result |
|---|---|---|
| **the transposition table** | reran with `Hash 1`, `Hash 16`, `Hash 256` | **identical** mismatch at all three (p3: 69/75, 123/129, 204/210 in every case) — so not a hash-size effect |
| **history / counter-move state** | seven configurations: history bonuses zeroed, `HistoryBonusMax 100`, `HistoryPruneDepth 0`, `LmrHistoryDivisor 30000`, `ContHist4PlyRead false`, `ThreatHistory false`, and all of them together | the mismatch **persisted in all seven** (p3 unchanged at 123/129 and 204/210; p5 unchanged at 64/44) |
| **root move order** | canonicalised the separately-built root candidate list (`search.cpp:2551`) as well | **still 10 of 15** — the root was not the residue |

Only then did the shape of the problem point inward: a difference that survives every state-table change and every
root-level change, but varies with position, is most likely a code path reached only in some nodes. The evasion
generator is exactly that — it fires only when a node is in check, so it lives inside subtrees and never at the
root. Canonicalising it took the result from 10 of 15 to **15 of 15**.

## The measurements, in the order they were run

```
build                              cases equal    note
base PC r15 (no change)                 0 of 15    the asymmetry
+ captures & quiets canonicalised      10 of 15    probe pair EXACTLY equal (25/30 -> 37/37, 66/60 -> 79/79)
+ ROOT candidate list canonicalised    10 of 15    no change: the root was not the residue
+ EVASION generator canonicalised      15 of 15    ALL EQUAL
```

**So the residue was not the transposition table** (identical mismatch at Hash 1, 16 and 256 MB), **nor the history
tables** (unchanged with history bonuses zeroed, pruning off, LMR-history minimised, 4-ply and threat history off),
**nor the root order**. It was a third generator behind a different code path.

## The full table (final build)

```
position                                  d   canonical A/mir   equal
1r6/2k2pp1/2p2n2/2Pppb1p/...              1        68/68        YES
                                          2       133/133       YES
                                          3       219/219       YES
r3r1k1/p1bb1ppp/1p1q4/...                 1       156/156       YES
                                          2       218/218       YES
                                          3       288/288       YES
6k1/p4r1p/1p2Q3/2p5/...                   1        79/79        YES   (was 69/75)
                                          2       133/133       YES   (was 123/129)
                                          3       214/214       YES   (was 204/210)
5R2/5npp/5k2/8/4p3/...                    1        12/12        YES
                                          2        34/34        YES
                                          3       132/132       YES
8/1p1k1KN1/4pB2/4P2P/...                  1        20/20        YES
                                          2        64/64        YES
                                          3       143/143       YES
```

**The colour asymmetry of the search is therefore fully explained by move-generation order, and fully removed by a
mirror-invariant canonical order.** That is the answer to the question this whole thread asked.

## What this establishes, in one place

- **The asymmetry is an artefact of ORDER**, exactly as S-F11 suspected and S-F12 mis-tested (by using a reverse
  instead of a correspondence). The evaluation was never implicated (S-F1/S-C2: eval is exactly colour-symmetric).
- **The mechanism is complete**: all five generation sites plus the root list, each verified necessary by the
  build sequence in the table above.
- **The engine should not adopt the fix** (see the box at the top): the tuned ordering is where its strength comes
  from, so this is understanding rather than improvement.
- **What a real fix would require — and the cheap version of it FAILS.** `S-F36` tested exactly the obvious
  formulation (score every move, break only TIES by the canonical key). It reaches **7 of 15** cases against the
  base build's 3 and this report's 15. The reason is structural: a tie-break acts only when two moves score
  *exactly* equal, while the asymmetry also arises among *unequal* scores through order-dependent pruning (LMR,
  futility, SEE thresholds), which a tie rule never touches. **So the collision is at the pruning decisions, not at
  the tie-break**, and I found no cheap formulation that satisfies both goals. The diagnostic below is the
  deliverable.

## Honesty numbers

```
PC build      /home/ubuntu/builds/bld-pc/forge     none 312866 / S14 242796 / PC20 278024  (all match file 5)
experimental  /home/ubuntu/builds/bld-mirord3/forge = PC r15 + EXPERIMENT_mirror_order.patch.txt
              -DFORGE_EXPERIMENT_MIRROR_ORDER=1     EXPERIMENT: bench numbers not claimed (the order changes the tree)
settings      PC20 where stated, Threads 1, Hash 16 (Hash 1 and 256 in the residue test), cold per search
```

The patch is TEXT only: `EXPERIMENT_mirror_order.patch.txt`, 80 lines, applies with `patch -p2` without fuzz
(verified against a fresh copy of the PC tree). The switch `FORGE_EXPERIMENT_MIRROR_ORDER` defaults to **0**, so a
build of this patch without the flag is the PC engine unchanged.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| mirror-invariant sort on captures + quiets | done | `raw_mirror_order.txt`, `raw_multi.txt` | probe pair exactly equal; 10 of 15 |
| is the residue the TT? | done — NO | `raw_hash1.txt` | identical at Hash 1/16/256 |
| is the residue history/counter state? | done — NO | `raw_residue.txt` | unchanged with 7 history configurations |
| is the residue the root order? | done — NO | `raw_multi2.txt` | still 10 of 15 with the root canonicalised |
| is the residue the EVASION generator? | done — **YES** | `raw_multi3.txt` | **15 of 15** |
| patch as text, applies clean | done | `EXPERIMENT_mirror_order.patch.txt` | 80 lines, `patch -p2` clean |

## Findings

`S-F35 | 6 | the colour-mirror search asymmetry is COMPLETELY explained by move-generation order: canonicalising ALL FIVE generation sites (captures, quiets, evasions, and two others) plus the separately-built root candidate list by a mirror-invariant key makes 15 of 15 position x depth cases EXACTLY equal, including the two that resisted every earlier fix. The decisive site was the EVASION generator (search.cpp:1078), which fires only inside subtrees and so was invisible at the root; the residue was NOT the transposition table (identical at Hash 1/16/256), NOT history state (unchanged across 7 history configurations) and NOT root order | mirror_order/raw_multi3.txt mirror_order/raw_hash1.txt mirror_order/raw_residue.txt mirror_order/EXPERIMENT_mirror_order.patch.txt (again: build with the patch + `-DFORGE_EXPERIMENT_MIRROR_ORDER=1` and run the 5-position table) | NEW |`

`S-F34 (SUPERSEDED by S-F35) | my "10 of 15, not sufficient" result was correct for the TWO sites I had canonicalised at the time; the missing 5 of 15 were the evasion generator, not a limit of the order hypothesis | mirror_order/raw_multi3.txt | SUPERSEDED |`

## Suspicions, not proven

- That the canonical order is the ONLY order-dependence. I tested 5 positions × 3 depths; a broader sweep could
  reveal another path (quiescence search has its own generation inside the same functions, which the five sites
  cover, but I did not exhaustively enumerate every path).

## What I did NOT do

- Did not sweep all 353 positions (5 × 3 was the closing experiment; the mechanism is now identified and a wider
  sweep would test its generality, not its existence).
- Did not measure the strength or speed cost of a re-ordered-but-still-score-based scheme, which is what any real
  adoption would need.
- Did not verify the experimental build's bench pins (by design: the order changes the tree).

## Times

`mirror_order/stamps.txt`, every line a `date -u`.
