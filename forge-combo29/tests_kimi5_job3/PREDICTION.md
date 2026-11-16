# kimi5 job 3 — PREDICTION (committed before any measuring command; never edited after)

Source read at commit 6b98f217 (work branch tip). All `search.cpp` lines are that file's lines.
"Tree factor" = nodes to finish `go depth D` with the switch ON / with it OFF, empty table per search
(`ucinewgame`+`isready` before every search), Threads 1, Hash 16, first 200 UHO lines. "Fire share" =
the counter-defined share of all search nodes (or, where marked "per search", of the 200 searches).
Every number has its kill range: outside it my reading of that switch is dead.

## The eight rows

### 1. LmrDeeperShallower
- Acts at: search.cpp:2017-2021 (deeper/shallower decision), 2022 (re-search skip). Option read at uci.cpp:409.
- Nodes: any node inside the LMR block (depth>=2, move_count>1(+1 at root), not bare-king, quiet-or-late)
  whose reduced search beat alpha ("full_depth_needed"), all node types, in check or not.
- Does: re-orders depth — new_depth += 1 (deeper) or -1 (shallower) before the LMR verification re-search;
  if the adjusted new_depth <= reduced_depth, the full re-search is SKIPPED (2022).
- Constants: deeper if score > best_score + 40 + 2*new_depth (scales with depth); shallower if
  score < best_score + new_depth (scales with depth). The +/-1 itself does not scale.
- TREE FACTOR d8 0.98 [0.90,1.06] | d12 0.98 [0.88,1.08] | d16 0.99 [0.88,1.10]. The shallower arm skips
  whole re-searches; the deeper arm adds plies; near-cancel by construction.
- FIRE SHARE d8 1.0% | d12 1.5% | d16 2.0% of nodes (kill [0.2%, 8%]). Counter: lmrds_deeper+lmrds_shallower.
- Turn: roughly depth-neutral; if anything, the deeper arm's cost grows at d16+ (added plies are deeper),
  so a small node increase there.

### 2. ThreatHistory
- Acts at: search.cpp:1345-1349 (read in ordering history), 1351-1355 (update), call sites 1330 (picker
  quiet score via quiet_history), 1386/1392 (cutoff updates), 2084 (PV-quiet update). Bucket index:
  quiet_threat_index 290-320 (pawn -> 0; else cheaper-attacker test on the destination). uci.cpp:410.
- Nodes: every quiet move at every node that scores or updates quiet history — all node types, any depth;
  through `history` at 1829 it also moves LMR r (2002) and history pruning (1880).
- Does: re-orders quiets (a second history keyed by threat bucket) and shifts their LMR reduction by
  clamp(history/LmrHistoryDivisor,-2,2) with LmrHistoryDivisor=6000.
- Constants: none of its own; bonus = history_bonus(depth) (quadratic 20, linear 48, max 2048 — scales
  with depth). Table cleared by ucinewgame (Worker::clear, 1022).
- TREE FACTOR d8 0.99 [0.93,1.05] | d12 0.99 [0.92,1.06] | d16 0.99 [0.92,1.08]. Ordering-only; a young
  table on a fresh game adds noise before signal, so near 1 at fixed depth with empty histories each search.
- FIRE SHARE (nodes with >=1 quiet carrying a nonzero threat bonus) d8 25% | d12 40% | d16 50%
  (kill [8%, 80%]). Rises with depth as the table fills within one search.
- Turn: ordering gains persist with depth; slight decay only because deeper searches already order well.

### 3. NullThreatVerify
- Acts at: search.cpp:1695 (null allowed only if !null_blocked_), 1723-1741 (threat gate + verification
  search), helper cheaper_enemy_attacks_dearer 155-175 (any cheaper enemy attacker on our N/B/R/Q).
- Nodes: cut nodes at remaining depth < 14 with eval >= beta where the null search just beat beta AND a
  cheaper enemy piece attacks a dearer piece of the side to move. At depth >= 14 nothing changes
  (verification existed already, 1719).
