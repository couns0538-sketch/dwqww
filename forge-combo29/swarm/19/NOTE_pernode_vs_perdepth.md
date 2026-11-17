# A per-node constant versus a depth-growing cost — the distinction that decides where to optimise

seat 19 · area 9 · one paragraph, for the owner, drawn from two of my measurements that happen to make a clean
contrast.

## The sentence

**`refresh_king_lines`'s redundancy is a per-node constant (96.8 % → 96.6 % of its calls waste work, unchanged
from 804 K to 2.83 M calls), whereas `probe_body`'s cost grows with depth (2.68 % at bench 13 → 8.47 % at bench
16).** So a fix to the king-lines waste buys the same fraction at every depth and can never become the dominant
cost, while a fix to the probe's per-probe work buys more the deeper the engine searches.

## Why that decides the order of attack

| | king-lines redundancy (19-C19, 29-F4) | transposition-table probe (19-F35) |
|---|---|---|
| shape | **per-node constant** | **depth-growing** |
| measured | 96.8 % at 2.8 M calls vs 96.6 % at 0.8 M calls | 2.68 % self at depth 13 → **8.47 %** at depth 16 |
| a fix is worth | the same share at every depth | **more** the deeper the search goes |
| and it is already known to be | ~0.056 % of instructions, so not worth doing | worth ~6 points of engine time, so worth understanding |

**Practical form for the owner:** at the depths his matches use, the transposition table is the larger prize and
it is the one that grows; the king-lines redundancy is real, provable and cheap to fix but permanently small.
Neither is urgent; this only says which to look at first if he looks at either.

## The caveat on the TT half

The 8.47 % is measured at **Hash 16** because `bench` hardcodes a 16 MB table (19-F37), and his GUI will use a
different size — so the *share* will differ even if the growth trend holds. The per-node half has no such
caveat: the ratio was unchanged across depths and marginally worse under PC20 (97.2 %).

## Addendum: the reproducibility result that backs my Threads-1 claim

`19-C26` replicated seat 24's 24-F31: **Threads 1 is bit-exact on 40 of 40 positions** (base tree, S14, Hash 16,
OwnBook false, depth 12, two fresh processes each) — identical in **move and node count**, zero differences of
either kind. That is **an independent harness confirming the property my own results rest on**, which is a
stronger position than my 19-F24 ("I never set Threads") alone: the regime is now verified rather than assumed,
by two seats with two harnesses.
