# kimi5 job 4 PREDICTION (Part 1) — written from the code only, before any measurement

Engine: commit 6b98f217 (forge-combo29), built-in net. Code read: src/search.cpp lines
1797 (best_score = -Infinite), 1991-1993 (candidate gate), 2011-2015 (reduced search),
2016-2024 (LmrDeeperShallower block), 2035-2037 (PV full-window search), 2043-2056
(best_score/alpha update). Value constants: include/forge/search.hpp:72-76
(Infinite = 32001, MateValue = 32000, MateInMaxPly = MateValue - MaxPly).

Candidate = a late-move-reduced move with score > alpha && reduced_depth < new_depth.
At every candidate the margin m = score - best_score is > 0. Proof: at entry
best_score = -Infinite <= alpha; the update block (2043-2056) keeps alpha >= best_score
after every searched move; a candidate has score > alpha, so m >= score - alpha > 0.
The switch then classifies by m, in CENTIPAWNS against new_depth in PLIES:
    do_shallower: m < new_depth          (a 1..~15 cp band)
    unchanged:    new_depth <= m <= 40 + 2 * new_depth
    do_deeper:    m > 40 + 2 * new_depth
do_deeper and do_shallower cannot both fire (40 + 2*nd > nd for nd >= 1).

## (a) Per 1,000 candidates, switch on — predicted shares, ranges outside which my reading is WRONG

Grounding: job 3 measured deeper 3.34 / shallower 0.67 per 1000 NODES at d12 and
3.78 / 0.61 at d16 (ratio ~5:1 and ~6:1). Candidates per 1000 nodes were never counted;
I estimate candidates ~8-20 per 1000 nodes, so the per-candidate shares below are wide.

| share of candidates | d12 range | d16 range |
|---|---|---|
| S3 (do_deeper, re-search one ply deeper) | [150, 500] | [150, 500] |
| S1 (do_shallower, re-search one ply shallower: m < nd AND reduced_depth < nd - 1) | [10, 150] | [10, 150] |
| S2 (do_shallower, re-search SKIPPED: m < nd AND reduced_depth == nd - 1) | [5, 120] | [5, 120] |
| unchanged (nd <= m <= 40 + 2*nd) | [300, 800] | [300, 800] |

S2 needs the clamped reduction r == 1 exactly (or new_depth == 2), so I expect S2 < S1
or comparable; shallower overall far below deeper (job 3's 5-6x). S3's share should not
fall with depth (its per-node rate grew 3.34 -> 3.78 from d12 to d16).

## (b) Tree factors vs switch OFF (200 positions, empty table, 1 thread) — predicted

Job 3 + Fable measured BOTH on: d12 = 0.895 [0.851, 0.944], d16 = 0.909 [0.851, 0.970].
My reading: the SAVING comes from shallower (S1+S2 remove one ply or the whole re-search);
deeper is a small TAX (adds one ply to ~4x more re-searches, and at PV nodes also to the
full-window search at line 2035, which uses the changed new_depth).

| column | d12 range | d16 range |
|---|---|---|
| shallower only (LmrDeeperBase 100000) | [0.82, 0.96] | [0.82, 0.96] |
| deeper only (LmrShallowerBase -100000) | [1.00, 1.09] | [1.00, 1.09] |

My sentence from job 3 ("shallower dominates the saved re-searches") is DEAD if
deeper-only comes out < 1.00 or shallower-only > 1.00, and WRONG-MECHANISM if the two
single columns multiply to something far from the both column (|product - both| > 0.05).

## (c) best_score at its starting value or a mate score when a candidate arrives

STARTING VALUE (-Infinite): cannot happen in this code. A candidate needs
move_count > 1 (+1 at root) (1991-1993). move_count is incremented only for legal,
non-excluded moves (1817, 1822-1823), and EVERY pre-search prune is gated on
best_score > -MateInMaxPly (1842 for the whole shallow-pruning block, 1918-1919 for the
wide-quiet-miss block), so the first counted move is always searched. search() never
returns -Infinite (its minimum is a mate-loss score > -Infinite = -32001), so after
move 1 best_score >= -MateInMaxPly. If it EVER were -Infinite: threshold
best_score + 40 + 2*nd = -31961+2*nd, so do_deeper would fire on essentially every
candidate (only a reduced score below ~-31931, a fast mate-loss, would not);
do_shallower (score < -32001 + nd) could never fire. No int overflow: values stay
within +/-32001 + 72.

MATE SCORE: can happen, and the block has NO is_mate_score guard (unlike the pruning
gate at 1842 and the singular-search guard at 1930). Two cases:
- best_score = +mate (an earlier move already mates): do_shallower fires for every
  later candidate whose reduced score is not an even faster mate
  (score < best_score + new_depth ~always true). Every later fail-high is then verified
  ONE PLY SHORT or NOT AT ALL; at a cut node the unverified reduced score stands and
  can cause the cutoff. Cost: cheap; correctness risk: an unverified mate claim
  propagates upward where the old code would have re-searched at full new_depth.
- best_score = -mate (all earlier moves get mated): threshold -Mate + 40 + 2*nd, so any
  candidate with an ordinary score fires do_deeper; the re-search runs one ply deeper.
  Harmless for correctness, small spend.
Where best_score gets its FIRST real value: lines 2043-2044
(`if (score > best_score) best_score = score;`) after the first move's search completes;
initialized at line 1797.

## Kill criteria
- (a) any measured share outside its range -> my candidate model is wrong.
- (b) deeper-only < 1.00 or shallower-only > 1.00 -> my mechanism is wrong.
- (c) a measured candidate with best_score == -Infinite -> my pruning-gate proof has a
  hole; a measured candidate with mate best_score CONFIRMS the unguarded case above.
