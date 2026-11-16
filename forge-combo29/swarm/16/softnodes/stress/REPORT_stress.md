# REPORT_stress — is the softnodes overshoot bounded? (area: the PC's self-play path)

**What was asked (my own follow-up to S-F16):** S-F16 saw up to 2.061x overshoot at N=2000 on four positions.
Is that a bound worth telling the owner, or unbounded?

**The answer: ~2.06x SURVIVES as an empirical bound — my prediction that a quiet position would exceed it was
WRONG (P1 refuted) — and determinism and finished-depth held absolutely on all 16 runs.**

```
budget    n   overshoot range     max      determinism   finished-depth
  2000    8   1.022x .. 2.006x    2.006x   all 1 result  all 3/3
200000    8   1.028x .. 1.767x    1.767x   all 1 result  all 3/3
```

Across all 12 positions I have now measured at N=2000 (4 in S-F16 + these 8), **no position exceeds 2.061x**, and
the new maximum is 2.006x. Positions were chosen as the 8 G positions with the FEWEST legal captures, i.e. the
quietest available — the case where one depth step is most likely to be expensive relative to the budget, which
was exactly the mechanism P1 bet on. It did not happen: the search finishes the crossing depth, and the ladder
coarseness caps the overshoot just above 2x.

**The interesting new number is at the LARGE budget.** At N=200000 one position (`2R5/4P3/r7/5P1K/1k6/p1p5/6r1/R7 b`,
quiet7) overshoots to **1.767x** — 353,498 nodes against a 200,000 budget. That is a bigger absolute overshoot
than anything at N=2000 (up to ~2,100 extra nodes), and it means the overshoot is not "a few hundred nodes at a
small budget": a single depth step near a mate-ish position costs ~150k nodes. So the honest statement is a
bound of ~2.1x of the budget **in relative terms**, with no bound on the absolute number of nodes past N.

**P4 also refuted, in the other direction from what I expected:** I predicted the relative overshoot would be
smaller at large N. It is smaller on 7 of 8 positions (1.03–1.21x) but quiet7 is 1.767x at N=200000 against
1.109x at N=2000 on the same position — so the relative overshoot can be LARGER at a big budget when a step is
expensive.

**How sure:** high. 16 measurements, 3 reps each, every one deterministic (1 distinct result) and every one
ending on a completed depth.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16, fresh process + ucinewgame per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 8 quiet positions at N=2000 | done | `run.log`, `raw/stress.txt` | 1.022x–2.006x, none above 2.061x — P1 refuted |
| the same 8 at N=200000 | done | same | 1.028x–1.767x; one position at 1.767x is 353,498 nodes |
| determinism over 3 reps everywhere | done | same | 16/16 one distinct result |
| finished-depth everywhere | done | same | 16/16 complete |
| find a position exceeding 2.061x | NOT found | — | searched the quietest 8; no counterexample |
| absolute bound on nodes past N | NOT established | — | quiet7 shows it can be ~150k |

## Findings

`S-F17 | 6 | the softnodes overshoot is bounded in RELATIVE terms but not in absolute ones: across 12 positions at N=2000 no position exceeds 2.061x the budget (new max 2.006x), yet at N=200000 one quiet position overshoots to 1.767x = 353,498 nodes, because the crossing depth step itself costs ~150k nodes there — so "about 2x the budget" is the usable bound for the owner's self-play at N=2000, but the absolute number of nodes past N can be large at big budgets. Determinism (1 distinct result) and finished-depth held on all 16 runs | softnodes/stress/run.log (again: `python3 softnodes/stress/stress_softnodes.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That ~2.06x holds for N=2000 on ALL positions, not just 12. Twelve positions is not a proof, and I found no
  counterexample while deliberately hunting one.
- That quiet7's 1.767x is a mate-search effect (the position has passed pawns and rooks on the 7th). Not checked.

## What I did NOT do

- Did not search for a counterexample beyond the 8 quietest G positions (the most likely case, which is why I
  stopped there).
- Did not test the clock path, which is a different limit type and the PC's match path.

## What I am NOT sure about

- Whether the PC's self-play ever hits a position like quiet7 at a large budget, since self-play uses N=2000.

## Times

`softnodes/stress/stamps.txt`, every line a `date -u`.
