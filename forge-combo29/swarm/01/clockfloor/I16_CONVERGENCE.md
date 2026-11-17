# i=16: PC20 did not verify more — it converged later, and my verdict was wrong twice (S-C48)

The coordinator asked whether i=16's 18.4× work was **verification** (PC20 examined a defence S14 never saw) or **waste**
(same line, more siblings). The answer is neither, and finding that out overturned my own conclusion twice.

## What the traces actually show

`5k2/2Q5/p3Kn2/P7/N4r2/5P1R/RP2P3/8 b - - 4 67`, `go depth 12`, every depth's PV captured.

| depth | S14 score | S14 nodes | PC20 score | PC20 nodes | S14 seldepth | PC20 seldepth |
|---|---|---|---|---|---|---|
| 7 | cp −3089 | 5,868 | cp −3148 | 4,916 | **25** | 17 |
| 8 | cp −3446 | 9,677 | cp −3111 | 8,596 | **25** | 21 |
| **9** | **mate −4** | **11,613** | cp −3363 | 22,938 | **25** | 26 |
| 10 | mate −4 | 12,035 | cp −3518 | 50,649 | **25** | 34 |
| 11 | mate −4 | 12,394 | cp −3431 | 54,767 | **25** | 34 |
| 12 | mate −3 | 12,957 | mate −3 | **238,009** | **25** | **51** |

**S14 found the mate at depth 9 (11,613 nodes). PC20 did not find it until depth 12 — 238,009 nodes.** Through depths
9, 10 and 11 PC20 was still returning ordinary evaluations (`cp −3363`, `cp −3518`, `cp −3431`) while S14 had already
proved `mate −4`.

And the seldepth column explains why: **S14's seldepth saturates at 25 from depth 7 onward, while PC20's climbs
17 → 21 → 26 → 34 → 51.** PC20 is still deepening its quiescence search every iteration; S14 stopped extending. That is
what the 18.4× buys: not a different conclusion and not a new defence, but **a much longer tail of captures and checks
in every iteration, which delays convergence to the mate it eventually reports.**

## Three verdicts, two of them wrong

| attempt | basis | verdict | why it was wrong |
|---|---|---|---|
| 1 | depth, seldepth, nodes | "DEFECT candidate" | ignored the score, so "same depth" hid a different claim |
| 2 | PV divergence at depth 4 | "**VERIFICATION** — examined resources outside S14's tree" | PV divergence means *has not converged yet*, not *found a new defence*; I read a snapshot of an unsettled search as a difference in knowledge |
| 3 | score by depth, seldepth growth | **later convergence** | — |

Attempt 2 is the instructive failure. The rule I applied — "different PV ⇒ new resource examined" — is a valid
inference about **finished** searches and an invalid one about **iterations of the same search**. PC20's depth-4 PV was
not a better answer; it was an answer from a shallower place, because at depth 4 PC20's seldepth was the same 9 but its
ordering differed. I compared two mid-flight snapshots and drew a conclusion about what each had *learned*.

## What this does to the `S-C46`/`S-C47` conclusion

Nothing that matters, and one thing that sharpens it. The coordinator's synthesis settles the framing:

* **the node ratio is bimodal** (median 0.926, mean 1.214, tail to 18.4×) — that is where the five outliers live;
* **per-node cost is uniformly ~1.07×** — seat 19's n=180 quartiles 1.044/1.071/1.110, 162/180 above 1.0, and the
  correlation between the two quantities is r = 0.044.

So i=16 is **an anomaly in the node ratio, not in per-node cost** — exactly as the coordinator said. PC20 does more work
per node nearly everywhere (a small uniform tax), and *wildly* more nodes on a few positions (the bimodal tail). i=16 is
the extreme of the second effect, and the mechanism is a quiescence search that keeps extending where S14's stopped.

**The correct description of i=16 is therefore: PC20 spends 18.4× the nodes because its quiescence search extends
deeper in every iteration, and that delays — rather than improves — the mate it eventually finds.** It is a real cost
with a real mechanism, not waste in the sense of "the same search done badly", and not verification in the sense of
"checked more defences".

## The `S-C47` claim that has to be narrowed

`S-C47` said i=16 was "more verification of the same answer". **That is withdrawn.** The traces show PC20 reached the
same *mate score* only at depth 12, having reported ordinary evaluations for three iterations where S14 already had a
mate. Same final score, later arrival, much more work — and its seldepth is the reason.

The other four positions in `S-C47` are untouched: three found a mate **shorter** (`mate 6→4`, `5→4`, `5→4`), which is
a stronger claim on its own score evidence, and i=99's seldepth rise is a separate case I have not re-examined under
this new lens and should.

## The workload warning, which affects my gate

The coordinator also reported that **bench node ratios flip sign across benches** (11: +14.5 %, 13: −10.6 %, 16:
+8.7 %) while real positions sit at −9.1 %. **A node-count claim is meaningless without the workload that produced it.**
My `check_depth_claims.py` verifies per-depth node counts against a trace, so it is scoped to its artifact — but the
`S-C46` prose says "PC20 saves 7.4 % of nodes" about `depth 12` on `R_1911.fens` positions, and a reader could carry
that to a bench. Every such statement needs its workload attached, and the rule page should say so.
