PROPOSAL A4: Amend P7 to compare the previously tested deeper/shallower re-search against the existing `LmrDeeperShallower` switch before scheduling a new implementation.

KIND: source fact

EVIDENCE: `debate/PLAN.md:234–239` groups this candidate with earlier-tree code described as absent. `source/src/search.cpp:163,2430–2441` already has a default-off arm. After a reduced search beats alpha, it adds one ply if score > best_score + 40 + 2×new_depth, subtracts one if score < best_score + new_depth, then checks whether another search is needed. `source/src/uci.cpp:820,1035–1051` exposes and applies the switch. I checked all 24 loop options. They leave it off. Equivalence to the older measured patch is unverified, so its +8.7 estimate cannot be assigned to this implementation.

COST: Allow 30 CPU-worker minutes for source comparison and switch-off position checks, zero GPU. A strength test waits behind P1 and uses P7’s existing bundle slot, with the costed games in `debate/PLAN.md:31–32,334–340`.

HOW IT IS JUDGED: Compare the old patch on the PC against the active branch conditions and depth adjustments above. If equivalent, reuse the switch in the first predeclared P7 bundle. If different, record the changed predicates and choose one variant before testing. On the final P1 settings, require switch-off equality of move, score and nodes per position on the project’s openings and game positions. For adoption, predeclare both opening seeds. Require the bundle to reach H1 for [0,+5] at 20k on each seed, the paired 4,000-game 250k lower 95% bound >0 under P12, and a 2k-soft non-regression test with lower bound >−3 before self-play. A cap without the required decision leaves it out. A bundle pass supports the bundle only.

WHAT WOULD CHANGE MY MIND: If a direct comparison shows the earlier candidate does materially different work, keep it as a separately named candidate and cost that implementation. The switch in this tree still needs to be identified correctly.
