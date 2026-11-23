PROPOSAL N1: Reconcile P1 and P10 by adding a mandatory 2,000 soft-node self-play match and a pre-confirmation audit of dead/coupled parameters to P10's adoption bar, required before the tuned values enter the loop or the P3b rented server day.

KIND: source fact

EVIDENCE:
1. Bar mismatch between P1 and P10: `debate/PLAN.md:107-109` lists five deciding matches for P1, including `at self-play depth (2,000 soft nodes)`, `with a second net`, and `with a second seed`. `debate/PLAN.md:301-303` (P10) drops the 2,000 soft-node match, requiring only (1) 20k SPRT, (2) 250k 4,000g LB > 0, and (3) 6+0.06 2,000g >= -5. Yet `debate/PLAN.md:44-46` (J3) documents a search bundle that passed SPRT [0, 5] at 20,000 nodes (+10.6 [+4.1, +17.1]) and was dropped after losing ~-18 Elo at 2,000 soft nodes, and `debate/PLAN.md:56-59` (J6) shows tuned search shape moved strength by +79.2 +/- 7.5 Elo at 2,000 nodes. Adopting P10 without a 2,000 soft-node check risks feeding weaker self-play into both the loop and the P3b rented day (`PLAN.md:175-177`).
2. Dead/coupled parameter zones exist in `source/src/search.cpp` (confirming the unchecked risk flagged at `PLAN.md:113-115`):
   - `source/src/search.cpp:2041`: `if (tune::EvalSwingMult != 0 ...)` makes `EvalSwingMax` (`search.cpp:150,2045`) completely inert whenever `EvalSwingMult == 0`.
   - `source/src/search.cpp:2307`: `if (tune::CaptureFutilityBase > 0 ...)` makes `CaptureFutilityMultiplier` and `CaptureFutilityDepth` (`search.cpp:114-115,2308,2312`) inert whenever `CaptureFutilityBase == 0`.
   - `source/src/search.cpp:2988`: `if (tune::AspFailHighReduce != 0 ...)` makes `AspFailHighMaxReduce` (`search.cpp:156,2989`) inert whenever `AspFailHighReduce == 0`.
   - `source/src/search.cpp:2416`: `history / tune::LmrHistoryDivisor` is integer division (already noted in `PLAN.md:242-244`), so small steps in `LmrHistoryDivisor` only move quantized bucket edges (`+/-1`, `+/-2`).
   - `source/src/search.cpp:2101-2102` and `loop/LOOP_OPTIONS.txt:10`: under current `NullMoveBase = 5`, at depth 9 and `eval - beta = 450`, `R = 10` (`depth - R = -1`, going directly to qsearch); verify whether the SPSA final values push `NullMoveBase` or `NullMoveEvalDivisor` into degenerate step regions.
   (Which exact 40 parameters the live SPSA tuner varies is not in this checkout: not checked.)

COST:
- Parameter audit: ~15 CPU minutes on 1 thread (inspect the final 40-parameter list against `source/src/search.cpp` guards, verify `bench 11` / `bench 13` node-count delta of each parameter perturbed individually to detect dead parameters).
- 2,000 soft-node confirmation match: 6,000 games at 2,000 soft nodes on 16 threads takes ~10-15 CPU minutes (by scaling from `PLAN.md:27-28`: 4,000 games at 50k nodes = 872 s, and `STATE.md` / Fable readcheck reply: 2k soft nodes averages ~3,517 nodes, ~14x fewer nodes per move than 50k).
- GPU hours: 0.

HOW IT IS JUDGED:
1. Before running P10's confirmation matches, run a 1-thread sensitivity check on the final 40 tuned values against `source/src/search.cpp` (flag any parameter whose perturbation leaves `bench 13` unchanged or sits behind a zero gate; drop/revert inert settings rather than carrying noise into `LOOP_OPTIONS.txt`).
2. Add a 4th mandatory condition to P10's bar (same exe, round 67 net, equal settings per J9): 6,000 games at 2,000 soft nodes (`selfgame` node limit) must finish with point estimate >= 0 and 95% lower bound >= -3 Elo (and if adopted for self-play, also confirm on a second net or second seed per P1 before the P3b server day).
3. Keep P10's existing three bars (20k SPRT H1, 250k 4,000g LB > 0, 6+0.06 2,000g point >= -5). All four must pass before adoption.

WHAT WOULD CHANGE MY MIND:
- If the 40 tuned parameters are already verified to contain zero dead/gated entries (with raw sensitivity output) and the owner explicitly decides the tuned values will ONLY be used for match play (never for self-play or P3b), then the 2,000 soft-node bar would not be needed for self-play.
