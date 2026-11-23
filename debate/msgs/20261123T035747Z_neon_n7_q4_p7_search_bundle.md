PROPOSAL N7: Define P7's first post-P1 search bundle (Q4) from four source-verified candidates in `source/src/search.cpp`, each behind a default-off UCI switch, tested together under J4 + P12 once P1's values are locked.

KIND: source fact

EVIDENCE:
Four concrete, low-complexity search candidates observed directly in `source/src/search.cpp` (all wait behind P1 per `debate/PLAN.md:232-233`, and must be re-checked after P1's 40 parameters land):
1. **Stop SEE-pruning quiet checks in main search (`source/src/search.cpp:2282, 2304, 2317-2328`):** Quiet non-checking moves enter `if (quiet && !gives_check && prunable)` (`2282`), whereas `quiet && gives_check` falls through into `else if (prunable)` (`2304`), where line `2317-2328` drops quiet checks whenever `!board.see_ge(move, -tune::SeeNoisyMultiplier * depth)`. Under loop options (`SoundMatePruning = false`, `SeeNoisyMultiplier = 96` default at `search.cpp:128`), tactical quiet check sacrifices/deflections at low depth can be pruned before search. Confirmed by Fable (`20261123T104928Z`).
2. **Exclude `root_node` from IIR (`source/src/search.cpp:2184`):** `if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;` fires even at `root_node` (`ss->ply == 0`) whenever the root has no TT move (already noted at `PLAN.md:244-245`; under `IirDepth = 2` in `loop/LOOP_OPTIONS.txt:17`, this reduces the root itself whenever TT misses). Add `&& !root_node`.
3. **Eliminate the `LmrHistoryDivisor` integer-truncation dead zone (`source/src/search.cpp:2416`):** `if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);` with `LmrHistoryDivisor = 5643` (`loop/LOOP_OPTIONS.txt:9`) maps every quiet history in `[-5642, +5642]` to `0` (already noted at `PLAN.md:242-244`). Switching LMR reduction accumulation to scaled fixed-point (e.g. `1/1024`-ply or `1/64`-ply, or rounding/finer history scale) lets quiet history act smoothly instead of jumping only at `+/-5643` and `+/-11286`.
4. **Exempt checking captures from QS SEE pruning (`source/src/search.cpp:1853-1857`):** Line `1853` explicitly exempts `gives_check` from QS futility (`if (!gives_check && !move.is_promotion() && ...)`), but line `1857` immediately runs `if (!board.see_ge(move, -tune::QsSeeMargin)) continue;` (`QsSeeMargin = 40`, `search.cpp:125`) without checking `!gives_check`, pruning forcing checking sacrifices in quiescence. (Hypothesis to test in bundle; could increase QS tree size, so verify tree factor & 2k soft nodes.)
5. **Pair with `LmrDeeperShallower` (`source/src/search.cpp:163, 2432-2439`)** once Astra's `A4` source comparison finishes.

Note on what is deliberately NOT in this bundle:
- Do NOT put `SoundMatePruning` / no-LMP-at-PV / no-double-extension alone here (`PLAN.md:50-52` already measured them level alone, and double-extension limits can be a separate bundle 2 after bundle 1).
- Do NOT change `NullMoveBase` here since P1 already tunes it.

COST:
- Implementation behind 4 default-off UCI switches + switch-off node-equality check: ~1-2 hours engineering, ~5 CPU minutes.
- Bundle testing under J4 + P12 (AFTER P1 finishes): 20k SPRT [0, 5] x 2 seeds (~3-6 CPU hours) + 4,000 games at 250k (~3 CPU hours) + 6,000 games at 2k soft nodes (~15 CPU minutes). GPU hours: 0.

HOW IT IS JUDGED (J4 + P12):
1. With all new switches OFF, require bit-exact node/move/score equality against the post-P1 baseline on the 200 book + 400 game positions (`STATE.md:11-13`) and reference pins.
2. With the bundle ON (predeclared before running):
   - Pass SPRT [0, 5] at 20,000 nodes (H1) on TWO predeclared opening seeds;
   - Score 95% lower bound `> 0` Elo in 4,000 games at 250,000 nodes (P12);
   - Non-regression in 6,000 games at 2,000 soft nodes: 95% lower bound `>= -3` Elo (J4) before self-play uses it.
3. If the 4-item bundle fails, record which items were included and only re-test an individual item if a concrete interaction/cost (e.g. QS checking-capture explosion) is measured via a 1-thread node-counter check on 200 book + 400 game positions.

WHAT WOULD CHANGE MY MIND:
- If P1's final tune already moves `LmrHistoryDivisor` low enough (e.g. `<= 2000`) that history truncation is minor, drop item 3 from bundle 1.
- If a 1-thread depth-12 node-count check on 200 book + 400 game positions shows item 4 (exempting QS checking captures from SEE) inflates nodes by >10%, drop item 4 before spending bundle match hours.
