# kimi5 job 5, Part 1 prediction (from the code only, before any measurement)

Tree: 6b98f217 (my work branch tip carries it unchanged; `git diff 6b98f217 HEAD -- src include` is empty).
Read: search.cpp 1831-1915 (the block), 1866/1869/1880/1885/1893/1903 (s1..s6), 1837-1840 (the three cases),
1802 (has_material), 1673-1677 (bare_king_mode), 1991-2014 (the LMR reduced search the probe mirrors).

## (a) tree factor of each arm ALONE against none, depth 12

On O the job file's own K table pins the sums, so these are not predictions but checks: PV 12,399,593/12,573,318
= 0.9862, in-check 12,326,599/12,573,318 = 0.9804, mate 12,573,482/12,573,318 = 1.00001. My reading is wrong
if K3/K4/K5 do not reproduce to the node.

On G (353 whole-game positions) I transfer Fable's 400-position whole-game rows (PV 1.094 [1.028,1.163],
in-check 0.999 [0.943,1.046], mate 1.110 [1.005,1.244], depth 12) to my tree, widened for the smaller set:
- PV arm:        point 1.07, wrong outside [1.00, 1.20]
- in-check arm:  point 1.00, wrong outside [0.94, 1.10]
- mate arm:      point 1.10, wrong outside [0.98, 1.30]

## (b) which step carries most of the extra nodes on G

- PV arm: s1 (late-move pruning, 1866). It has the highest raw drop count of the six (it fires at nearly
  every node once move_count passes the lmp threshold, PV nodes included), and every s1-dropped quiet is one
  the arm now searches. Wrong if s1 is not the largest single contributor to the PV arm's extra nodes.
- mate-score arm: s1 again, by elimination from Fable's own two numbers: the PC guard that skips ONLY s2+s5
  at mate alpha costs 3 % of the tree where the whole arm costs ~11 %, so s1+s3+s4+s6 carry ~8 of the 11
  points; in bare won endings most legal moves are quiet and the mate alphas live at shallow remaining
  depth, where the lmp threshold is small, so s1 fires most of the four. Chief rival: s2. Wrong if s1 is not
  the largest single contributor among the six.

## (c) regret rates (probe: the dropped move searched at (alpha, alpha+1) at its post-reduction depth)

Per 1,000 drops, depth 12, all steps together:
- ordinary:   15-60
- PV node:    10-80   (0.7-1.6x ordinary; PV ordering is the best, so not higher)
- in check:   30-150  (1.5-4x ordinary; every legal move is an evasion, and s2/s5 cannot fire in check, so
                       the drops come from s1/s3/s4/s6 on moves that all matter)
- mate alpha: 60-300  (2.5-6x ordinary; s2's and s5's margins are alpha-relative, so against a mate alpha
                       they are vacuously true and prune near-every candidate, good ones included)
Worst cell: (mate alpha, s2). Wrong if a case lands outside its range, or the worst cell is not
(mate alpha, s2) or (mate alpha, s5).

## (d) why the mate arm changes so few searches and then multiplies a bare won ending

A mate-scored alpha needs an ancestor where a sibling line already returned a mate score; that is rare
(Fable: 14/22 of 400 searches changed at d12/d16). Once it happens in a bare won ending (KQ-K, KQR-K), the
mate score backs up along the whole conversion line, so alpha stays mate-scored for many consecutive plies.
At those nodes the block fires at nearly every strong-side node, because the guards at 1841-1842 do not stop
it there: `has_material` (1802, 1842) exempts only the side to move with no non-pawn material, i.e. the bare
DEFENDER's nodes, not the attacker's; `best_score > -MateInMaxPly` (1842) holds while converting;
`mate_moves_ == 0` and `halfmove_clock() + depth < 100` (1841) hold in these endings; `!root_node` (1841)
holds below the root; `bare_king_mode` (1842, defined 1673-1677) needs FORGE_BARE_KING_MATE_FIX AND more
than one worker, so it is false at Threads 1 and never rescues these nodes. Inside the block, s2 (1869-1873:
`ss->static_eval + FutilityBase + FutilityMultiplier * lmr_depth <= alpha`) and s5 (1893-1898: same shape
plus capture value and history/8) compare a FINITE eval against a mate-sized alpha, so the test is true for
every candidate at lmr_depth within the limit; they prune good moves together with bad ones, and the arm
searches them all. Few searches contain such subtrees; the ones that do pay several times over (Fable:
3.6-3.9x in KQ-K/KQR-K). File/line for every condition that matters: 1802, 1841, 1842, 1869-1873,
1893-1898, 1673-1677.