- Does: replaces a trusted null cutoff by a verification search at depth-reduction with null moves
  disabled below (null_blocked_ set 1731, restored 1735 BEFORE the abort check 1738).
- Constants: depth<14 gate (scales with remaining depth — covers every node below the first two plies of
  a depth-16 search); verification depth = depth - reduction (scales).
- TREE FACTOR d8 1.02 [0.98,1.08] | d12 1.03 [0.98,1.10] | d16 1.04 [0.98,1.12]. Pure added searches.
- FIRE SHARE (threat-gated verifications / nodes) d8 0.3% | d12 0.4% | d16 0.5% (kill [0.05%, 2%]).
- Turn: cost share roughly depth-stable; the benefit (catching a wrong cutoff) matters most at shallow
  remaining depth, so the GAIN should shrink with depth.

### 4. NullSeeVeto
- Acts at: search.cpp:1699 (veto in the null-prune condition), helper null_see_veto_threat 1174-1196
  (after a null, any enemy capture with attacker < victim by SeePieceValue — king priced 100000 — that is
  legal and SEE >= 0). uci.cpp:413.
- Nodes: nodes that reach the null-prune test (depth >= NullMoveMinDepth=3, eval >= beta, static_eval >=
  beta-24*depth+180, non-pawn material, not a failing TT upper bound) — cut nodes, not in check.
- Does: skips the null move itself (no null search, no cutoff) — the node is searched in full.
- Constants: none numeric; the veto scan runs per candidate node.
- TREE FACTOR d8 1.01 [0.97,1.08] | d12 1.02 [0.97,1.09] | d16 1.03 [0.97,1.10]: vetoed nodes lose a
  cheap cutoff and pay a full search.
- FIRE SHARE (vetoes / nodes) d8 0.5% | d12 0.7% | d16 0.8% (kill [0.1%, 3%]).
- Turn: same shape as NullThreatVerify — cost stable-to-up, benefit front-loaded; gain shrinks with depth.

