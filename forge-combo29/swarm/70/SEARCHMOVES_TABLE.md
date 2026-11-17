# SEARCHMOVES_TABLE — which uses are sound, vacuous, or wrong

Engine `6b98f217`, all measurements at depth 12 unless the row says otherwise,
Threads 1, S14, fresh process per search. Every row names the file with the
evidence and the exact command that regenerates it.

## Verdicts

| # | use of `searchmoves` | verdict | the measurement | evidence |
|---|---|---|---|---|
| 1 | pin **the best move the search itself returned** and check the bestmove came back | **VACUOUS** | bestmove preserved **60/60**, but the score matched in **1/60** and `|delta| >= 10 cp` in **48/60**. The check cannot fail by construction: the only legal root move is the one you pinned. | `job2/pin_count.txt`, `python3 job2/pin_count.py` |
| 2 | pin the best move and read its **score** as the engine's score | **WRONG** | pinned score equals the in-tree score in **10/265** (move, position) pairs; **211/265** off by >= 10 cp, **50/265** by >= 50 cp; **sd 44 cp**; top move alone **1/53**. | `job1/pinned_vs_intree.txt`, `python3 job1/pinned_vs_intree.py` |
| 3 | pin **one** move and read its score as "what this move is worth" | **WRONG** | same measurement as row 2, single-move arm: the value produced is a different search's value, not the in-tree value. | `job1/pinned_vs_intree.txt` |
| 4 | pin **2 candidates** and compare | **SOUND ABOVE ~50 cp, WRONG BELOW** | pair agreement **47/53** (2 cand.); but **313/317 = 0.987** when they differ by >= 100 cp and **478/511 = 0.935** at >= 10 cp. Not sound as a blanket control. | `job3/rank_final.txt`, `job3/rank_why.txt` |
| 5 | pin **3 candidates** and rank them | **WRONG** | pairwise agreement **142/159** (95% CI 0.835–0.932); exact full ordering **40/53**. Interval excludes 1.0. | `job3/rank_final.txt`, `python3 job3/rank_final.py` |
| 6 | pin **5 candidates** and rank them | **WRONG** | pairwise agreement **486/530** (95% CI 0.890–0.938); exact full ordering **30/53**. | `job3/rank_final.txt` |
| 7 | pin each of the top 5 alone, then take the highest as "the engine's choice" | **WRONG** | the plain bestmove is the top-scoring candidate in only **49/60**; **11/60** positions have some other candidate above it. No reference involved. | `job3/verifier_operation.txt`, `python3 job3/verifier_operation.py` |
| 8 | `searchmoves <all legal moves>` as a **no-op control** | **WRONG — it is not a no-op** | 49/60 positions return the same bestmove, but only **1/60** return the same score. Cause isolated to one line (root TT store): restoring it gives **60/60** moves and **60/60** scores. | `job1/causal_split.txt`, `job1/order_vs_search.txt` |
| 9 | `searchmoves <all legal moves>` as a **tie-break probe** | **NEARLY SOUND, WEAK** | on positions with a **proven** mate-in-1 tie the bestmove changed **3/156** (vs 22/120 on ordinary positions), so it is a poor instrument for ties: it almost never re-picks within a proven tie, and where it changes the move it changed the score. | `job1/ties.txt`, `python3 job1/ties.py` |
| 10 | `searchmoves <all legal>` and use the **node count** to compare | **WRONG** | node totals differ on essentially every position (e.g. `26322` vs `11665`; `74730` vs `42753` in `job1/order_vs_search.txt`). The restriction changes the search. | `job1/order_vs_search.txt` |
| 11 | **empty** `searchmoves` (bare keyword) | **ERROR, correctly signalled** | `bestmove 0000`, `score cp 0`, `nodes 0`, plus `info string searchmoves restriction has no legal root moves`. Legal to rely on: the string is always present. | `job4/degenerate.txt` |
| 12 | `searchmoves` with **all moves illegal** | **ERROR, correctly signalled** | identical to row 11, same info string, 0 nodes. | `job4/degenerate.txt` |
| 13 | `searchmoves` with a **legal and an illegal** move together | **SILENTLY NARROWED — dangerous** | the illegal token is dropped with **no diagnostic at all**; the search is byte-identical to pinning the legal move alone (`g1h3` cp −40 n1359 on startpos). A mistyped corpus is silently a different experiment. | `job4/degenerate.txt` |
| 14 | `searchmoves` with a **fully-dropped** list (`0000`, wrong case, zero-length) | **ERROR, signalled — but indistinguishable from empty** | all three print the same restriction string and search 0 nodes; only the argument text says which you sent. | `job4/degenerate.txt` |
| 15 | `searchmoves` with **duplicate** legal moves | **SOUND** | identical to pinning once: `g1h3` cp −40 n1359, same as E5. | `job4/degenerate.txt` |
| 16 | rely on **argument order** of the move list | **SOUND** | legal+illegal and illegal+legal give identical bestmove, score and node count on both test positions. | `job4/degenerate.txt` (control C2) |
| 17 | treat **`bestmove 0000`** as an unconditional error | **WRONG** | checkmate roots also give `0000` (with `score mate 0`), stalemate roots give `0000` (with `score cp 0`), neither emits the restriction string. Only the presence of that string marks an error. | `job4/zero_move_meaning.txt` |
| 18 | separate the three `0000` cases from the **stream alone** | **SOUND** | checkmate → `score mate 0`; stalemate → `score cp 0`; restriction → info string. Measured on both a real mate and two real stalemates, each with perft-1 = 0 confirming the board. | `job4/zero_move_meaning.txt` |
| 19 | use **MultiPV 5** as the ground-truth ranking to validate a pinned corpus | **UNSOUND AS-IS** | MultiPV's rank-1 move differs from the plain search's bestmove in **7/60** (53/60 agree). Secondary lines run in a separate worker with its own hash. | `job3/rank_final.txt` |
| 20 | use **restricted MultiPV** over the same candidate set as the reference | **USABLE** | this is reference R3; it is itself a restriction, so it inherits the distortion, but its rank 1 comes from the main worker. Used in F6 alongside R1; both reject rank preservation. | `job3/rank_final.txt` |

## The three-line summary

- **Vacuous:** pin the winner, check the winner came back. True 60/60 by
  construction, says nothing.
- **Sound:** argument order; duplicate moves; two-candidate comparison when the
  gap is >= ~50–100 cp; reading the empty/all-illegal error; separating the three
  `0000` cases from the score kind plus the info string.
- **Wrong:** any absolute score from a pin; any ranking of 3 or more candidates;
  `<all legal>` as a no-op control or as a tie probe; MultiPV as ground truth;
  treating `0000` as always an error; trusting a mixed legal/illegal list.

## The fix, if the engine side wants one

One line. `src/search.cpp:2093` suppresses the root TT store under a restriction:

```2093:2093:forge-combo29/src/search.cpp
    if (excluded.is_none() && !(root_node && root_restricted_)) {
```

Removing `&& !(root_node && root_restricted_)` alone returns the restricted search
to the unrestricted answer on **60/60** positions and scores (**60/60**), with
`bench 13` unchanged at 862329 (`job1/causal_split.txt`). That would make
`searchmoves <all legal>` a true no-op control. It would **not** by itself make a
single pinned score equal the in-tree score, because the pinned search still has a
one-move root; the remaining divergence needs measuring after the change.
