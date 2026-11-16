# THE LAST EXPERIMENT — keys, content, and a hypothesis of mine that the data FALSIFIED

Seat 06. Base tree, Threads 1, Hash 16. Instrumented builds: J (per-root-move node/qsearch counters),
I (picker scores), K (transposition and pawn keys). All pins checked where measured.

## The question asked

Print the transposition key and the stored entry for the one node that differs, on both sides, and say
whether the key differs or the stored content does.

## Answer, part 1: the keys differ — and that is EXPECTED, not the defect

`key_dump_root.txt`, root visit, both sides:

| move | key self | key mirror | equal |
|---|---|---|---|
| all 6 root moves | 18150232708356121761 | 3033376473120125418 | **False** |
| pawn keys | 18185490276865357752 | 16681261905262858283 | **False** |

A colour-mirrored position is a **genuinely different position**, so a different Zobrist key is correct
behaviour, not a bug: `compute_key()` XORs `Z.piece[piece][square]` over **absolute** squares plus
`Z.side` for Black (`src/board.cpp:1407-1417`). Absolute-square Zobrist hashing cannot give a mirror pair
the same key and is not supposed to. **So outcome 1 of the two the brief named does not apply: there is no
hashing or zobrist defect here.**

## Answer, part 2: the stored *content* is not colour-dependent either

`node_picker_scores.txt`, the qsearch-child node, all 22 moves on both sides:

| | result |
|---|---|
| moves whose picker score differs | **0 of 22** |
| scores, self | 20 moves at 0, `b8b7` and `b8f8` at **12000** |
| scores, mirror | 20 moves at 0, `b8b7` and `b8f8` at **12000** |

The engine's **opinion of every move is identical** on both sides. Nothing colour-dependent is stored.
**Outcome 2 does not apply in the form the brief supposed either** — the content agrees.

## What IS different: the tie structure, and the order it collapses to

At that node **20 of 22 moves are tied at 0 and 2 are tied at 12000**. `std::sort`'s comparator
`a.score > b.score` is false for every equal pair, so a 20-way tie is resolved by whatever order the
moves arrived in — and that order is the generator's emission order, which differs under a colour mirror
(established earlier: `order_tt_chain.txt`, `rootmove_trace.txt`).

## The part I got wrong, stated plainly

I formed the hypothesis "the asymmetry is **purely** ordering, so the resulting SCORE must be identical at
every depth even though node counts differ" and I tested it. **It is falsified** (`final_verification.txt`):

| depth | score self | score mirror | scores equal | nodes self | nodes mirror |
|---|---|---|---|---|---|
| 1 | cp 1978 | cp 1978 | **yes** | 34 | 45 |
| 2 | cp 2038 | cp 2038 | **yes** | 77 | 88 |
| 3 | cp 1852 | cp 1852 | **yes** | 185 | 151 |
| 4 | cp 1952 | cp 1926 | **no** | 379 | 307 |
| 5 | cp 1844 | cp 1917 | **no** | 798 | 642 |
| 6 | cp 1861 | cp 2062 | **no** | 1220 | 1953 |

So ordering explains **depths 1–3** cleanly (identical scores, different node counts) and stops explaining
the behaviour at **depth 4 and beyond**, where the scores themselves diverge. Ordering is therefore the
**trigger**, not the whole cause: at depth ≥ 4 a different order leads to different *evaluations being
reached*, which is a second effect layered on top.

## What that means, honestly

The brief offered two final outcomes. **Neither is what the data shows**, and I am not going to force the
result into either:

- Keys differ — but that is correct for absolute-square Zobrist, so no hashing defect.
- Content is identical at the level measured — so nothing colour-dependent is stored in the picker scores.
- The real mechanism is **tied scores collapsing to a mirror-varying emission order**, which fully explains
  depths 1–3 and only partly explains depth ≥ 4.

**This needs another step, and I am saying so plainly rather than closing the thread on a tidy story.** The
next experiment is named and small: at depth 4, dump the same picker-score vectors for the nodes where the
*scores* first diverge, and check whether the scores differ there because a *different set of nodes was
visited* (ordering, still) or because the *same* node is scored differently (a genuine evaluation or
stored-content asymmetry). That single distinction decides whether the thread ends as "ordering, all the
way down" or as "ordering triggers a second, deeper asymmetry".

## Raw output

`key_dump_root.txt`, `node_picker_scores.txt`, `tie_analysis.txt`, `final_verification.txt`,
`rootmove_trace.txt`, `e6f7_tt_test.txt`, `node_equivalence.txt`, `tt_isolation.txt`.