### 5. ContHist4PlyRead
- Acts at: search.cpp:1337-1338 (quiet_history adds (ss-4)->continuation/2), 1327-1328 (quiet_history_sum
  passes the cont4 table), 791-792 (picker constructor's cont4 pointer). Writes to the 4-back table happen
  UNCONDITIONALLY in update_continuation 1363-1367 (backs {1,2,4}); the option gates only the READ.
- Nodes: quiet moves scored at ply >= 5 where the stack entry 4 back holds a real move — i.e. most of the
  tree below the fourth ply, all node types, in check or not.
- Does: re-orders quiets (ordering) and, via quiet_history at 1829, shifts LMR r (2002) and history
  pruning (1880) by the same clamp as ThreatHistory.
- Constants: weight 1/2 (1338) — does NOT scale with depth.
- TREE FACTOR d8 0.99 [0.94,1.05] | d12 1.00 [0.94,1.06] | d16 1.00 [0.93,1.07]. One more ordering term;
  near-neutral on node count.
- FIRE SHARE (nodes whose quiet scoring included the cont4 term) d8 50% | d12 60% | d16 65%
  (kill [20%, 90%]).
- Turn: persists with depth; no mechanism for a turn.

### 6. AspCappedReopen
- Acts at: search.cpp:2419-2421 (fail low), 2427-2429 (fail high), helpers capped_fail_low/high
  2131-2139 (margin 13; mate or |score| >= 640 opens fully), delta growth 2435 (delta += delta/2 + 4,
  both modes). uci.cpp:430.
- Nodes: ROOT only, on aspiration windows that fail (narrow window from depth 4, 2405-2409). Every
  re-search is a full-depth root search with the new window.
- Does: widens the failed side to only 13 past the returned bound instead of score-delta. NOTE (read,
  not measured): the `break` at 2421/2429 is dead — iteration_score <= iteration_score-13 is never true —
  so the loop ALWAYS re-searches after a cap; a far-moved score is walked back in ~13+delta-growth steps,
  each step a full-depth narrow re-search.
- Constants: AspReopenMargin 13, AspDecisiveScore 640, AspirationDelta 18 — none scale with depth; the
  COST of each loop step scales with depth (a full root search).
- TREE FACTOR d8 0.99 [0.92,1.08] | d12 1.01 [0.92,1.10] | d16 1.04 [0.92,1.14]: cheap or slightly saving
  at shallow depth, more cap-loop steps at depth as scores swing wider.
- FIRE SHARE (searches of the 200 with >=1 capped reopen) d8 20% | d12 30% | d16 40% (kill [5%, 70%]);
  per-node share < 0.5% at every depth.
- Turn: THE clearest turn-with-depth mechanism of the eight (loop count x full-depth step cost).

### 7. HindsightDepth
- Acts at: search.cpp:2012/2014 (parent hands withheld_plies = new_depth-reduced_depth to the child),
  1611-1635 (child adjusts depth), 1582 (reset), 2340 (stack init). uci.cpp:390.
- Nodes: non-PV, non-root, not-in-check, unexcluded children of LMR-reduced moves (withheld > 0) whose
  parent has a static eval.
- Does: re-searches the child one ply SHALLOWER if the mover's static eval fell by >= SeePieceValue[Pawn]
  (mover_loss = parent_eval + child corrected eval), one ply DEEPER if it did not fall and >= 3 plies were
  withheld; a TT entry at least that deep vetoes the change (1626); depth <= 0 falls to qsearch (1630).
  The raw eval computed for the decision is reused (1609, 1654) so no double evaluation.
- Constants: pawn threshold (SeePieceValue[Pawn]) and withheld>=3 — neither scales with depth.
- TREE FACTOR d8 1.00 [0.94,1.08] | d12 1.01 [0.94,1.09] | d16 1.01 [0.94,1.10]: the two arms partly
  cancel; small net growth.
- FIRE SHARE (nodes whose depth actually changed / all nodes) d8 0.8% | d12 1.2% | d16 1.5%
  (kill [0.2%, 5%]). Counter: hd_minus+hd_plus.
- Turn: one adjusted ply is a bigger fraction of a shallow subtree, so the effect (both ways) is largest
  at d8 and dilutes with depth — the OPPOSITE turn of AspCappedReopen.

### 8. SoundMatePruning
- Acts at: search.cpp:1837-1841 (sound_mate_case), arms sound_arm_enabled search.hpp:319-328
  (FollowOption -> the option), skip targets: the whole shallow-pruning block 1866-1906 (LMP 1866,
  futility 1869-1879, history prune 1880-1884, quiet SEE prune 1885-1889, capture futility 1893-1906).
  Option handler uci.cpp:439-446 (toggle clears the searcher).
- Nodes: non-root move loops with mate_moves_==0, halfmove+depth<100, best_score > -MateInMaxPly, with
  material: the block is SKIPPED at PV nodes, in-check nodes, and when alpha is already a mate score.
- Does: un-prunes — moves the block would have dropped are searched.
- Constants: none new; the prunings it skips carry FutilityDepth 7, FutilityBase 100, FutilityMultiplier
  110, LmpBase 4, HistoryPruneDepth 3, HistoryPruneMultiplier 2048, SeeQuietMultiplier 24,
  CaptureFutilityBase 0 (capture futility OFF at default), CaptureFutilityMultiplier 250,
  CaptureFutilityDepth 6 — all depth-scaled via lmr_depth.
- TREE FACTOR d8 1.01 [0.97,1.06] | d12 1.01 [0.97,1.07] | d16 1.02 [0.97,1.08]: PV+check nodes are a
  small share, so a small growth.
- FIRE SHARE (nodes skipping the block due to an arm) d8 4% | d12 3.2% | d16 2.6% (kill [0.8%, 10%]):
  the PV fraction of the tree falls with depth.
- Turn: cost grows with the size of the un-pruned subtrees — mildly up with depth.

### The six-bundle
- TREE FACTOR d8 1.01 [0.93,1.10] | d12 1.02 [0.93,1.12] | d16 1.04 [0.93,1.14]: the growth switches
  (3,4,6) outweigh the saving ones (1,2,5); pair overlaps shave a little off the product.

## (a) Pairs on the same nodes or signal
1. NullThreatVerify x NullSeeVeto — same node set (null-candidate cut nodes), same signal ("a cheaper
   enemy attack on a dearer piece"): the veto removes nodes BEFORE the null search (1699) that the verify
   would have re-searched AFTER it (1723). Together they over-defend the same tactical nodes: the bundle
   pays both scan costs and both full searches; effects ADD on disjoint sub-cases but the overlap makes
   the sum LESS than the parts (the veto steals gate cases from the verify). Counter: nodes where both
   fired = vetoed nodes whose position also passes cheaper_enemy_attacks_dearer — measured as
   nsv_vetoes under the pair vs ntv_gates lost.
2. ThreatHistory x ContHist4PlyRead — both add terms to the SAME quiet history score (1330, 1337) and
   through it to the SAME LMR clamp (2002) and history prune (1880): effects ADD in ordering and can
   over-reduce/over-trust a quiet that is strong in both tables (double-counted "this quiet is good").
3. LmrDeeperShallower x HindsightDepth — both re-depth the SAME reduced move: the parent adjusts the
   re-search depth (2017-2021) and the child adjusts its own depth again (1611-1635): a reduced move that
   beats alpha can be deepened twice on the same signal (its reduced score) — effects ADD toward
   over-extension of reduced subtrees.
4. AspCappedReopen — root only; no shared signal with the other five.
5. SoundMatePruning x (any pruning-affecting switch) — it un-prunes nodes the others then act inside;
   additive, no double count.

## (b) ONE suspect inside the six
**AspCappedReopen.** Mechanism: at 20,000 nodes (shallow) root fails are rare and each capped re-search
is cheap — the narrower window can even save nodes (its small positive at 20k). At 250,000 nodes (deep)
scores swing wider at the root, the cap walks a far-moved score back in several full-depth narrow
re-searches (the break at 2421/2429 never fires), and each step costs a deep root search — cost grows
with depth, benefit does not. The single measurement that proves me wrong: the measured tree factor at
depth 16 NOT above the factor at depth 12 (factor16 <= factor12), or the counter acr_low+acr_high per
failed search NOT growing from d12 to d16. Runner-up: NullThreatVerify (added verifications scale with
the tree, the rescued cutoffs are shallow-depth errors).

## (c) The replay mismatches, from the code
NullThreatVerify: every read is a function of (board, stack, TT, histories). Its only worker member,
null_blocked_, is saved (1731) and restored (1735) BEFORE the abort check (1738) — an aborted
verification cannot leak it. cheaper_enemy_attacks_dearer (155-175) is a pure board function.
Worker::clear (1019-1030) resets histories and the whole stack. NO code path found that depends on
anything but position, limits, TT and history state.
SoundMatePruning: the option and its arms are read node-locally (1837-1841, search.hpp:319-328);
SoundPruneTrace is off outside tests; toggling clears the searcher deterministically (uci.cpp:442-446).
NO such path found either.
What I expect in part 2: 200 of 200 equal nodes AND equal bestmove for BOTH switches in the repeat test
(carried tables, one process). On this tree the determinism holds; the old mismatch is then more likely
in the old agent's replay (a wall-clock component in its "fixed-nodes" loop, a per-game option re-set
changing clear() timing, or openings not actually identical). A repeat result below 200 of 200 for one
of these two switches would convict this tree instead — the first differing position, both node counts,
and the cause would go in the report.
